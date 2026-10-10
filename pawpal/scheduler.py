"""Scheduling service for PawPal+.

The Scheduler stores no task data of its own. It receives tasks from an Owner
or a Pet, then orders, filters, and inspects them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .models import Owner, Task


@dataclass
class Scheduler:
    """Stateless planning engine over a list of tasks."""

    owner: Optional[Owner] = None

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Return the tasks ordered chronologically by their "HH:MM" time_str."""
        raise NotImplementedError

    def filter_by_status(self, tasks: List[Task], completed: bool) -> List[Task]:
        """Return only the tasks whose is_completed matches `completed`."""
        raise NotImplementedError

    def detect_conflicts(self, tasks: List[Task]) -> List[str]:
        """Return a message for each time slot holding more than one task."""
        raise NotImplementedError

    def handle_recurring(self, task: Task) -> Optional[Task]:
        """Spawn the next occurrence of a completed recurring task.

        Return None when the task does not repeat or is not yet complete.
        """
        raise NotImplementedError
