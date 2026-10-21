from datetime import date, datetime, time, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


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


# ---------------------------------------------------------------------------
# Helpers for the stress tests
# ---------------------------------------------------------------------------
DAY = date(2030, 1, 15)


def dt(h, m=0, day=DAY):
    return datetime.combine(day, time(h, m))


def make_owner(*pet_names):
    owner = Owner("Owner", "owner", "o@example.com")
    pets = [Pet(n, "dog") for n in pet_names]
    for p in pets:
        owner.add_pet(p)
    return (owner, *pets)


def make_scheduler(owner=None, start=time(8), end=time(20), day=DAY):
    s = Scheduler(day, start, end)
    if owner is not None:
        owner.add_schedule(s)
    return s


def task(title="t", minutes=30, start=None, **kw):
    return Task(pet_id="", title=title, duration_minutes=minutes, start=start, **kw)


# ---------------------------------------------------------------------------
# 1. Sorting
# ---------------------------------------------------------------------------
def test_sort_by_time_orders_out_of_order_tasks_earliest_first():
    s = make_scheduler()
    tasks = [task("c", start=dt(14, 30)), task("a", start=dt(8)), task("b", start=dt(9, 5))]
    assert [t.title for t in s.sort_by_time(tasks)] == ["a", "b", "c"]


def test_sort_by_time_zero_padding_puts_0905_before_1430():
    s = make_scheduler()
    late, early = task("late", start=dt(14, 30)), task("early", start=dt(9, 5))
    assert s.sort_by_time([late, early]) == [early, late]


def test_sort_by_time_unscheduled_tasks_sort_last():
    s = make_scheduler()
    none1, a, none2, b = task("n1"), task("a", start=dt(23, 59)), task("n2"), task("b", start=dt(0, 0))
    result = s.sort_by_time([none1, a, none2, b])
    assert result[:2] == [b, a]
    assert {t.title for t in result[2:]} == {"n1", "n2"}


def test_sort_by_time_does_not_mutate_input():
    s = make_scheduler()
    tasks = [task("c", start=dt(14)), task("a", start=dt(8)), task("n")]
    snapshot = list(tasks)
    result = s.sort_by_time(tasks)
    assert tasks == snapshot and result is not tasks


def test_sort_by_time_identical_start_times_are_stable():
    s = make_scheduler()
    first, second, third = task("1", start=dt(9)), task("2", start=dt(9)), task("3", start=dt(9))
    result = s.sort_by_time([first, second, third])
    assert [t.title for t in result] == ["1", "2", "3"]


def test_sort_by_time_empty_and_defaults_to_own_tasks():
    s = make_scheduler()
    assert s.sort_by_time([]) == []
    s.add_task_to_schedule(task("late"), dt(15))
    s.add_task_to_schedule(task("early"), dt(9))
    assert [t.title for t in s.sort_by_time()] == ["early", "late"]
    assert [t.title for t in s.get_daily_schedule()] == ["early", "late"]


# ---------------------------------------------------------------------------
# 2. Recurrence
# ---------------------------------------------------------------------------
def test_daily_recurrence_keeps_original_time_of_day_and_copies_fields():
    owner, pet = make_owner("Rex")
    t = task("Meds", 10, dt(7, 45), recurrence="daily", priority="high", category="health")
    pet.add_task(t)
    nxt = pet.complete_task(t.task_id)
    assert nxt.start == datetime.combine(date.today() + timedelta(days=1), time(7, 45))
    assert (nxt.title, nxt.duration_minutes, nxt.priority, nxt.category, nxt.recurrence) == \
           ("Meds", 10, "high", "health", "daily")
    assert nxt.task_id != t.task_id and nxt.is_completed is False and t.is_completed is True


def test_recurring_task_without_start_spawns_unscheduled_task():
    pet, t = _recurring("daily", None)
    nxt = pet.complete_task(t.task_id)
    assert nxt is not None and nxt.start is None


