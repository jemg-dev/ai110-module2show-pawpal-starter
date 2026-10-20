from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from typing import List, Literal, Optional
from uuid import uuid4

Priority = Literal["low", "medium", "high"]
Recurrence = Literal["none", "daily", "weekly"]

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
RECURRENCE_DELTA = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


def new_id() -> str:
    return uuid4().hex


def _apply_fields(obj, allowed: set, fields: dict) -> None:
    """Set only known, editable attributes; reject anything else."""
    for name, value in fields.items():
        if name not in allowed:
            raise AttributeError(f"{type(obj).__name__} has no editable field '{name}'")
        setattr(obj, name, value)


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

    _EDITABLE = {"title", "duration_minutes", "description", "priority",
                 "category", "recurrence", "is_completed", "start"}

    @property
    def end(self) -> Optional[datetime]:
        """Derived from start + duration_minutes; None if unscheduled."""
        if self.start is None:
            return None
        return self.start + timedelta(minutes=self.duration_minutes)

    def overlaps(self, start: datetime, duration_minutes: int) -> bool:
        """Return True if this task's time range overlaps the given range."""
        if self.start is None:
            return False
        other_end = start + timedelta(minutes=duration_minutes)
        return self.start < other_end and start < self.end

    def edit_task(self, **fields) -> None:
        """Update this task's editable fields from keyword arguments."""
        _apply_fields(self, self._EDITABLE, fields)

    def mark_complete(self) -> Optional[Task]:
        """Mark done; return the next occurrence if recurring, else None."""
        self.is_completed = True
        delta = RECURRENCE_DELTA.get(self.recurrence)
        if delta is None:
            return None
        next_start = self.start + delta if self.start else None
        return replace(self, is_completed=False, start=next_start, task_id=new_id())


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

    _EDITABLE = {"name", "species", "breed", "age", "dietary_restrictions",
                 "allergies", "notes"}

    def edit_pet(self, **fields) -> None:
        """Update this pet's editable fields from keyword arguments."""
        _apply_fields(self, self._EDITABLE, fields)

    def add_task(self, task: Task) -> None:
        """Should set task.pet_id to this pet's id."""
        task.pet_id = self.pet_id
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id from this pet."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def check_task_constraints(self, task: Task) -> List[str]:
        """Return warnings where a task conflicts with dietary restrictions or allergies."""
        text = f"{task.title} {task.description} {task.category}".lower()
        warnings = []
        for item in self.allergies:
            if item.lower() in text:
                warnings.append(f"{self.name} is allergic to '{item}' (task: {task.title})")
        for item in self.dietary_restrictions:
            if item.lower() in text:
                warnings.append(f"{self.name} has a dietary restriction on '{item}' (task: {task.title})")
        return warnings


@dataclass
class Scheduler:
    """The brain: plans one day, bounded by a time window. It reads tasks for
    all of an owner's pets through Owner.get_all_tasks()."""
    date: date
    window_start: time
    window_end: time
    tasks: List[Task] = field(default_factory=list)
    schedule_id: str = field(default_factory=new_id)
    # Set by Owner.add_schedule; excluded from repr/eq to avoid a reference cycle.
    owner: Optional[Owner] = field(default=None, repr=False, compare=False)

    def _window_bounds(self) -> tuple[datetime, datetime]:
        """Return the schedule window as a (start, end) datetime pair."""
        return (datetime.combine(self.date, self.window_start),
                datetime.combine(self.date, self.window_end))

    def add_task_to_schedule(self, task: Task, start: datetime) -> None:
        """Schedule a task at the given start, raising ValueError on duplicates or conflicts."""
        if any(t.task_id == task.task_id for t in self.tasks):
            raise ValueError(f"Task '{task.title}' is already scheduled")
        if self.has_conflict(start, task.duration_minutes):
            raise ValueError(f"Task '{task.title}' conflicts at {start:%H:%M}")
        task.start = start
        self.tasks.append(task)

    def remove_task_from_schedule(self, task_id: str) -> None:
        """Remove the task with the given id from this schedule."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def has_conflict(self, start: datetime, duration_minutes: int) -> bool:
        """Should also reject ranges outside the window or crossing midnight."""
        end = start + timedelta(minutes=duration_minutes)
        if start.date() != self.date or end.date() != self.date:
            return True
        window_start, window_end = self._window_bounds()
        if start < window_start or end > window_end:
            return True
        return any(t.overlaps(start, duration_minutes) for t in self.tasks)

    def get_daily_schedule(self) -> List[Task]:
        """Tasks sorted by start time."""
        return sorted(self.tasks, key=lambda t: t.start)

    def find_next_available_slot(self, duration_minutes: int) -> Optional[datetime]:
        """Single pass over sorted tasks; None if nothing fits."""
        need = timedelta(minutes=duration_minutes)
        cursor, window_end = self._window_bounds()
        for task in self.get_daily_schedule():
            if task.end <= cursor:
                continue
            if task.start - cursor >= need:
                return cursor
            cursor = max(cursor, task.end)
        return cursor if window_end - cursor >= need else None

    def get_owner_tasks(self, include_completed: bool = False) -> List[Task]:
        """Every pet's tasks via the Owner (priority-ordered)."""
        if self.owner is None:
            raise ValueError("Scheduler has no owner; add it with Owner.add_schedule()")
        return self.owner.get_all_tasks(include_completed)

    def auto_schedule(self) -> List[Task]:
        """Place the owner's pending tasks (all pets) into this day, highest
        priority first. Returns the tasks that could not be placed."""
        scheduled_ids = {t.task_id for t in self.tasks}
        unplaced = []
        for task in self.get_owner_tasks():
            if task.task_id in scheduled_ids:
                continue
            if task.start is not None and task.start.date() != self.date:
                continue  # belongs to another day
            slot = task.start or self.find_next_available_slot(task.duration_minutes)
            if slot is None or self.has_conflict(slot, task.duration_minutes):
                unplaced.append(task)
            else:
                self.add_task_to_schedule(task, slot)
        return unplaced


@dataclass
class Owner:
    name: str
    username: str
    email: str
    pets: List[Pet] = field(default_factory=list)
    schedules: List[Scheduler] = field(default_factory=list)
    owner_id: str = field(default_factory=new_id)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove the pet with the given id from this owner."""
        self.pets = [p for p in self.pets if p.pet_id != pet_id]

    def get_pet(self, pet_id: str) -> Optional[Pet]:
        """Return the pet with the given id, or None if not found."""
        return next((p for p in self.pets if p.pet_id == pet_id), None)

    def add_schedule(self, schedule: Scheduler) -> None:
        """Attach a schedule to this owner and link it back to the owner."""
        schedule.owner = self
        self.schedules.append(schedule)

    def get_all_tasks(self, include_completed: bool = False) -> List[Task]:
        """All pets' tasks, ordered by priority (high first)."""
        tasks = [t for pet in self.pets for t in pet.tasks
                 if include_completed or not t.is_completed]
        return sorted(tasks, key=lambda t: PRIORITY_RANK[t.priority])
