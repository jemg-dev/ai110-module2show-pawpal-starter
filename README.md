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

Describe your app in numbered steps so a reader can follow along without watching a video:

    As of the end of Phase 2, I've implemented the core logic of the pawpal system. There are four interacting classes, The Owner, Pet, Task, and Scheduler classes. The Owner, Pet, Scheduler class will each have attributes that hold tasks. However, each of the list of tasks that belong to each respective class may not hold the same values/tasks all the time. An owner my have a much longer list of tasks that spans all his/her pets. A pet of course will only have tasks that are unique to that pet. The scheduler class will have a list of tasks that are scheduled, but it can also call the all the owners' tasks so that it may try to fit them into the schedule for a given date-time frame. The scheduler tries to fit all of the owners' tasks for all the pets into a given date-time frame, by checking if tasks have already been scheduled.

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
