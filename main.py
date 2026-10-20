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

    perla.add_task(Task(pet_id="", title="Morning walk", duration_minutes=30,
                      priority="high", category="exercise", recurrence="daily"))
    perla.add_task(Task(pet_id="", title="Evening feeding", duration_minutes=15,
                      priority="medium", category="feeding", start=at(18)))
    mia.add_task(Task(pet_id="", title="Medication", duration_minutes=10,
                      priority="high", category="health", start=at(9, 30)))
    mia.add_task(Task(pet_id="", title="Play session", duration_minutes=20,
                      priority="low", category="play"))

    scheduler = Scheduler(date=date.today(), window_start=time(8), window_end=time(20))
    owner.add_schedule(scheduler)

    unplaced = scheduler.auto_schedule()

    pet_names = {pet.pet_id: pet.name for pet in owner.pets}

    print(f"Today's Schedule - {scheduler.date:%A, %B %d, %Y}")
    print(f"Owner: {owner.name}  |  Window: {scheduler.window_start:%H:%M}-{scheduler.window_end:%H:%M}")
    print("-" * 60)
    for task in scheduler.get_daily_schedule():
        print(f"{task.start:%H:%M}-{task.end:%H:%M}  {task.title:<18} "
              f"{pet_names[task.pet_id]:<5} [{task.priority}]")

    if unplaced:
        print("-" * 60)
        print("Could not schedule: " + ", ".join(t.title for t in unplaced))


if __name__ == "__main__":
    main()
