"""Tests for the PawPal+ system logic."""

from pawpal_system import Pet, Task


def make_task(task_id: str = "t1", time_str: str = "08:00") -> Task:
    """Build a throwaway task for a test to act on."""
    return Task(
        id=task_id,
        pet_id="milo",
        title="Park Walk",
        category="walk",
        time_str=time_str,
        duration_minutes=30,
        priority="high",
    )


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
