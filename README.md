# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## 🧩 System Overview

PawPal+ is built from four classes in `pawpal_system.py` (see `diagrams/uml_final.mmd` for the UML):

- **Owner:** the user account (name, username, email). It holds a list of pets and a list of schedules. It can add and remove pets, look one up by id, and attach a schedule. `get_all_tasks()` returns every pet's pending tasks ordered by priority, and `filter_tasks()` narrows them by completion status and pet name.
- **Pet:** one animal (name, species, breed, age, dietary restrictions, allergies, notes) and its own list of tasks. It can edit its info, add, remove and complete tasks, and warn when a task conflicts with its allergies or diet. `complete_task()` also stores the next occurrence of a recurring task.
- **Task:** one unit of care (title, description, duration, priority, category, repeat rule, completion status and an optional start time). It works out its own end time, checks whether it overlaps a time range, can be edited, and `mark_complete()` builds the next occurrence of a daily or weekly task.
- **Scheduler:** plans one day inside a time window (for example 08:00-20:00). It reads tasks for all of an owner's pets, sorts them by time, detects conflicts, finds free slots, and `auto_schedule()` places tasks by priority and returns any that don't fit.

How they connect: an Owner has many Pets, a Pet has many Tasks, and a Scheduler reads all of the Owner's tasks and schedules them into a day.

## ✨ Features

- **Multiple pets per owner:** each pet has its own task list, and the scheduler reads every pet's tasks through the owner.
- **Rich tasks:** title, duration, priority (low / medium / high), category, description, repeat rule and an optional fixed start time.
- **Sorting by time:** tasks are ordered by a zero-padded `"HH:MM"` key. Tasks without a start time go last, and the original list is never changed.
- **Filtering:** by completion status, by pet name (case-insensitive), or both. An unknown pet returns an empty list.
- **Conflict warnings:** any two pending, timed tasks on the same day whose time ranges overlap are reported, for the same pet or different pets. Back-to-back tasks are fine, and the check returns warnings instead of raising errors.
- **Daily and weekly recurrence:** completing a recurring task creates the next occurrence at the same time of day (today + 1 day or + 7 days). Completing a task twice never creates a duplicate.
- **Priority-based auto-scheduling:** pending tasks are placed high priority first. A fixed start time is honored; other tasks go into the earliest gap that fits. Nothing is placed outside the daily window or past midnight, and tasks that don't fit are returned as unplaced.
- **Free-slot search:** finds the earliest gap in the day long enough for a task, which the app uses to suggest a new time.
- **Pet-safety warnings:** a task whose title, description or category mentions one of the pet's allergies or dietary restrictions triggers a warning.
- **Streamlit UI:** add pets and tasks, mark tasks complete, filter, view the sorted table, see conflict banners, delete a task with a suggested re-add time, and generate the daily schedule.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

SAMPLE OUTPUT AFTER PHASE 2; STEP 2:
'''
Today's Schedule - Tuesday, October 20, 2026
Owner: Josue  |  Window: 08:00-20:00
------------------------------------------------------------
08:00-08:30  Morning walk       Perla [high]
08:30-08:50  Play session       Mia   [low]
09:30-09:40  Medication         Mia   [high]
18:00-18:15  Evening feeding    Perla [medium]
'''

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
=========================================================================================================== test session starts ============================================================================================================
platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\josue\Documents\Projects\ai110-module2show-pawpal-starter
plugins: anyio-4.15.1, cov-7.1.0
collected 67 items                                                                                                                                                                                                                          

tests\test_pawpal.py ...................................................................                                                                                                                                              [100%]

============================================================================================================== tests coverage ==============================================================================================================
_____________________________________________________________________________________________ coverage: platform win32, python 3.13.15-final-0 _____________________________________________________________________________________________

Name                   Stmts   Miss  Cover
------------------------------------------
pawpal_system.py         183      0   100%
tests\test_pawpal.py     462      0   100%
------------------------------------------
TOTAL                    645      0   100%
============================================================================================================ 67 passed in 0.19s ============================================================================================================

Given these test results and stress tests, I would give this a 4/5 confidence level just because there may always be something unaccounted for.

```

## 📐 Smarter Scheduling

Each feature is implemented by a method in `pawpal_system.py`.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time(tasks=None)` | Uses `sorted()` with a lambda key that formats each start as a zero-padded `"HH:MM"` string, which sorts correctly as text. Tasks with no start time go last. `Scheduler.get_daily_schedule()` uses it to display the day. |
| Filtering | `Owner.filter_tasks(completed=None, pet_name=None)` | Filters across all of an owner's pets by completion status (`True`/`False`), by pet name (case-insensitive), or both; a filter left as `None` is ignored. The Streamlit task table exposes it as "Filter by status" and "Filter by pet" dropdowns. |
| Conflict handling | `Scheduler.find_conflicts(tasks=None)` | Lightweight check that returns warning messages instead of raising errors. Sorts the day's pending, timed tasks and flags every pair whose time ranges overlap, for the same pet or different pets. Back-to-back tasks are not conflicts. Shown as yellow warnings in the app and printed by `main.py`. (`add_task_to_schedule()` still raises `ValueError` on a forced clash, and `auto_schedule()` reports clashes as unplaced.) |
| Recurring tasks | `Task.mark_complete()`, `Pet.complete_task(task_id)` | Tasks repeat `"none"`, `"daily"` or `"weekly"`. Completing one through `Pet.complete_task()` adds a new copy due today + 1 day (daily) or + 7 days (weekly), computed with `timedelta`, at the original time of day. Non-recurring tasks spawn nothing, and completing a task twice creates no duplicates. |

