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
        """Mark this task complete and build its next occurrence if it repeats.

        For a "daily" or "weekly" task the next occurrence is a copy with a new
        task_id, is_completed=False, and a start of today + timedelta(days=1)
        or timedelta(weeks=1) at the original time of day (no start stays
        None). The caller is responsible for storing it; see Pet.complete_task.

        Returns:
            The new Task for a recurring task, otherwise None. Completing an
            already-completed task does nothing and returns None, so repeat
            calls can't create duplicates.
        """
        if self.is_completed:
            return None
        self.is_completed = True
        delta = RECURRENCE_DELTA.get(self.recurrence)
        if delta is None:
            return None
        next_start = (datetime.combine(date.today() + delta, self.start.time())
                      if self.start else None)
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

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Complete one of this pet's tasks, spawning the next occurrence.

        Calls Task.mark_complete and, for a daily/weekly task, adds the new
        occurrence to this pet's task list.

        Args:
            task_id: The id of the task to complete.

        Returns:
            The newly created next occurrence, or None if the task doesn't repeat.

        Raises:
            ValueError: If this pet has no task with that id.
        """
        task = next((t for t in self.tasks if t.task_id == task_id), None)
        if task is None:
            raise ValueError(f"{self.name} has no task with id '{task_id}'")
        next_task = task.mark_complete()
        if next_task is not None:
            self.add_task(next_task)
        return next_task

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

    def sort_by_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Sort tasks chronologically by time of day.

        The sort key is the task's start formatted as a zero-padded "HH:MM"
        string, which orders correctly as plain text ("09:05" < "14:30").

        Args:
            tasks: Tasks to sort. Defaults to this schedule's own tasks.

        Returns:
            A new list ordered earliest to latest. Tasks with no start time
            sort last. The input list is not modified.
        """
        tasks = self.tasks if tasks is None else tasks
        return sorted(tasks, key=lambda t: t.start.strftime("%H:%M") if t.start else "99:99")

    def find_conflicts(self, tasks: Optional[List[Task]] = None) -> List[str]:
        """Detect overlapping tasks and report them as warnings, never errors.

        Only pending tasks that have a start time on this schedule's date are
        considered. They are sorted by start time and each task is compared
        with the tasks that start before it ends; the inner loop stops at the
        first task that starts after it ends, since later ones can't overlap.
        Back-to-back tasks (one ends exactly when the next starts) do not
        conflict.

        Args:
            tasks: Tasks to check. Defaults to the owner's pending tasks
                (or this schedule's own tasks if it has no owner).

        Returns:
            One message per overlapping pair, noting whether the tasks belong
            to the same pet or different pets. An empty list means no conflicts.
        """
        if tasks is None:
            tasks = self.owner.get_all_tasks() if self.owner else self.tasks
        timed = self.sort_by_time([t for t in tasks
                                   if t.start is not None and t.start.date() == self.date
                                   and not t.is_completed])

        def label(task: Task) -> str:
            pet = self.owner.get_pet(task.pet_id) if self.owner else None
            return (f"'{task.title}' ({pet.name if pet else 'unknown pet'}, "
                    f"{task.start:%H:%M}-{task.end:%H:%M})")

        warnings = []
        for i, a in enumerate(timed):
            for b in timed[i + 1:]:
                if b.start >= a.end:
                    break  # sorted by start: nothing later can overlap a
                kind = "same pet" if a.pet_id == b.pet_id else "different pets"
                warnings.append(f"WARNING: conflict ({kind}): {label(a)} overlaps {label(b)}")
        return warnings

    def get_daily_schedule(self) -> List[Task]:
        """Tasks sorted by start time."""
        return self.sort_by_time()

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

    def filter_tasks(self, completed: Optional[bool] = None,
                     pet_name: Optional[str] = None) -> List[Task]:
        """Return the owner's tasks that match every filter given.

        Args:
            completed: True for finished tasks, False for pending ones,
                None to ignore completion status.
            pet_name: Only tasks for the pet with this name (case-insensitive),
                None to include every pet.

        Returns:
            Matching tasks in pet order, then the order they were added. An
            unknown pet name returns an empty list.
        """
        return [t for pet in self.pets
                if pet_name is None or pet.name.lower() == pet_name.lower()
                for t in pet.tasks
                if completed is None or t.is_completed == completed]

    def get_all_tasks(self, include_completed: bool = False) -> List[Task]:
        """All pets' tasks, ordered by priority (high first)."""
        tasks = [t for pet in self.pets for t in pet.tasks
                 if include_completed or not t.is_completed]
        return sorted(tasks, key=lambda t: PRIORITY_RANK[t.priority])
