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

    milo_tasks = [
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


def print_conflicts(scheduler: Scheduler, tasks: List[Task]) -> None:
    """Report tasks whose time ranges overlap, across all pets."""
    rule("Scheduling conflicts")
    conflicts = scheduler.detect_conflicts(tasks)
    if not conflicts:
        print("  none -- no two tasks overlap")
        return
    for first, second in conflicts:
        print(
            f"  {first.time_str} {scheduler.pet_name_for(first)}'s {first.title} "
            f"runs until {format_minutes(first.end_minutes())}, but "
            f"{scheduler.pet_name_for(second)}'s {second.title} starts "
            f"{second.time_str}"
        )
    print("  the owner cannot be in two places at once, so one needs moving")


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


def print_recurrence(scheduler: Scheduler, task: Task) -> None:
    """Show a completed recurring task spawning its next occurrence."""
    rule("Recurring tasks")
    spawned = scheduler.handle_recurring(task)
    if spawned is None:
        print(f"  {task.title} does not repeat, or is not finished yet")
        return
    print(f"  {task.title} is {task.frequency} and was completed on {task.due_date}")
    print(f"  next occurrence: {spawned.id} due {spawned.due_date} at {spawned.time_str}")


def main() -> None:
    """Run the full demo."""
    owner, scheduler = build_household()

    print_household(owner)
    print_schedule(scheduler, owner.get_all_tasks(), "Today's Schedule")
    print_conflicts(scheduler, owner.get_all_tasks())

    # Work through the morning so the later sections have something to report.
    owner.find_pet("Milo").tasks[0].mark_complete()
    owner.find_pet("Luna").tasks[0].mark_complete()

    print_status_split(scheduler, owner.get_all_tasks())
    print_budgeted_plan(scheduler, TIME_BUDGET)
    print_recurrence(scheduler, owner.find_pet("Milo").tasks[0])
    print()


if __name__ == "__main__":
    main()