def test_recurrence_chain_keeps_spawning_from_today():
    pet, t = _recurring("daily", dt(8))
    n1 = pet.complete_task(t.task_id)
    n2 = pet.complete_task(n1.task_id)
    assert n2.start.date() == date.today() + timedelta(days=1)
    assert len(pet.tasks) == 3
    assert [x.is_completed for x in pet.tasks] == [True, True, False]


def test_completing_twice_never_duplicates_weekly_task():
    pet, t = _recurring("weekly", dt(8))
    assert pet.complete_task(t.task_id) is not None
    for _ in range(3):
        assert pet.complete_task(t.task_id) is None
    assert len(pet.tasks) == 2


def test_complete_task_unknown_id_raises_value_error():
    pet, _ = _recurring("daily", dt(8))
    with pytest.raises(ValueError):
        pet.complete_task("does-not-exist")
    assert len(pet.tasks) == 1


def test_complete_task_on_pet_with_no_tasks_raises():
    with pytest.raises(ValueError):
        Pet("Empty", "cat").complete_task("anything")


def test_complete_task_only_looks_at_its_own_pets_tasks():
    owner, a, b = make_owner("A", "B")
    t = task("walk", start=dt(8), recurrence="daily")
    a.add_task(t)
    with pytest.raises(ValueError):
        b.complete_task(t.task_id)
    assert t.is_completed is False


# ---------------------------------------------------------------------------
# 3. Conflict detection
# ---------------------------------------------------------------------------
def test_conflicts_identical_start_times_flagged():
    owner, a, b = make_owner("A", "B")
    a.add_task(task("x", 30, dt(9)))
    b.add_task(task("y", 30, dt(9)))
    w = make_scheduler(owner).find_conflicts()
    assert len(w) == 1 and "different pets" in w[0] and w[0].startswith("WARNING")


def test_conflicts_same_pet_identical_start_flagged():
    owner, a = make_owner("A")
    a.add_task(task("x", 30, dt(9)))
    a.add_task(task("y", 30, dt(9)))
    w = make_scheduler(owner).find_conflicts()
    assert len(w) == 1 and "same pet" in w[0]


def test_conflicts_back_to_back_not_flagged():
    owner, a = make_owner("A")
    a.add_task(task("x", 30, dt(9)))
    a.add_task(task("y", 30, dt(9, 30)))
    assert make_scheduler(owner).find_conflicts() == []


def test_conflicts_one_minute_overlap_flagged():
    owner, a = make_owner("A")
    a.add_task(task("x", 31, dt(9)))
    a.add_task(task("y", 30, dt(9, 30)))
    assert len(make_scheduler(owner).find_conflicts()) == 1


def test_conflicts_long_task_overlapping_several_short_ones():
    owner, a = make_owner("A")
    a.add_task(task("long", 180, dt(9)))
    a.add_task(task("s1", 30, dt(9, 30)))
    a.add_task(task("s2", 30, dt(10)))
    a.add_task(task("s3", 30, dt(13)))        # after the long task ends
    w = make_scheduler(owner).find_conflicts()
    assert len(w) == 2 and all("long" in x for x in w)


def test_conflicts_ignore_completed_untimed_and_other_day_tasks():
    owner, a = make_owner("A")
    a.add_task(task("live", 60, dt(9)))
    done = task("done", 60, dt(9)); done.is_completed = True
    a.add_task(done)
    a.add_task(task("untimed", 60))
    a.add_task(task("tomorrow", 60, dt(9, day=DAY + timedelta(days=1))))
    a.add_task(task("yesterday", 60, dt(9, day=DAY - timedelta(days=1))))
    assert make_scheduler(owner).find_conflicts() == []


def test_conflicts_three_way_pileup_reports_every_pair():
    owner, a, b = make_owner("A", "B")
    a.add_task(task("1", 60, dt(9)))
    a.add_task(task("2", 60, dt(9)))
    b.add_task(task("3", 60, dt(9)))
    assert len(make_scheduler(owner).find_conflicts()) == 3


