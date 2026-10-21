import streamlit as st
from datetime import date, datetime, time

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to **PawPal+**, your pet care planning assistant. Add your pets, list the care
they need each day, and PawPal+ builds a clear schedule that keeps everything on track.
"""
)

with st.expander("What PawPal+ can do", expanded=True):
    st.markdown(
        """
- **Track pets and tasks:** walks, feeding, medication, grooming and more, each with a duration and priority.
- **Plan your day:** place every pending task into today's window, highest priority first, and see anything that doesn't fit.
- **Catch conflicts:** get a warning when two tasks overlap, with a suggested free time to move one.
- **Stay organized:** view tasks sorted by time and filter them by pet or status.
- **Handle routines:** daily and weekly tasks automatically schedule their next occurrence when completed.
- **Stay safe:** get a warning when a task mentions one of your pet's allergies or dietary restrictions.
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")

# st.session_state persists across reruns, so only create the Owner once.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, username=owner_name.lower(), email="")
owner = st.session_state.owner

st.subheader("Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        if pet_name.strip():
            owner.add_pet(Pet(name=pet_name.strip(), species=species))
            st.success(f"Added {pet_name.strip()}!")
        else:
            st.error("Pet name is required.")

# Filled in after the task form below so the task counts are current.
pets_table = st.empty()

st.markdown("### Tasks")
if owner.pets:
    # Select by id: the widget may hand back a copy, so look the real Pet up on the owner.
    pet_id = st.selectbox(
        "Pet",
        [p.pet_id for p in owner.pets],
        format_func=lambda pid: f"{owner.get_pet(pid).name} ({owner.get_pet(pid).species})",
    )
    pet = owner.get_pet(pet_id)
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    recurrence = st.selectbox("Repeats", ["none", "daily", "weekly"])
    pick_start = st.checkbox("Choose a start time (otherwise the scheduler picks one)")
    start_time = st.time_input("Start time", value=time(9, 0), step=300, disabled=not pick_start)

    if st.button("Add task"):
        start = datetime.combine(date.today(), start_time) if pick_start else None
        task = Task(pet_id=pet.pet_id, title=task_title, duration_minutes=int(duration),
                    priority=priority, start=start, recurrence=recurrence)
        for warning in pet.check_task_constraints(task):
            st.warning(warning)
        pet.add_task(task)
        st.success(f"Added '{task_title}' for {pet.name}.")
else:
    st.info("Add a pet before adding tasks.")

pending = owner.filter_tasks(completed=False)
if pending:
    st.markdown("#### Mark a task complete")
    done_id = st.selectbox(
        "Task",
        [t.task_id for t in pending],
        format_func=lambda tid: next(
            f"{owner.get_pet(t.pet_id).name}: {t.title}" for t in pending if t.task_id == tid),
    )
    if st.button("Mark complete"):
        done = next(t for t in pending if t.task_id == done_id)
        next_task = owner.get_pet(done.pet_id).complete_task(done.task_id)
        if next_task is not None:
            st.success(f"Completed '{done.title}'. Next {done.recurrence} occurrence added.")
        else:
            st.success(f"Completed '{done.title}'.")

if owner.pets:
    pets_table.table([{"name": p.name, "species": p.species, "tasks": len(p.tasks)} for p in owner.pets])
else:
    pets_table.info("No pets yet. Add one above.")

pet_names = {p.pet_id: p.name for p in owner.pets}
# Throwaway scheduler (not added to owner.schedules) just to run the conflict check.
checker = Scheduler(date=date.today(), window_start=time(8, 0), window_end=time(20, 0))
checker.owner = owner
conflicts = checker.find_conflicts()
if conflicts:
    # One loud summary with the next step, then one specific line per clash.
    st.error(f"⚠️ {len(conflicts)} scheduling conflict(s) today. "
             "Delete one task in each pair using 'Delete a task' below, then re-add it at the suggested time.")
    for message in conflicts:
        st.warning(message.removeprefix("WARNING: "))
elif any(t.start for t in owner.get_all_tasks()):
    st.success("No scheduling conflicts today.")

all_tasks = owner.filter_tasks()
if all_tasks:
    with st.expander("Delete a task", expanded=bool(conflicts)):
        delete_id = st.selectbox(
            "Task to delete",
            [t.task_id for t in all_tasks],
            format_func=lambda tid: next(
                f"{pet_names[t.pet_id]}: {t.title} ({t.start:%H:%M})" if t.start
                else f"{pet_names[t.pet_id]}: {t.title}" for t in all_tasks if t.task_id == tid),
        )
        victim = next(t for t in all_tasks if t.task_id == delete_id)
        # Find a free slot among today's other pending timed tasks.
        planner = Scheduler(date=date.today(), window_start=time(8, 0), window_end=time(20, 0))
        planner.tasks = [t for t in all_tasks if t.task_id != delete_id and not t.is_completed
                         and t.start is not None and t.start.date() == planner.date]
        slot = planner.find_next_available_slot(victim.duration_minutes)
        if slot:
            st.info(f"Suggested time to re-add it: {slot:%H:%M} "
                    f"({victim.duration_minutes} min, {victim.priority} priority, repeats: {victim.recurrence}).")
        else:
            st.info("No free slot left today for this task; try a shorter duration.")
        if st.button("Delete task"):
            owner.get_pet(victim.pet_id).remove_task(delete_id)
            st.toast(f"Deleted '{victim.title}'. Re-add it with the form above.")
            st.rerun()

if any(p.tasks for p in owner.pets):
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        status = st.selectbox("Filter by status", ["All", "Pending", "Completed"])
    with fcol2:
        pet_filter = st.selectbox("Filter by pet", ["All"] + [p.name for p in owner.pets])
    shown = owner.filter_tasks(
        completed={"All": None, "Pending": False, "Completed": True}[status],
        pet_name=None if pet_filter == "All" else pet_filter,
    )
    if shown:
        st.caption("Sorted by start time; tasks without a time are listed last.")
        shown = checker.sort_by_time(shown)
        st.table([
            {"pet": pet_names[t.pet_id], "title": t.title,
             "start": t.start.strftime("%H:%M") if t.start else "auto",
             "duration_minutes": t.duration_minutes, "priority": t.priority,
             "status": "done" if t.is_completed else "pending"}
            for t in shown
        ])
    else:
        st.info("No tasks match these filters.")

st.divider()

st.subheader("Build Schedule")
st.caption("Places every pending task into today's 8:00-20:00 window, highest priority first.")

if st.button("Generate schedule"):
    schedule = Scheduler(date=date.today(), window_start=time(8, 0), window_end=time(20, 0))
    owner.add_schedule(schedule)
    unplaced = schedule.auto_schedule()
    if schedule.tasks:
        if unplaced:
            st.warning(f"Scheduled {len(schedule.tasks)} task(s); {len(unplaced)} did not fit.")
        else:
            st.success(f"All {len(schedule.tasks)} task(s) fit in today's window.")
        st.table([
            {"start": t.start.strftime("%H:%M"), "end": t.end.strftime("%H:%M"),
             "pet": pet_names[t.pet_id], "task": t.title, "priority": t.priority}
            for t in schedule.get_daily_schedule()
        ])
    else:
        st.info("No tasks to schedule.")
    for t in unplaced:
        st.warning(f"Could not fit '{t.title}' ({pet_names[t.pet_id]}) in today's window. "
                   "Shorten it, lower another task's priority, or move it to another day.")