## 📸 Demo Walkthrough

### Main UI features

Run the app with `streamlit run app.py`. From the page a user can:

- **Add pets:** enter a name and species. A summary table shows each pet and how many tasks it has.
- **Add tasks:** pick a pet, then set the title, duration (1-240 min), priority (low / medium / high) and repeat (none / daily / weekly). Optionally tick "Choose a start time"; otherwise the scheduler picks one. If a task mentions one of the pet's allergies or dietary restrictions, a warning appears.
- **Mark a task complete:** a daily or weekly task automatically gets its next occurrence.
- **See conflicts:** a red banner gives the number of overlapping tasks, followed by one yellow warning per clash naming both tasks, the pet(s) and the times. A green message shows when nothing overlaps.
- **Delete a task:** the "Delete a task" panel suggests the next free time slot for the chosen task, so the owner can delete it and re-add it without a clash.
- **Filter and sort:** filter the task table by status and by pet. The table is always sorted by start time, with untimed tasks last.
- **Generate a schedule:** places every pending task into today's 08:00-20:00 window, highest priority first, and lists any task that didn't fit.

### Example workflow

1. Enter an owner name, then add a pet (for example, Perla the dog).
2. Add a task for Perla: "Morning walk", 30 minutes, high priority, repeats daily, starting at 08:00.
3. Add a second task that overlaps it, such as "Vet call" at 08:15. The conflict banner and warning appear straight away.
4. Open "Delete a task", select "Vet call", read the suggested time, delete it and re-add it at that time. The warning turns into "No scheduling conflicts today."
5. Mark "Morning walk" complete. A new "Morning walk" appears for tomorrow at 08:00, and the status filter now shows one done and one pending task.
6. Click "Generate schedule" to see today's plan in time order. If anything didn't fit, a warning says which task and what to try.

### Key Scheduler behaviors shown

- **Sorting:** `sort_by_time` orders tasks chronologically, with untimed tasks last.
- **Filtering:** `filter_tasks` narrows the list by completion status and pet name, case-insensitively.
- **Conflict warnings:** `find_conflicts` flags overlapping pending tasks, for the same pet or different pets, and never treats back-to-back tasks as a clash.
- **Recurrence:** completing a daily or weekly task creates the next occurrence at the same time of day.
- **Auto-scheduling:** `auto_schedule` places tasks by priority, respects fixed start times, stays inside the window and returns whatever doesn't fit.

### Sample CLI output

`python main.py` builds an owner with two pets, completes a daily task and prints the results of each feature. Output will differ by date; this run was on Tuesday, 2026-10-20.

```
Completed 'Morning walk' -> next occurrence starts Wed 2026-10-21 08:00 (today is Tue 2026-10-20)

As added (out of order)
------------------------------------------------------------
18:00  Evening feeding  Perla  [medium] pending
14:05  Afternoon walk   Perla  [medium] pending
08:00  Morning walk     Perla  [high  ] done
08:00  Morning walk     Perla  [high  ] pending
14:15  Vet call         Perla  [medium] pending
09:30  Medication       Mia    [high  ] pending
09:05  Play session     Mia    [low   ] pending
--:--  Grooming         Mia    [low   ] pending
18:00  Flea treatment   Mia    [medium] pending

sort_by_time()
------------------------------------------------------------
08:00  Morning walk     Perla  [high  ] done
08:00  Morning walk     Perla  [high  ] pending
09:05  Play session     Mia    [low   ] pending
09:30  Medication       Mia    [high  ] pending
14:05  Afternoon walk   Perla  [medium] pending
14:15  Vet call         Perla  [medium] pending
18:00  Evening feeding  Perla  [medium] pending
18:00  Flea treatment   Mia    [medium] pending
--:--  Grooming         Mia    [low   ] pending

filter_tasks(completed=True)
------------------------------------------------------------
08:00  Morning walk     Perla  [high  ] done

filter_tasks(completed=False)
------------------------------------------------------------
18:00  Evening feeding  Perla  [medium] pending
14:05  Afternoon walk   Perla  [medium] pending
08:00  Morning walk     Perla  [high  ] pending
14:15  Vet call         Perla  [medium] pending
09:30  Medication       Mia    [high  ] pending
09:05  Play session     Mia    [low   ] pending
--:--  Grooming         Mia    [low   ] pending
18:00  Flea treatment   Mia    [medium] pending

filter_tasks(pet_name='mia')
------------------------------------------------------------
09:30  Medication       Mia    [high  ] pending
09:05  Play session     Mia    [low   ] pending
--:--  Grooming         Mia    [low   ] pending
18:00  Flea treatment   Mia    [medium] pending

Mia's pending tasks, sorted by time
------------------------------------------------------------
09:05  Play session     Mia    [low   ] pending
09:30  Medication       Mia    [high  ] pending
18:00  Flea treatment   Mia    [medium] pending
--:--  Grooming         Mia    [low   ] pending

Conflict check
------------------------------------------------------------
WARNING: conflict (same pet): 'Afternoon walk' (Perla, 14:05-14:35) overlaps 'Vet call' (Perla, 14:15-14:35)
WARNING: conflict (different pets): 'Evening feeding' (Perla, 18:00-18:15) overlaps 'Flea treatment' (Mia, 18:00-18:15)

filter_tasks(pet_name='Rex')  [unknown pet]
------------------------------------------------------------
(none)
```
