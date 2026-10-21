from pawpal_system import Pet, Task


def test_mark_complete_changes_task_status():
    task = Task(pet_id="", title="Morning walk", duration_minutes=30)
    assert task.is_completed is False

    task.mark_complete()

    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Perla", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(pet_id="", title="Evening feeding", duration_minutes=15))

    assert len(pet.tasks) == 1


def _recurring(recurrence, start=None):
    from pawpal_system import Pet, Task
    pet = Pet(name="Rex", species="dog")
    task = Task(pet_id="", title="Walk", duration_minutes=20, recurrence=recurrence, start=start)
    pet.add_task(task)
    return pet, task


def test_daily_task_spawns_next_occurrence_tomorrow():
    from datetime import date, datetime, time, timedelta
    start = datetime.combine(date.today() - timedelta(days=3), time(8, 15))
    pet, task = _recurring("daily", start)
    nxt = pet.complete_task(task.task_id)
    assert task.is_completed and nxt in pet.tasks and nxt.task_id != task.task_id
    assert not nxt.is_completed and nxt.pet_id == pet.pet_id
    assert nxt.start == datetime.combine(date.today() + timedelta(days=1), time(8, 15))


def test_weekly_task_spawns_next_occurrence_in_seven_days():
    from datetime import date, datetime, time, timedelta
    pet, task = _recurring("weekly", datetime.combine(date.today(), time(17, 0)))
    nxt = pet.complete_task(task.task_id)
    assert nxt.start.date() == date.today() + timedelta(days=7)


def test_non_recurring_task_spawns_nothing_and_double_complete_is_noop():
    pet, task = _recurring("none")
    assert pet.complete_task(task.task_id) is None
    assert len(pet.tasks) == 1
    pet2, t2 = _recurring("daily")
    assert pet2.complete_task(t2.task_id) is not None
    assert pet2.complete_task(t2.task_id) is None
    assert len(pet2.tasks) == 2


def test_find_conflicts_same_pet_and_different_pets_without_raising():
    from datetime import date, datetime, time
    from pawpal_system import Owner, Pet, Scheduler, Task
    at = lambda h, m=0: datetime.combine(date.today(), time(h, m))
    owner = Owner("o", "o", "o")
    a, b = Pet("A", "dog"), Pet("B", "cat")
    owner.add_pet(a); owner.add_pet(b)
    a.add_task(Task("", "walk", 30, start=at(9)))
    a.add_task(Task("", "bath", 30, start=at(9, 15)))    # same pet as walk
    b.add_task(Task("", "feed", 10, start=at(9, 20)))    # different pet
    b.add_task(Task("", "play", 10, start=at(9, 30)))    # back-to-back with walk: fine
    s = Scheduler(date.today(), time(8), time(20)); owner.add_schedule(s)
    w = s.find_conflicts()
    assert len(w) == 4 and any("same pet" in x for x in w) and any("different pets" in x for x in w)
    assert not any("play" in x and "walk" in x for x in w)
    assert Scheduler(date.today(), time(8), time(20)).find_conflicts() == []
