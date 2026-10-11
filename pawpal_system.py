"""PawPal+ system logic.

Implements the design in diagrams/uml.mmd.

Classes:
    Task      -- one unit of pet care (walk, feeding, medication, vet visit)
    Pet       -- the animal receiving care, and its collection of tasks
    Owner     -- the household: contact info and the pets it is responsible for
    Scheduler -- engine that orders, filters, and manages tasks across pets
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

PRIORITIES = ("low", "medium", "high")

# Where save_to_json() and load_from_json() default to.
DATA_FILE = "data.json"

# A glyph per category, used by the CLI and the Streamlit UI so a task's kind
# is readable at a glance instead of requiring the category column to be read.
CATEGORY_ICONS: Dict[str, str] = {
    "walk": "🚶",
    "feeding": "🍖",
    "medication": "💊",
    "grooming": "🛁",
    "enrichment": "🧶",
    "vet": "🩺",
    "other": "📌",
}

# Status and priority glyphs, kept beside the category icons so every display
# surface draws from one place.
STATUS_ICONS: Dict[bool, str] = {True: "✅", False: "⬜"}
PRIORITY_ICONS: Dict[str, str] = {"high": "🔴", "medium": "🟡", "low": "🟢"}

# The window plan_day() and next_available_slot() treat as the care day.
DAY_START = "07:00"
DAY_END = "21:00"

# Higher number means more important, so sorting descending puts "high" first.
_PRIORITY_RANK: Dict[str, int] = {name: i for i, name in enumerate(PRIORITIES)}

# How many days forward each frequency repeats. "once" never repeats.
_FREQUENCY_DAYS: Dict[str, int] = {"daily": 1, "weekly": 7}


def _parse_hhmm(time_str: str) -> int:
    """Convert an "HH:MM" clock time to minutes since midnight.

    Accepts a missing leading zero ("9:00"), because sorting those as plain
    strings would place "9:00" after "17:30".
    """
    parts = time_str.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"time_str must look like 'HH:MM', got {time_str!r}")
    try:
        hours, minutes = int(parts[0]), int(parts[1])
    except ValueError:
        raise ValueError(f"time_str must be numeric, got {time_str!r}") from None
    if not 0 <= hours <= 23 or not 0 <= minutes <= 59:
        raise ValueError(f"time_str is not a real clock time: {time_str!r}")
    return hours * 60 + minutes


def format_minutes(total_minutes: int) -> str:
    """Convert minutes since midnight back to a zero-padded "HH:MM" string."""
    hours, minutes = divmod(total_minutes % (24 * 60), 60)
    return f"{hours:02d}:{minutes:02d}"


def next_occurrence(
    task: "Task", completed_on: Optional[date] = None
) -> Optional["Task"]:
    """Build the follow-up for a completed recurring task, or None.

    The next date is anchored to the task's own due_date, not to when it was
    actually finished, so a weekly Monday task completed late on Thursday stays
    a Monday task. Anchoring to the completion date instead would let a task
    drift forward through the calendar every time the owner ran late.

    A task finished long after it was due would otherwise spawn an occurrence
    that is itself already overdue, so the date advances in whole steps until it
    lands in the future.

    `completed_on` defaults to today and exists so callers can pin the clock,
    which keeps the CLI demo's output identical on every run.

    Lives at module level because both Scheduler.handle_recurring() and
    Pet.complete_task() need it, and Pet must not depend on Scheduler.
    """
    if not task.is_completed or not task.repeats():
        return None

    today = completed_on or date.today()
    step = timedelta(days=_FREQUENCY_DAYS[task.frequency])
    base = task.due_date or today
    next_date = base + step
    while next_date <= today:
        next_date += step

    return replace(
        task,
        id=Task.new_id(task.pet_id, task.title, next_date.isoformat()),
        due_date=next_date,
        is_completed=False,
    )


@dataclass
class Task:
    """A single unit of pet care.

    Every kind of care activity is one Task with different field values, so a
    walk, a feeding, a dose of medication, and a vet visit share one type.
    """

    id: str
    pet_id: str
    title: str
    category: str
    time_str: str
    duration_minutes: int
    priority: str = "medium"
    frequency: str = "once"
    description: str = ""
    due_date: Optional[date] = None
    assigned_to: Optional[str] = None
    is_completed: bool = False

    def __post_init__(self) -> None:
        """Reject values that would silently corrupt a schedule later."""
        if self.priority not in _PRIORITY_RANK:
            raise ValueError(
                f"priority must be one of {PRIORITIES}, got {self.priority!r}"
            )
        if self.duration_minutes <= 0:
            raise ValueError(
                f"duration_minutes must be positive, got {self.duration_minutes!r}"
            )
        # Normalize the clock time so every stored value is zero-padded, and
        # fail fast on garbage rather than at sort time.
        self.time_str = format_minutes(_parse_hhmm(self.time_str))

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.is_completed = True

    def mark_pending(self) -> None:
        """Reset this task back to not-done."""
        self.is_completed = False

    def start_minutes(self) -> int:
        """Return time_str as minutes since midnight, for sorting and overlap math."""
        return _parse_hhmm(self.time_str)

    def end_minutes(self) -> int:
        """Return the minute this task finishes."""
        return self.start_minutes() + self.duration_minutes

    def priority_rank(self) -> int:
        """Return a sortable rank where a higher number is more important."""
        return _PRIORITY_RANK[self.priority]

    def repeats(self) -> bool:
        """Return True when this task is set to recur."""
        return self.frequency in _FREQUENCY_DAYS

    def overlaps(self, other: Task) -> bool:
        """Return True when this task's time range intersects `other`'s.

        Two ranges collide when each starts before the other ends. Tasks that
        merely touch end-to-start (08:00-08:30 and 08:30-09:00) do not collide.
        """
        return (
            self.start_minutes() < other.end_minutes()
            and other.start_minutes() < self.end_minutes()
        )

    @staticmethod
    def new_id(pet_id: str, title: str, when: str) -> str:
        """Build a readable, unique task id, used when spawning an occurrence."""
        slug = "-".join(title.lower().split())
        return f"{pet_id}-{slug}-{when}"

    def icon(self) -> str:
        """Return the glyph for this task's category."""
        return CATEGORY_ICONS.get(self.category, CATEGORY_ICONS["other"])

    def status_icon(self) -> str:
        """Return a glyph showing whether this task is done."""
        return STATUS_ICONS[self.is_completed]

    def priority_icon(self) -> str:
        """Return a glyph showing how important this task is."""
        return PRIORITY_ICONS[self.priority]

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe dict of this task, with the date as a string."""
        data = asdict(self)
        data["due_date"] = self.due_date.isoformat() if self.due_date else None
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Rebuild a Task from to_dict() output, parsing the date back."""
        fields = dict(data)
        raw_date = fields.get("due_date")
        fields["due_date"] = date.fromisoformat(raw_date) if raw_date else None
        return cls(**fields)

    def describe(self) -> str:
        """Return a one-line summary of this task for CLI output."""
        window = f"{self.time_str}-{format_minutes(self.end_minutes())}"
        line = f"{window} {self.title} ({self.duration_minutes} min) [{self.priority}]"
        if self.assigned_to:
            line += f" -- {self.assigned_to}"
        if self.is_completed:
            line += " [done]"
        return line


