from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import List, Optional


@dataclass
class Task:
    task_id: int
    title: str
    description: str = ""
    duration_minutes: int = 0
    priority: str = "medium"
    category: str = ""
    is_recurring: bool = False
    is_completed: bool = False
    start_time: Optional[time] = None
    end_time: Optional[time] = None

    def create_task(self) -> None:
        pass

    def delete_task(self) -> None:
        pass

    def edit_task(self) -> None:
        pass

    def mark_complete(self) -> None:
        pass


@dataclass
class Pet:
    pet_id: int
    name: str
    species: str
    breed: str = ""
    age: int = 0
    dietary_restrictions: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    notes: str = ""
    tasks: List[Task] = field(default_factory=list)

    def add_pet(self) -> None:
        pass

    def remove_pet(self) -> None:
        pass

    def edit_pet(self) -> None:
        pass

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task_id: int) -> None:
        pass


@dataclass
class Scheduler:
    schedule_id: int
    date: date
    start_time: time
    end_time: time
    tasks: List[Task] = field(default_factory=list)

    def add_task_to_schedule(self, task: Task, start_time: time) -> None:
        pass

    def remove_task_from_schedule(self, task_id: int) -> None:
        pass

    def has_conflict(self, start_time: time, duration: int) -> bool:
        pass

    def get_daily_schedule(self) -> List[Task]:
        pass

    def find_next_available_slot(self, duration: int) -> Optional[time]:
        pass


@dataclass
class Owner:
    owner_id: int
    name: str
    username: str
    email: str
    pets: List[Pet] = field(default_factory=list)
    schedules: List[Scheduler] = field(default_factory=list)

    def create_user(self) -> None:
        pass

    def delete_user(self) -> None:
        pass

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet_id: int) -> None:
        pass

    def get_all_tasks(self) -> List[Task]:
        pass