def test_conflicts_never_raise_on_odd_input():
    s = make_scheduler()
    assert s.find_conflicts() == []                       # no owner, no tasks
    owner, _ = make_owner("A")
    assert make_scheduler(owner).find_conflicts() == []   # pet with no tasks
    orphan = [task("x", 30, dt(9)), task("y", 30, dt(9))]
    w = s.find_conflicts(orphan)                          # pet_id unknown, no owner
    assert len(w) == 1 and "unknown pet" in w[0]


def test_conflicts_accepts_explicit_task_list():
    owner, a = make_owner("A")
    a.add_task(task("x", 60, dt(9)))
    a.add_task(task("y", 60, dt(9)))
    s = make_scheduler(owner)
    assert s.find_conflicts([]) == []
    assert len(s.find_conflicts()) == 1


# ---------------------------------------------------------------------------
# 4. Auto-scheduling and constraints
# ---------------------------------------------------------------------------
def test_auto_schedule_places_higher_priority_first():
    owner, a = make_owner("A")
    a.add_task(task("low", 30, priority="low"))
    a.add_task(task("high", 30, priority="high"))
    a.add_task(task("med", 30, priority="medium"))
    s = make_scheduler(owner, time(8), time(10))
    assert s.auto_schedule() == []
    assert [(t.title, t.start) for t in s.get_daily_schedule()] == \
           [("high", dt(8)), ("med", dt(8, 30)), ("low", dt(9))]


def test_auto_schedule_low_priority_loses_when_window_is_tight():
    owner, a = make_owner("A")
    low, high = task("low", 60, priority="low"), task("high", 60, priority="high")
    a.add_task(low); a.add_task(high)
    s = make_scheduler(owner, time(8), time(9))
    unplaced = s.auto_schedule()
    assert unplaced == [low] and [t.title for t in s.tasks] == ["high"]


def test_auto_schedule_honors_fixed_start_time():
    owner, a = make_owner("A")
    a.add_task(task("fixed", 30, dt(13, 15), priority="low"))
    a.add_task(task("floating", 30, priority="high"))
    s = make_scheduler(owner)
    assert s.auto_schedule() == []
    starts = {t.title: t.start for t in s.tasks}
    assert starts == {"fixed": dt(13, 15), "floating": dt(8)}


def test_auto_schedule_floating_task_flows_around_fixed_task():
    owner, a = make_owner("A")
    a.add_task(task("fixed", 60, dt(8), priority="low"))
    a.add_task(task("floating", 30, priority="low"))
    s = make_scheduler(owner, time(8), time(12))
    assert s.auto_schedule() == []
    assert {t.title: t.start for t in s.tasks} == {"fixed": dt(8), "floating": dt(9)}


def test_auto_schedule_high_priority_floating_beats_clashing_low_fixed():
    owner, a = make_owner("A")
    a.add_task(task("fixed", 30, dt(8, 15), priority="low"))
    a.add_task(task("floating", 30, priority="high"))
    s = make_scheduler(owner, time(8), time(10))
    unplaced = s.auto_schedule()
    assert [t.title for t in unplaced] == ["fixed"]
    assert s.tasks[0].title == "floating" and s.tasks[0].start == dt(8)


def test_auto_schedule_two_fixed_tasks_at_same_time_second_unplaced():
    owner, a, b = make_owner("A", "B")
    first, second = task("first", 30, dt(9), priority="high"), task("second", 30, dt(9))
    a.add_task(first); b.add_task(second)
    s = make_scheduler(owner)
    assert s.auto_schedule() == [second]
    assert s.tasks == [first]


def test_auto_schedule_fixed_start_outside_window_is_unplaced():
    owner, a = make_owner("A")
    early, late = task("early", 30, dt(7, 30)), task("late", 30, dt(20, 0))
    a.add_task(early); a.add_task(late)
    s = make_scheduler(owner, time(8), time(20))
    assert {t.title for t in s.auto_schedule()} == {"early", "late"}
    assert s.tasks == []