@dataclass
class Pet:
    """The animal receiving care, and the owner of its own task list."""

    id: str
    name: str
    species: str
    breed: str = ""
    age: int = 0
    dietary_notes: str = ""
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and stamp it with this pet's id."""
        if any(existing.id == task.id for existing in self.tasks):
            raise ValueError(f"{self.name} already has a task with id {task.id!r}")
        task.pet_id = self.id
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> bool:
        """Remove the task with this id. Return True if something was removed."""
        for index, task in enumerate(self.tasks):
            if task.id == task_id:
                del self.tasks[index]
                return True
        return False

    def get_pending_tasks(self) -> List[Task]:
        """Return this pet's tasks that are not yet completed."""
        return [task for task in self.tasks if not task.is_completed]

    def find_task(self, task_id: str) -> Optional[Task]:
        """Look up one of this pet's tasks by id."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def complete_task(
        self, task_id: str, completed_on: Optional[date] = None
    ) -> Optional[Task]:
        """Mark a task complete and, if it recurs, schedule its next occurrence.

        Returns the newly created follow-up task, or None when the task does
        not repeat. This is the automatic path: callers that want to complete a
        task without spawning anything call Task.mark_complete() directly.
        `completed_on` defaults to today.
        """
        task = self.find_task(task_id)
        if task is None:
            return None
        task.mark_complete()
        follow_up = next_occurrence(task, completed_on)
        if follow_up is not None:
            self.add_task(follow_up)
        return follow_up

    def label(self) -> str:
        """Return a display name, including breed when one is known."""
        return f"{self.name} ({self.breed})" if self.breed else self.name

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe dict of this pet and its tasks."""
        return {
            "id": self.id,
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "age": self.age,
            "dietary_notes": self.dietary_notes,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pet":
        """Rebuild a Pet and its tasks from to_dict() output."""
        fields = dict(data)
        tasks = [Task.from_dict(raw) for raw in fields.pop("tasks", [])]
        return cls(tasks=tasks, **fields)


@dataclass
class Owner:
    """The household: contact info and the pets it is responsible for."""

    name: str
    email: str = ""
    phone: str = ""
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        if any(existing.id == pet.id for existing in self.pets):
            raise ValueError(f"a pet with id {pet.id!r} is already registered")
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return every task across every pet, flattened for the scheduler."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> List[Task]:
        """Return the not-yet-completed tasks across every pet."""
        return [task for task in self.get_all_tasks() if not task.is_completed]

    def find_pet(self, name: str) -> Optional[Pet]:
        """Look up a pet by name, case-insensitively. First match wins."""
        target = name.strip().lower()
        for pet in self.pets:
            if pet.name.lower() == target:
                return pet
        return None

    def find_pet_by_id(self, pet_id: str) -> Optional[Pet]:
        """Look up a pet by id, used to resolve Task.pet_id back to its Pet."""
        for pet in self.pets:
            if pet.id == pet_id:
                return pet
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe dict of the whole household."""
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "pets": [pet.to_dict() for pet in self.pets],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Owner":
        """Rebuild an Owner, its pets, and their tasks from to_dict() output."""
        fields = dict(data)
        pets = [Pet.from_dict(raw) for raw in fields.pop("pets", [])]
        return cls(pets=pets, **fields)

    def save_to_json(self, path: str = DATA_FILE) -> str:
        """Write the household to a JSON file and return the path written.

        Dates are stored as ISO strings and rebuilt on load, because json has
        no date type of its own.
        """
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2)
        return path

    @classmethod
    def load_from_json(cls, path: str = DATA_FILE) -> Optional["Owner"]:
        """Read a household back from a JSON file.

        Returns None when the file does not exist, so a first run starts empty
        instead of crashing. A file that exists but is corrupt raises, because
        silently discarding someone's saved pets would be worse.
        """
        try:
            with open(path, encoding="utf-8") as handle:
                return cls.from_dict(json.load(handle))
        except FileNotFoundError:
            return None

    def complete_task(
        self, task_id: str, completed_on: Optional[date] = None
    ) -> Optional[Task]:
        """Complete a task belonging to any pet, spawning a follow-up if it recurs."""
        for pet in self.pets:
            if pet.find_task(task_id) is not None:
                return pet.complete_task(task_id, completed_on)
        return None


@dataclass
class Scheduler:
    """Planning engine. Holds a reference to the household but stores no tasks."""

    owner: Optional[Owner] = None

    def _require_owner(self) -> Owner:
        """Return the attached owner, or explain why there is nothing to plan."""
        if self.owner is None:
            raise ValueError("Scheduler has no owner attached; nothing to plan")
        return self.owner

    def pet_name_for(self, task: Task) -> str:
        """Resolve a task's pet_id to a display name, falling back to the raw id."""
        if self.owner is not None:
            pet = self.owner.find_pet_by_id(task.pet_id)
            if pet is not None:
                return pet.name
        return task.pet_id

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Return the tasks ordered chronologically.

        Ties break on priority (most important first) then title, so the same
        input always produces the same order.
        """
        return sorted(
            tasks,
            key=lambda task: (task.start_minutes(), -task.priority_rank(), task.title),
        )

    def sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Return the tasks most important first, then chronologically.

        The mirror image of sort_by_time(): where that answers "what happens
        next", this answers "what matters most". Ties inside a priority band
        fall back to clock order, then title, so the result is reproducible.
        """
        return sorted(
            tasks,
            key=lambda task: (-task.priority_rank(), task.start_minutes(), task.title),
        )

    def filter_by_status(self, tasks: List[Task], completed: bool) -> List[Task]:
        """Return only the tasks whose is_completed matches `completed`."""
        return [task for task in tasks if task.is_completed == completed]

    def filter_by_pet(self, tasks: List[Task], pet_name: str) -> List[Task]:
        """Return only the tasks belonging to the named pet.

        Matches on the pet's id when the name resolves through the owner, and
        falls back to comparing pet_id directly so the method still works on a
        hand-built list with no owner attached.
        """
        target = pet_name.strip().lower()
        pet = self.owner.find_pet(pet_name) if self.owner is not None else None
        pet_id = pet.id if pet is not None else target
        return [task for task in tasks if task.pet_id.lower() == pet_id.lower()]

    def detect_conflicts(self, tasks: List[Task]) -> List[Tuple[Task, Task]]:
        """Return each pair of tasks whose time ranges overlap.

        Works across pets, so a 08:00 walk for one pet and a 08:15 dose for
        another are reported: the owner cannot be in two places at once.
        """
        ordered = self.sort_by_time(tasks)
        conflicts: List[Tuple[Task, Task]] = []
        for index, task in enumerate(ordered):
            # Sorted by start time, so stop once a later task starts after this
            # one ends -- everything beyond it starts later still.
            for other in ordered[index + 1 :]:
                if other.start_minutes() >= task.end_minutes():
                    break
                if task.overlaps(other):
                    conflicts.append((task, other))
        return conflicts

    def conflict_warnings(self, tasks: List[Task]) -> List[str]:
        """Return a readable warning per overlapping pair, never raising.

        A conflict is something for the owner to resolve, not an error, so this
        reports and returns rather than interrupting the program.
        """
        warnings = []
        for first, second in self.detect_conflicts(tasks):
            same_pet = first.pet_id == second.pet_id
            who = (
                f"{self.pet_name_for(first)} has two tasks booked at once"
                if same_pet
                else f"{self.pet_name_for(first)} and {self.pet_name_for(second)} "
                "both need attention at once"
            )
            warnings.append(
                f"WARNING: {who} -- {first.title} runs "
                f"{first.time_str}-{format_minutes(first.end_minutes())} but "
                f"{second.title} starts {second.time_str}"
            )
        return warnings

    def next_available_slot(
        self,
        duration_minutes: int,
        tasks: Optional[List[Task]] = None,
        day_start: str = DAY_START,
        day_end: str = DAY_END,
    ) -> Optional[str]:
        """Return the earliest "HH:MM" where a task of this length fits.

        Sweeps the day once in clock order, carrying a cursor through the
        booked time: whenever the gap between the cursor and the next task is
        wide enough, that gap is the answer. Returns None when nothing in the
        window is long enough.

        Defaults to every task across the household, so the slot it offers does
        not collide with another pet's care.
        """
        if duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

        if tasks is None:
            tasks = self.owner.get_all_tasks() if self.owner is not None else []

        window_start = _parse_hhmm(day_start)
        window_end = _parse_hhmm(day_end)
        cursor = window_start

        for task in self.sort_by_time(tasks):
            # Tasks already finished do not block the calendar.
            if task.is_completed:
                continue
            start, end = task.start_minutes(), task.end_minutes()
            if end <= cursor or start >= window_end:
                continue
            if start - cursor >= duration_minutes:
                return format_minutes(cursor)
            cursor = max(cursor, end)

        if window_end - cursor >= duration_minutes:
            return format_minutes(cursor)
        return None

    def handle_recurring(
        self, task: Task, completed_on: Optional[date] = None
    ) -> Optional[Task]:
        """Build the next occurrence of a completed recurring task.

        Returns a new Task without attaching it, so a list being iterated is
        never mutated mid-loop. Returns None when the task does not repeat or is
        not yet complete. For the automatic path that also attaches the result,
        use Pet.complete_task() or Owner.complete_task().
        """
        return next_occurrence(task, completed_on)

    def plan_day(self, minutes_available: Optional[int] = None) -> List[Task]:
        """Build today's plan across every pet in self.owner.

        Pulls pending tasks from the owner and orders them chronologically. When
        `minutes_available` is given, the most important tasks are kept first and
        anything that no longer fits the budget is dropped; the kept tasks are
        then returned in clock order.
        """
        owner = self._require_owner()
        pending = owner.get_all_pending_tasks()
        if minutes_available is None:
            return self.sort_by_time(pending)

        # Spend the budget on the most important tasks, earliest first within a
        # priority band, so a dropped task is always the least important one.
        by_importance = sorted(
            pending,
            key=lambda task: (-task.priority_rank(), task.start_minutes(), task.title),
        )
        selected: List[Task] = []
        remaining = minutes_available
        for task in by_importance:
            if task.duration_minutes <= remaining:
                selected.append(task)
                remaining -= task.duration_minutes
        return self.sort_by_time(selected)

    def explain_plan(self, plan: List[Task]) -> List[str]:
        """Return one line per task explaining why it is scheduled when it is."""
        conflicting = {id(task) for pair in self.detect_conflicts(plan) for task in pair}
        lines: List[str] = []
        for task in plan:
            reason = (
                f"{task.priority} priority {task.category} for "
                f"{self.pet_name_for(task)}"
            )
            if id(task) in conflicting:
                reason += "; overlaps another task, so one needs moving"
            lines.append(f"{task.describe()} -- {reason}")
        return lines

    def dropped_from_plan(self, plan: List[Task]) -> List[Task]:
        """Return the pending tasks that did not make it into `plan`."""
        owner = self._require_owner()
        kept = {id(task) for task in plan}
        return [
            task for task in owner.get_all_pending_tasks() if id(task) not in kept
        ]
