"""PawPal+ CLI demo.

Builds a small household and walks through every scheduler feature in the
terminal, so the backend logic can be verified without the Streamlit UI.

Run with:
    python main.py
"""

from datetime import date
from typing import List, Tuple

from pawpal_system import Owner, Pet, Scheduler, Task, format_minutes

# A fixed date keeps the recurring-task output identical on every run.
TODAY = date(2026, 10, 10)

# Minutes of hands-on care time the owner has today, used to show the
# scheduler dropping work that no longer fits.
TIME_BUDGET = 30


def rule(title: str) -> None:
    """Print a titled section divider."""
    print()
    print(title)
    print("-" * len(title))


def build_household() -> Tuple[Owner, Scheduler]:
    """Create one owner, two pets, and six tasks spread across the day."""
    owner = Owner(name="Jordan Vega", email="jordan@example.com", phone="555-0134")

    milo = Pet(
        id="milo",
        name="Milo",
        species="dog",
        breed="Beagle",
        age=4,
        dietary_notes="grain-free kibble only",
    )
    luna = Pet(
        id="luna",
        name="Luna",
        species="cat",
        breed="Tabby",
        age=2,
        dietary_notes="allergic to chicken",
    )
    owner.add_pet(milo)
    owner.add_pet(luna)

    # Deliberately out of chronological order: the evening task is added first,
    # so "Today's Schedule" proves sort_by_time() is doing the ordering rather
    # than the insertion order happening to be right.
    milo_tasks = [
        Task(
            id="milo-groom",
            pet_id="milo",
            title="Brush Coat",
            category="grooming",
            time_str="19:00",
            duration_minutes=20,
            priority="low",
            frequency="weekly",
            due_date=TODAY,
        ),
        Task(
            id="milo-walk-am",
            pet_id="milo",
            title="Park Walk",
            category="walk",
            time_str="08:00",
            duration_minutes=45,
            priority="high",
            frequency="daily",
            due_date=TODAY,
            assigned_to="Jordan",
        ),
        Task(
            id="milo-feed-pm",
            pet_id="milo",
            title="Evening Kibble",
            category="feeding",
            time_str="17:30",
            duration_minutes=10,
            priority="high",
            frequency="daily",
            due_date=TODAY,
            description="grain-free only",
        ),
    ]
    luna_tasks = [
        Task(
            id="luna-feed-am",
            pet_id="luna",
            title="Morning Kibble",
            category="feeding",
            time_str="08:15",
            duration_minutes=10,
            priority="high",
            frequency="daily",
            due_date=TODAY,
            description="no chicken",
        ),
        Task(
            id="luna-meds",
            pet_id="luna",
            title="Ear Drops",
            category="medication",
            time_str="09:00",
            duration_minutes=5,
            priority="medium",
            frequency="daily",
            due_date=TODAY,
            assigned_to="Alex",
        ),
        Task(
            id="luna-play",
            pet_id="luna",
            title="Wand Play",
            category="enrichment",
            time_str="18:00",
            duration_minutes=15,
            priority="medium",
            due_date=TODAY,
        ),
        # Exactly the same start time as Milo's Evening Kibble, to show the
        # scheduler catching an identical-timestamp clash as well as an overlap.
        Task(
            id="luna-feed-pm",
            pet_id="luna",
            title="Evening Pouch",
            category="feeding",
            time_str="17:30",
            duration_minutes=10,
            priority="high",
            frequency="daily",
            due_date=TODAY,
            description="no chicken",
        ),
    ]
    for task in milo_tasks:
        milo.add_task(task)
    for task in luna_tasks:
        luna.add_task(task)

    return owner, Scheduler(owner=owner)


def print_household(owner: Owner) -> None:
    """Print who is in the household and what each pet needs to know about."""
    rule(f"PawPal+ -- {owner.name} ({owner.email})")
    for pet in owner.pets:
        print(f"  {pet.label()}, {pet.species}, age {pet.age}")
        print(f"    diet: {pet.dietary_notes}")
        print(f"    tasks on file: {len(pet.tasks)}")