def test_auto_schedule_task_longer_than_window_is_unplaced():
    owner, a = make_owner("A")
    big = task("big", 600)
    a.add_task(big)
    s = make_scheduler(owner, time(8), time(10))
    assert s.auto_schedule() == [big] and s.tasks == []


def test_auto_schedule_never_crosses_midnight():
    owner, a = make_owner("A")
    crosses = task("crosses", 60, dt(23, 30))
    fits = task("fits", 29, dt(23, 30))
    a.add_task(crosses); a.add_task(fits)
    s = make_scheduler(owner, time(22), time(23, 59))
    assert s.auto_schedule() == [crosses]
    assert s.tasks == [fits]
    assert all(t.end.date() == DAY for t in s.tasks)


def test_task_ending_exactly_at_window_end_fits_but_one_minute_more_does_not():
    s = make_scheduler(start=time(8), end=time(10))
    assert s.has_conflict(dt(9), 60) is False
    assert s.has_conflict(dt(9), 61) is True
    assert s.has_conflict(dt(8), 120) is False
    assert s.has_conflict(dt(8), 121) is True
    assert s.has_conflict(dt(7, 59), 10) is True           # starts a minute early


def test_auto_schedule_exact_fit_at_window_end_vs_one_minute_over():
    owner, a = make_owner("A")
    exact = task("exact", 60, dt(9))
    a.add_task(exact)
    s = make_scheduler(owner, time(8), time(10))
    assert s.auto_schedule() == [] and s.tasks == [exact]

    owner2, b = make_owner("B")
    over = task("over", 61, dt(9))
    b.add_task(over)
    s2 = make_scheduler(owner2, time(8), time(10))
    assert s2.auto_schedule() == [over] and s2.tasks == []


def test_has_conflict_rejects_other_day_and_overlap_but_allows_adjacent():
    s = make_scheduler()
    s.add_task_to_schedule(task("a", 30), dt(9))
    assert s.has_conflict(dt(9, 29), 10) is True
    assert s.has_conflict(dt(9, 30), 10) is False
    assert s.has_conflict(dt(8, 30), 30) is False
    assert s.has_conflict(dt(8, 31), 30) is True
    assert s.has_conflict(dt(9, day=DAY + timedelta(days=1)), 10) is True


def test_add_task_to_schedule_rejects_duplicate_and_conflict():
    s = make_scheduler()
    t = task("a", 30)
    s.add_task_to_schedule(t, dt(9))
    with pytest.raises(ValueError):
        s.add_task_to_schedule(t, dt(11))
    with pytest.raises(ValueError):
        s.add_task_to_schedule(task("b", 30), dt(9, 15))
    assert len(s.tasks) == 1


def test_auto_schedule_skips_completed_and_other_day_tasks():
    owner, a = make_owner("A")
    done = task("done", 30); done.is_completed = True
    other_day = task("other", 30, dt(9, day=DAY + timedelta(days=1)))
    a.add_task(done); a.add_task(other_day)
    s = make_scheduler(owner)
    assert s.auto_schedule() == [] and s.tasks == []
    assert other_day.start == dt(9, day=DAY + timedelta(days=1))   # untouched


def test_auto_schedule_is_idempotent():
    owner, a = make_owner("A")
    a.add_task(task("x", 30)); a.add_task(task("y", 30))
    s = make_scheduler(owner)
    s.auto_schedule()
    snapshot = [(t.task_id, t.start) for t in s.tasks]
    assert s.auto_schedule() == []
    assert [(t.task_id, t.start) for t in s.tasks] == snapshot


def test_auto_schedule_across_multiple_pets_produces_no_conflicts():
    owner, a, b = make_owner("A", "B")
    for i in range(4):
        a.add_task(task(f"a{i}", 45)); b.add_task(task(f"b{i}", 45))
    s = make_scheduler(owner, time(8), time(20))
    assert s.auto_schedule() == []
    assert len(s.tasks) == 8 and s.find_conflicts() == []


