"""Data models for PawPal+.

These classes mirror diagrams/uml.mmd. Attributes are declared with
dataclasses; methods are stubs to be filled in later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Task:
    """A single unit of pet care: a walk, a feeding, a medication, a vet visit."""

    id: str
    title: str
    category: str
    time_str: str
    frequency: str = "once"
    description: str = ""
    assigned_to: Optional[str] = None
    is_completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        raise NotImplementedError

    def mark_pending(self) -> None:
        """Reset this task back to not-done."""
        raise NotImplementedError


@dataclass
class Pet:
    """The animal receiving care, plus the tasks scheduled for it."""

    id: str
    name: str
    species: str
    breed: str = ""
    age: int = 0
    dietary_notes: str = ""
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        raise NotImplementedError

    def remove_task(self, task_id: str) -> bool:
        """Remove the task with this id. Return True if something was removed."""
        raise NotImplementedError

    def get_pending_tasks(self) -> List[Task]:
        """Return this pet's tasks that are not yet completed."""
        raise NotImplementedError


@dataclass
class Owner:
    """The household: contact info and the pets it is responsible for."""

    name: str
    email: str = ""
    phone: str = ""
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        raise NotImplementedError

    def get_all_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return every (pet, task) pair across all pets, for the scheduler."""
        raise NotImplementedError

    def find_pet(self, name: str) -> Optional[Pet]:
        """Look up a pet by name. Return None if there is no match."""
        raise NotImplementedError