def print_schedule(scheduler: Scheduler, tasks: List[Task], title: str) -> None:
    """Print tasks in clock order as an aligned table."""
    rule(title)
    if not tasks:
        print("  (nothing scheduled)")
        return

    ordered = scheduler.sort_by_time(tasks)
    pet_width = max(len(scheduler.pet_name_for(task)) for task in ordered)
    for task in ordered:
        window = f"{task.time_str}-{format_minutes(task.end_minutes())}"
        pet = scheduler.pet_name_for(task).ljust(pet_width)
        status = "done" if task.is_completed else "todo"
        who = f" (with {task.assigned_to})" if task.assigned_to else ""
        print(
            f"  {window}  {pet}  {task.title:<15} "
            f"{task.duration_minutes:>3} min  {task.priority:<6} {status}{who}"
        )


def print_insertion_order(scheduler: Scheduler, tasks: List[Task]) -> None:
    """Print tasks as they were entered, before any sorting."""
    rule("As entered (unsorted)")
    for task in tasks:
        print(f"  {task.time_str}  {scheduler.pet_name_for(task)}: {task.title}")


def print_per_pet(scheduler: Scheduler, owner: Owner) -> None:
    """Print each pet's own tasks, filtered by name out of the combined list."""
    rule("Filtered by pet")
    all_tasks = owner.get_all_tasks()
    for pet in owner.pets:
        mine = scheduler.sort_by_time(scheduler.filter_by_pet(all_tasks, pet.name))
        print(f"  {pet.name} ({len(mine)} tasks)")
        for task in mine:
            print(f"    {task.time_str}  {task.title}")


def print_conflicts(scheduler: Scheduler, tasks: List[Task]) -> None:
    """Report tasks whose time ranges overlap, across all pets."""
    rule("Scheduling conflicts")
    warnings = scheduler.conflict_warnings(tasks)
    if not warnings:
        print("  none -- no two tasks overlap")
        return
    for warning in warnings:
        print(f"  {warning}")
    print("  reported as warnings, so the program keeps running")


def print_status_split(scheduler: Scheduler, tasks: List[Task]) -> None:
    """Split tasks into done and outstanding."""
    rule("Progress so far")
    done = scheduler.filter_by_status(tasks, completed=True)
    todo = scheduler.filter_by_status(tasks, completed=False)
    print(f"  completed ({len(done)}): " + ", ".join(t.title for t in done))
    print(f"  remaining ({len(todo)}): " + ", ".join(t.title for t in todo))


def print_budgeted_plan(scheduler: Scheduler, minutes: int) -> None:
    """Fit the remaining work into a time budget and explain the result."""
    rule(f"Plan for a {minutes}-minute budget")
    plan = scheduler.plan_day(minutes_available=minutes)
    used = sum(task.duration_minutes for task in plan)
    for line in scheduler.explain_plan(plan):
        print(f"  {line}")
    print(f"  uses {used} of {minutes} minutes")

    dropped = scheduler.dropped_from_plan(plan)
    if dropped:
        print("  dropped, lowest priority first:")
        for task in dropped:
            print(
                f"    {task.title} ({task.duration_minutes} min, "
                f"{task.priority} priority)"
            )


def print_recurrence(owner: Owner, task_id: str) -> None:
    """Complete a recurring task and show its follow-up appearing by itself."""
    rule("Recurring tasks")
    pet = owner.find_pet_by_id("milo")
    before = len(pet.tasks)
    spawned = owner.complete_task(task_id)
    if spawned is None:
        print(f"  {task_id} does not repeat, so completing it created nothing")
        return
    print(f"  completed {task_id}, which is a {spawned.frequency} task")
    print(f"  follow-up created automatically: {spawned.id}")
    print(f"  due {spawned.due_date} at {spawned.time_str}, not completed")
    print(f"  {pet.name}'s task count went {before} -> {len(pet.tasks)}")


def main() -> None:
    """Run the full demo."""
    owner, scheduler = build_household()

    print_household(owner)
    print_insertion_order(scheduler, owner.get_all_tasks())
    print_schedule(scheduler, owner.get_all_tasks(), "Today's Schedule")
    print_per_pet(scheduler, owner)
    print_conflicts(scheduler, owner.get_all_tasks())

    # Work through the morning so the later sections have something to report.
    owner.find_pet("Milo").find_task("milo-walk-am").mark_complete()
    owner.find_pet("Luna").find_task("luna-feed-am").mark_complete()

    print_status_split(scheduler, owner.get_all_tasks())
    print_budgeted_plan(scheduler, TIME_BUDGET)
    print_recurrence(owner, "milo-feed-pm")
    print()


if __name__ == "__main__":
    main()
