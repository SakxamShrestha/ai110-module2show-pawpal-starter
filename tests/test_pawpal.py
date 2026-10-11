"""Tests for the PawPal+ system logic."""

from datetime import date

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


def make_task(
    task_id="t1",
    time_str="08:00",
    duration_minutes=30,
    priority="high",
    title="Park Walk",
    pet_id="milo",
    frequency="once",
    due_date=None,
):
    """Build a throwaway task for a test to act on."""
    return Task(
        id=task_id,
        pet_id=pet_id,
        title=title,
        category="walk",
        time_str=time_str,
        duration_minutes=duration_minutes,
        priority=priority,
        frequency=frequency,
        due_date=due_date,
    )


@pytest.fixture
def household():
    """An owner with two pets and no tasks yet."""
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(id="milo", name="Milo", species="dog"))
    owner.add_pet(Pet(id="luna", name="Luna", species="cat"))
    return owner


@pytest.fixture
def scheduler(household):
    """A scheduler wired to the household fixture."""
    return Scheduler(owner=household)


# ---------------------------------------------------------------------------
# Task state
# ---------------------------------------------------------------------------


def test_mark_complete_changes_status():
    """mark_complete() flips is_completed, and mark_pending() puts it back."""
    task = make_task()
    assert task.is_completed is False

    task.mark_complete()
    assert task.is_completed is True

    task.mark_pending()
    assert task.is_completed is False


