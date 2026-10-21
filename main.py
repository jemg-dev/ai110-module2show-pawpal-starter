from datetime import date, datetime, time

from pawpal_system import Owner, Pet, Scheduler, Task


def at(hour: int, minute: int = 0) -> datetime:
    return datetime.combine(date.today(), time(hour, minute))


def main() -> None:
    owner = Owner(name="Josue", username="josue", email="josue@email.com")

    perla = Pet(name="Perla", species="dog", breed="Maltese", age=10)
    mia = Pet(name="Mia", species="cat", breed="Siamese", age=2)
    owner.add_pet(perla)
    owner.add_pet(mia)

    # Tasks are deliberately added out of chronological order.
    perla.add_task(Task(pet_id="", title="Evening feeding", duration_minutes=15,
                      priority="medium", category="feeding", start=at(18)))
    mia.add_task(Task(pet_id="", title="Medication", duration_minutes=10,
                      priority="high", category="health", start=at(9, 30)))
    perla.add_task(Task(pet_id="", title="Afternoon walk", duration_minutes=30,
                      priority="medium", category="exercise", start=at(14, 5)))
    mia.add_task(Task(pet_id="", title="Play session", duration_minutes=20,
                      priority="low", category="play", start=at(9, 5)))
    perla.add_task(Task(pet_id="", title="Morning walk", duration_minutes=30,
                      priority="high", category="exercise", start=at(8), recurrence="daily"))
    mia.add_task(Task(pet_id="", title="Grooming", duration_minutes=25,
                      priority="low", category="grooming"))  # no start time

    # Completing the daily Morning walk also fills the status filter and spawns tomorrow's occurrence.
    morning = next(t for t in perla.tasks if t.title == "Morning walk")
    spawned = perla.complete_task(morning.task_id)

    # Two tasks deliberately booked at the same time: one clashes with another
    # task for the same pet, the other with a different pet's task.
    perla.add_task(Task(pet_id="", title="Vet call", duration_minutes=20,
                      priority="medium", category="health", start=at(14, 15)))  # overlaps Afternoon walk (Perla)
    mia.add_task(Task(pet_id="", title="Flea treatment", duration_minutes=15,
                      priority="medium", category="health", start=at(18, 0)))  # same time as Evening feeding (Perla)

    scheduler = Scheduler(date=date.today(), window_start=time(8), window_end=time(20))
    owner.add_schedule(scheduler)

    pet_names = {pet.pet_id: pet.name for pet in owner.pets}

    def show(heading: str, tasks) -> None:
        print(f"\n{heading}")
        print("-" * 60)
        if not tasks:
            print("(none)")
        for t in tasks:
            start = f"{t.start:%H:%M}" if t.start else "--:--"
            status = "done" if t.is_completed else "pending"
            print(f"{start}  {t.title:<16} {pet_names[t.pet_id]:<6} [{t.priority:<6}] {status}")

    print(f"Completed '{morning.title}' -> next occurrence starts {spawned.start:%a %Y-%m-%d %H:%M}"
          f" (today is {date.today():%a %Y-%m-%d})")

    everything = owner.filter_tasks()
    show("As added (out of order)", everything)
    show("sort_by_time()", scheduler.sort_by_time(everything))
    show("filter_tasks(completed=True)", owner.filter_tasks(completed=True))
    show("filter_tasks(completed=False)", owner.filter_tasks(completed=False))
    show("filter_tasks(pet_name='mia')", owner.filter_tasks(pet_name="mia"))
    show("Mia's pending tasks, sorted by time",
         scheduler.sort_by_time(owner.filter_tasks(completed=False, pet_name="Mia")))
    print("\nConflict check")
    print("-" * 60)
    conflicts = scheduler.find_conflicts()
    print("\n".join(conflicts) if conflicts else "No conflicts.")

    show("filter_tasks(pet_name='Rex')  [unknown pet]", owner.filter_tasks(pet_name="Rex"))


if __name__ == "__main__":
    main()
