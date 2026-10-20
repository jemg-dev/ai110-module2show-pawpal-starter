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
