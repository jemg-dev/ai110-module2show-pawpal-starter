from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import List, Literal, Optional
from uuid import uuid4

Priority = Literal["low", "medium", "high"]
Recurrence = Literal["none", "daily", "weekly"]


def new_id() -> str:
    return uuid4().hex


@dataclass
class Task:
    """A single task occurrence. A recurring task spawns its next occurrence
    (a new Task with a later start) when marked complete."""
    pet_id: str
    title: str
    duration_minutes: int
    description: str = ""
    priority: Priority = "medium"
    category: str = ""
    recurrence: Recurrence = "none"
    is_completed: bool = False
    start: Optional[datetime] = None
    task_id: str = field(default_factory=new_id)

    @property
    def end(self) -> Optional[datetime]:
        """Derived from start + duration_minutes; None if unscheduled."""
        pass

    def overlaps(self, start: datetime, duration_minutes: int) -> bool:
        pass

    def edit_task(self, **fields) -> None:
        pass

    def mark_complete(self) -> Optional[Task]:
        """Mark done; return the next occurrence if recurring, else None."""
        pass


@dataclass
class Pet:
    name: str
    species: str
    breed: str = ""
    age: int = 0
    dietary_restrictions: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    notes: str = ""
    tasks: List[Task] = field(default_factory=list)
    pet_id: str = field(default_factory=new_id)

    def edit_pet(self, **fields) -> None:
        pass

    def add_task(self, task: Task) -> None:
        """Should set task.pet_id to this pet's id."""
        pass

    def remove_task(self, task_id: str) -> None:
        pass

    def check_task_constraints(self, task: Task) -> List[str]:
        """Return warnings where a task conflicts with dietary restrictions or allergies."""
        pass


@dataclass
class Scheduler:
    """One day's plan, bounded by a time window."""
    date: date
    window_start: time
    window_end: time
    tasks: List[Task] = field(default_factory=list)
    schedule_id: str = field(default_factory=new_id)

    def add_task_to_schedule(self, task: Task, start: datetime) -> None:
        pass

    def remove_task_from_schedule(self, task_id: str) -> None:
        pass

    def has_conflict(self, start: datetime, duration_minutes: int) -> bool:
        """Should also reject ranges outside the window or crossing midnight."""
        pass

    def get_daily_schedule(self) -> List[Task]:
        """Tasks sorted by start time."""
        pass

    def find_next_available_slot(self, duration_minutes: int) -> Optional[datetime]:
        """Single pass over sorted tasks; None if nothing fits."""
        pass


@dataclass
class Owner:
    name: str
    username: str
    email: str
    pets: List[Pet] = field(default_factory=list)
    schedules: List[Scheduler] = field(default_factory=list)
    owner_id: str = field(default_factory=new_id)

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet_id: str) -> None:
        pass

    def get_pet(self, pet_id: str) -> Optional[Pet]:
        pass

    def add_schedule(self, schedule: Scheduler) -> None:
        pass

    def get_all_tasks(self, include_completed: bool = False) -> List[Task]:
        """All pets' tasks, ordered by priority (high first)."""
        pass