def test_add_task_increases_pet_task_count():
    """add_task() grows the pet's task list and stamps the task with the pet's id."""
    pet = Pet(id="milo", name="Milo", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(make_task("t1", "08:00"))
    assert len(pet.tasks) == 1

    pet.add_task(make_task("t2", "17:30"))
    assert len(pet.tasks) == 2

    assert pet.tasks[0].pet_id == "milo"


def test_remove_task_reports_whether_it_removed_anything():
    """remove_task() returns True for a real id and False for one that is absent."""
    pet = Pet(id="milo", name="Milo", species="dog")
    pet.add_task(make_task("t1"))

    assert pet.remove_task("nope") is False
    assert len(pet.tasks) == 1
    assert pet.remove_task("t1") is True
    assert pet.tasks == []


@pytest.mark.parametrize(
    "bad_field",
    [
        {"priority": "urgent"},
        {"duration_minutes": 0},
        {"time_str": "25:00"},
        {"time_str": "noon"},
    ],
)
def test_task_rejects_invalid_values(bad_field):
    """Values that would corrupt a schedule are refused at construction."""
    with pytest.raises(ValueError):
        make_task(**bad_field)


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------


def test_sort_by_time_orders_chronologically_not_alphabetically(scheduler):
    """A missing leading zero must not sort "9:00" after "17:30"."""
    tasks = [
        make_task("evening", "17:30"),
        make_task("morning", "9:00"),
        make_task("night", "19:00"),
    ]
    assert [task.id for task in scheduler.sort_by_time(tasks)] == [
        "morning",
        "evening",
        "night",
    ]


def test_sort_by_time_breaks_ties_by_priority(scheduler):
    """Two tasks at the same time order the more important one first."""
    tasks = [
        make_task("low-one", "08:00", priority="low", title="Brush"),
        make_task("high-one", "08:00", priority="high", title="Meds"),
    ]
    ordered = scheduler.sort_by_time(tasks)
    assert [task.id for task in ordered] == ["high-one", "low-one"]
    # Same input, same output: the plan has to be reproducible.
    assert scheduler.sort_by_time(ordered) == ordered


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def test_filter_by_status_splits_done_from_outstanding(scheduler):
    """filter_by_status() returns exactly the tasks matching the flag asked for."""
    done = make_task("done", "08:00")
    done.mark_complete()
    todo = make_task("todo", "09:00")

    assert scheduler.filter_by_status([done, todo], completed=True) == [done]
    assert scheduler.filter_by_status([done, todo], completed=False) == [todo]


def test_filter_by_pet_returns_only_that_pets_tasks(scheduler, household):
    """filter_by_pet() resolves a pet name and keeps only that pet's tasks."""
    household.find_pet("Milo").add_task(make_task("milo-walk", "08:00"))
    household.find_pet("Luna").add_task(make_task("luna-feed", "08:15", pet_id="luna"))
    household.find_pet("Luna").add_task(make_task("luna-meds", "09:00", pet_id="luna"))

    all_tasks = household.get_all_tasks()
    assert len(all_tasks) == 3

    luna_ids = [task.id for task in scheduler.filter_by_pet(all_tasks, "Luna")]
    assert luna_ids == ["luna-feed", "luna-meds"]
    # Name matching ignores case, so UI input does not have to be exact.
    assert scheduler.filter_by_pet(all_tasks, "milo") == [all_tasks[0]]


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------


def test_detect_conflicts_flags_overlap_across_pets(scheduler):
    """An 08:00 walk running 45 minutes collides with an 08:15 feeding."""
    walk = make_task("walk", "08:00", duration_minutes=45)
    feed = make_task("feed", "08:15", duration_minutes=10, pet_id="luna")

    conflicts = scheduler.detect_conflicts([walk, feed])
    assert len(conflicts) == 1
    assert {task.id for task in conflicts[0]} == {"walk", "feed"}


def test_detect_conflicts_flags_identical_start_times(scheduler):
    """Two tasks booked at the same minute are a conflict."""
    first = make_task("milo-feed", "17:30", duration_minutes=10)
    second = make_task("luna-feed", "17:30", duration_minutes=10, pet_id="luna")

    assert len(scheduler.detect_conflicts([first, second])) == 1


def test_detect_conflicts_ignores_tasks_that_only_touch(scheduler):
    """08:00-08:30 followed by 08:30-09:00 is back-to-back, not a clash."""
    first = make_task("first", "08:00", duration_minutes=30)
    second = make_task("second", "08:30", duration_minutes=30)

    assert scheduler.detect_conflicts([first, second]) == []


def test_conflict_warnings_reports_strings_without_raising(scheduler):
    """A clash is the owner's to resolve, so it comes back as text, not an error."""
    walk = make_task("walk", "08:00", duration_minutes=45)
    feed = make_task("feed", "08:15", duration_minutes=10)

    warnings = scheduler.conflict_warnings([walk, feed])
    assert len(warnings) == 1
    assert warnings[0].startswith("WARNING:")
    assert "Park Walk" in warnings[0]
    assert scheduler.conflict_warnings([walk]) == []


# ---------------------------------------------------------------------------
# Recurrence
# ---------------------------------------------------------------------------


def test_complete_task_spawns_next_daily_occurrence(household):
    """Completing a daily task attaches tomorrow's occurrence automatically."""
    milo = household.find_pet("Milo")
    milo.add_task(
        make_task("walk", "08:00", frequency="daily", due_date=date(2026, 10, 10))
    )

    follow_up = milo.complete_task("walk")

    assert follow_up is not None
    assert follow_up.due_date == date(2026, 10, 11)
    assert follow_up.is_completed is False
    assert follow_up.id != "walk"
    assert len(milo.tasks) == 2
    assert milo.get_pending_tasks() == [follow_up]


def test_complete_task_advances_a_weekly_task_by_seven_days(household):
    """A weekly frequency moves the due date a week, not a day."""
    milo = household.find_pet("Milo")
    milo.add_task(
        make_task("groom", "19:00", frequency="weekly", due_date=date(2026, 10, 10))
    )

    follow_up = milo.complete_task("groom")
    assert follow_up.due_date == date(2026, 10, 17)


def test_complete_task_creates_nothing_for_a_one_off(household):
    """A task set to "once" is completed and nothing is spawned."""
    milo = household.find_pet("Milo")
    milo.add_task(make_task("vet", "11:00", frequency="once"))

    assert milo.complete_task("vet") is None
    assert len(milo.tasks) == 1
    assert milo.tasks[0].is_completed is True


def test_handle_recurring_returns_without_attaching(scheduler, household):
    """The manual form hands back the new task so a loop can append it safely."""
    milo = household.find_pet("Milo")
    task = make_task("walk", "08:00", frequency="daily", due_date=date(2026, 10, 10))
    milo.add_task(task)

    assert scheduler.handle_recurring(task) is None  # not completed yet

    task.mark_complete()
    spawned = scheduler.handle_recurring(task)
    assert spawned is not None
    assert len(milo.tasks) == 1  # nothing was attached


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------


def test_plan_day_drops_the_lowest_priority_task_over_budget(household, scheduler):
    """Priority decides what is cut, not position in the day."""
    milo = household.find_pet("Milo")
    milo.add_task(make_task("meds", "08:00", duration_minutes=10, priority="high"))
    milo.add_task(make_task("play", "12:00", duration_minutes=15, priority="medium"))
    milo.add_task(make_task("brush", "19:00", duration_minutes=20, priority="low"))

    plan = scheduler.plan_day(minutes_available=30)

    assert [task.id for task in plan] == ["meds", "play"]
    assert sum(task.duration_minutes for task in plan) == 25
    assert [task.id for task in scheduler.dropped_from_plan(plan)] == ["brush"]


def test_plan_day_without_a_budget_returns_everything_outstanding(household, scheduler):
    """With no budget the plan is every pending task, in clock order."""
    milo = household.find_pet("Milo")
    milo.add_task(make_task("late", "19:00"))
    milo.add_task(make_task("early", "08:00"))
    done = make_task("done", "12:00")
    done.mark_complete()
    milo.add_task(done)

    assert [task.id for task in scheduler.plan_day()] == ["early", "late"]


def test_plan_day_without_an_owner_explains_itself():
    """A scheduler with nothing attached says so instead of failing obscurely."""
    with pytest.raises(ValueError, match="no owner attached"):
        Scheduler().plan_day()


# ---------------------------------------------------------------------------
# Priority-first ordering
# ---------------------------------------------------------------------------


def test_sort_by_priority_puts_important_tasks_first(scheduler):
    """sort_by_priority() leads with high priority even when it is late in the day."""
    tasks = [
        make_task("brush", "08:00", priority="low", title="Brush"),
        make_task("meds", "19:00", priority="high", title="Meds"),
        make_task("play", "12:00", priority="medium", title="Play"),
    ]
    assert [task.id for task in scheduler.sort_by_priority(tasks)] == [
        "meds",
        "play",
        "brush",
    ]


def test_sort_by_priority_falls_back_to_clock_order(scheduler):
    """Inside one priority band, the earlier task comes first."""
    tasks = [
        make_task("late", "17:00", priority="high", title="Late"),
        make_task("early", "08:00", priority="high", title="Early"),
    ]
    assert [task.id for task in scheduler.sort_by_priority(tasks)] == ["early", "late"]


# ---------------------------------------------------------------------------
# Next available slot
# ---------------------------------------------------------------------------


def test_next_available_slot_finds_the_gap_between_tasks(scheduler):
    """A 30-minute request lands in the gap after an 07:00-07:30 task."""
    tasks = [
        make_task("first", "07:00", duration_minutes=30),
        make_task("second", "08:00", duration_minutes=45),
    ]
    assert scheduler.next_available_slot(30, tasks) == "07:30"


def test_next_available_slot_skips_a_gap_that_is_too_short(scheduler):
    """A 45-minute request cannot use the 30-minute gap, so it lands after."""
    tasks = [
        make_task("first", "07:00", duration_minutes=30),
        make_task("second", "08:00", duration_minutes=45),
    ]
    assert scheduler.next_available_slot(45, tasks) == "08:45"


def test_next_available_slot_returns_none_when_the_day_is_full(scheduler):
    """With the whole care day booked there is no slot to offer."""
    tasks = [make_task("all-day", "07:00", duration_minutes=14 * 60)]
    assert scheduler.next_available_slot(30, tasks) is None


def test_next_available_slot_ignores_completed_tasks(scheduler):
    """A finished task no longer blocks the calendar."""
    done = make_task("done", "07:00", duration_minutes=120)
    done.mark_complete()
    assert scheduler.next_available_slot(60, [done]) == "07:00"


def test_next_available_slot_rejects_a_zero_length_request(scheduler):
    """Asking where a zero-minute task fits is a programming error."""
    with pytest.raises(ValueError, match="must be positive"):
        scheduler.next_available_slot(0, [])


# ---------------------------------------------------------------------------
# JSON persistence
# ---------------------------------------------------------------------------


def test_save_and_load_round_trips_the_whole_household(tmp_path, household):
    """Everything written to JSON comes back equal, dates included."""
    milo = household.find_pet("Milo")
    milo.add_task(
        make_task("walk", "08:00", frequency="daily", due_date=date(2026, 10, 10))
    )
    household.find_pet("Luna").add_task(
        make_task("feed", "08:15", pet_id="luna", title="Kibble")
    )

    path = household.save_to_json(str(tmp_path / "data.json"))
    restored = Owner.load_from_json(path)

    assert restored == household
    assert len(restored.get_all_tasks()) == 2
    # json has no date type, so this is the assertion that matters: the string
    # it was stored as has been parsed back into a real date.
    assert restored.find_pet("Milo").find_task("walk").due_date == date(2026, 10, 10)


def test_load_from_json_returns_none_when_there_is_no_file(tmp_path):
    """A first run with no saved data starts empty rather than crashing."""
    assert Owner.load_from_json(str(tmp_path / "absent.json")) is None


def test_saved_task_keeps_working_after_a_reload(tmp_path, household):
    """A rebuilt task is a real Task, not a dict: its methods still work."""
    household.find_pet("Milo").add_task(
        make_task("walk", "08:00", duration_minutes=45, frequency="daily",
                  due_date=date(2026, 10, 10))
    )
    path = household.save_to_json(str(tmp_path / "data.json"))

    restored = Owner.load_from_json(path)
    task = restored.find_pet("Milo").find_task("walk")

    assert task.end_minutes() == 8 * 60 + 45
    assert task.repeats() is True
    follow_up = restored.find_pet("Milo").complete_task("walk")
    assert follow_up.due_date == date(2026, 10, 11)


# ---------------------------------------------------------------------------
# Late completion of a recurring task
# ---------------------------------------------------------------------------


def test_recurrence_anchors_to_due_date_not_completion_date(household):
    """A weekly Monday task finished on Thursday stays a Monday task."""
    milo = household.find_pet("Milo")
    monday = date(2026, 10, 5)
    assert monday.strftime("%A") == "Monday"
    milo.add_task(
        make_task("bath", "10:00", frequency="weekly", due_date=monday)
    )

    thursday = date(2026, 10, 8)
    follow_up = milo.complete_task("bath", completed_on=thursday)

    # Anchored to the due date, so the weekday is preserved. Anchoring to the
    # completion date would have produced Thursday 15 October and let the task
    # drift through the calendar on every late finish.
    assert follow_up.due_date == date(2026, 10, 12)
    assert follow_up.due_date.strftime("%A") == "Monday"


def test_recurrence_catches_up_on_a_task_finished_weeks_late(household):
    """A long-overdue task spawns a future occurrence, not another overdue one."""
    milo = household.find_pet("Milo")
    three_weeks_ago = date(2026, 9, 7)
    milo.add_task(
        make_task("bath", "10:00", frequency="weekly", due_date=three_weeks_ago)
    )

    today = date(2026, 10, 10)
    follow_up = milo.complete_task("bath", completed_on=today)

    assert follow_up.due_date > today
    assert follow_up.due_date == date(2026, 10, 12)
    # Whole weekly steps, so the original weekday survives the catch-up.
    assert follow_up.due_date.strftime("%A") == three_weeks_ago.strftime("%A")


def test_recurrence_advances_one_step_when_not_overdue(household):
    """A task completed early or on time moves exactly one interval, no further."""
    milo = household.find_pet("Milo")
    milo.add_task(
        make_task("walk", "08:00", frequency="daily", due_date=date(2026, 10, 12))
    )

    follow_up = milo.complete_task("walk", completed_on=date(2026, 10, 10))
    assert follow_up.due_date == date(2026, 10, 13)