def test_auto_schedule_fills_window_then_overflow_goes_to_unplaced():
    owner, a = make_owner("A")
    for i in range(5):
        a.add_task(task(f"t{i}", 30))
    s = make_scheduler(owner, time(8), time(10))      # room for exactly 4
    unplaced = s.auto_schedule()
    assert len(s.tasks) == 4 and len(unplaced) == 1
    assert max(t.end for t in s.tasks) == dt(10)


def test_auto_schedule_without_owner_raises():
    with pytest.raises(ValueError):
        make_scheduler().auto_schedule()


def test_auto_schedule_with_owner_with_no_pets_does_nothing():
    owner, = make_owner()
    s = make_scheduler(owner)
    assert s.auto_schedule() == [] and s.tasks == []


def test_find_next_available_slot_variants():
    s = make_scheduler(start=time(8), end=time(12))
    assert s.find_next_available_slot(30) == dt(8)                   # empty day
    s.add_task_to_schedule(task("a", 30), dt(8))
    s.add_task_to_schedule(task("b", 30), dt(9))
    assert s.find_next_available_slot(30) == dt(8, 30)               # exact gap fit
    assert s.find_next_available_slot(31) == dt(9, 30)               # gap too small
    assert s.find_next_available_slot(150) == dt(9, 30)              # ends exactly at 12:00
    assert s.find_next_available_slot(151) is None                   # one minute too long


def test_find_next_available_slot_full_window_returns_none():
    s = make_scheduler(start=time(8), end=time(9))
    s.add_task_to_schedule(task("a", 60), dt(8))
    assert s.find_next_available_slot(1) is None


# ---------------------------------------------------------------------------
# 5. Filtering
# ---------------------------------------------------------------------------
def _filter_fixture():
    owner, rex, mia = make_owner("Rex", "Mia")
    r1, r2 = task("r1"), task("r2"); r2.is_completed = True
    m1, m2 = task("m1"), task("m2"); m1.is_completed = True
    rex.add_task(r1); rex.add_task(r2); mia.add_task(m1); mia.add_task(m2)
    return owner, r1, r2, m1, m2


def test_filter_no_arguments_returns_everything_in_pet_order():
    owner, r1, r2, m1, m2 = _filter_fixture()
    assert owner.filter_tasks() == [r1, r2, m1, m2]


def test_filter_by_completed_and_pending():
    owner, r1, r2, m1, m2 = _filter_fixture()
    assert owner.filter_tasks(completed=True) == [r2, m1]
    assert owner.filter_tasks(completed=False) == [r1, m2]


def test_filter_by_pet_name_is_case_insensitive():
    owner, r1, r2, m1, m2 = _filter_fixture()
    for name in ("mia", "MIA", "Mia", "mIa"):
        assert owner.filter_tasks(pet_name=name) == [m1, m2]


def test_filter_by_both_completed_and_pet():
    owner, r1, r2, m1, m2 = _filter_fixture()
    assert owner.filter_tasks(completed=False, pet_name="rex") == [r1]
    assert owner.filter_tasks(completed=True, pet_name="MIA") == [m1]


def test_filter_unknown_pet_returns_empty_list():
    owner, *_ = _filter_fixture()
    assert owner.filter_tasks(pet_name="Ghost") == []
    assert owner.filter_tasks(completed=True, pet_name="Ghost") == []
    assert owner.filter_tasks(pet_name="") == []


def test_filter_owner_with_no_pets_and_pet_with_no_tasks():
    empty_owner = Owner("o", "o", "o")
    assert empty_owner.filter_tasks() == []
    assert empty_owner.filter_tasks(completed=False, pet_name="Rex") == []
    assert empty_owner.get_all_tasks() == []
    owner, rex = make_owner("Rex")
    assert owner.filter_tasks() == [] and owner.filter_tasks(pet_name="rex") == []


def test_filter_reflects_completion_after_recurring_spawn():
    owner, rex = make_owner("Rex")
    t = task("walk", 30, dt(8), recurrence="daily")
    rex.add_task(t)
    nxt = rex.complete_task(t.task_id)
    assert owner.filter_tasks(completed=True) == [t]
    assert owner.filter_tasks(completed=False) == [nxt]


def test_get_all_tasks_priority_order_and_completed_toggle():
    owner, rex = make_owner("Rex")
    lo, hi, med = task("lo", priority="low"), task("hi", priority="high"), task("med")
    done = task("done", priority="high"); done.is_completed = True
    for t in (lo, hi, med, done):
        rex.add_task(t)
    assert owner.get_all_tasks() == [hi, med, lo]
    assert owner.get_all_tasks(include_completed=True) == [hi, done, med, lo]


# ---------------------------------------------------------------------------
# Sorting + conflicts together on a messy day
# ---------------------------------------------------------------------------
def test_messy_day_sort_then_conflicts_end_to_end():
    owner, a, b = make_owner("A", "B")
    a.add_task(task("c", 30, dt(14, 30)))
    a.add_task(task("a", 30, dt(9, 5)))
    b.add_task(task("b", 30, dt(9, 20)))      # overlaps a
    b.add_task(task("none", 30))
    s = make_scheduler(owner)
    ordered = s.sort_by_time(owner.filter_tasks())
    assert [t.title for t in ordered] == ["a", "b", "c", "none"]
    assert len(s.find_conflicts()) == 1


# ---------------------------------------------------------------------------
# Simple coverage tests: editing, removing, constraints, unscheduled tasks
# ---------------------------------------------------------------------------
def test_edit_task_updates_fields_and_rejects_unknown_field():
    t = task("walk")
    t.edit_task(title="run", duration_minutes=45, priority="high")
    assert (t.title, t.duration_minutes, t.priority) == ("run", 45, "high")
    with pytest.raises(AttributeError):
        t.edit_task(task_id="new-id")


def test_edit_pet_updates_fields_and_rejects_unknown_field():
    pet = Pet("Rex", "dog")
    pet.edit_pet(name="Max", age=3)
    assert (pet.name, pet.age) == ("Max", 3)
    with pytest.raises(AttributeError):
        pet.edit_pet(pet_id="new-id")


def test_unscheduled_task_has_no_end_and_never_overlaps():
    t = task("walk")
    assert t.end is None
    assert t.overlaps(dt(9), 30) is False


def test_remove_task_from_pet():
    pet = Pet("Rex", "dog")
    keep, drop = task("keep"), task("drop")
    pet.add_task(keep); pet.add_task(drop)
    pet.remove_task(drop.task_id)
    assert pet.tasks == [keep]


def test_remove_task_from_schedule():
    s = make_scheduler()
    keep, drop = task("keep"), task("drop")
    s.add_task_to_schedule(keep, dt(9))
    s.add_task_to_schedule(drop, dt(10))
    s.remove_task_from_schedule(drop.task_id)
    assert s.tasks == [keep]


def test_remove_pet_from_owner():
    owner, a, b = make_owner("A", "B")
    owner.remove_pet(a.pet_id)
    assert owner.pets == [b]
    assert owner.get_pet(a.pet_id) is None


def test_check_task_constraints_flags_allergy_and_diet():
    pet = Pet("Rex", "dog", allergies=["chicken"], dietary_restrictions=["grain"])
    warnings = pet.check_task_constraints(task("Feed chicken and grain treats"))
    assert len(warnings) == 2
    assert "allergic" in warnings[0] and "dietary restriction" in warnings[1]


def test_check_task_constraints_is_case_insensitive_and_clean_task_is_ok():
    pet = Pet("Rex", "dog", allergies=["Chicken"])
    assert len(pet.check_task_constraints(task("CHICKEN dinner"))) == 1
    assert pet.check_task_constraints(task("Morning walk")) == []


def test_find_next_available_slot_skips_task_that_ends_before_cursor():
    s = make_scheduler(start=time(8), end=time(12))
    s.tasks = [task("long", 120, dt(8)), task("inside", 30, dt(8, 30))]  # inside is covered by long
    assert s.find_next_available_slot(30) == dt(10)
