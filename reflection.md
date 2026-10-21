# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
    At a glance there will be at least an Owner class and Pet and Task classes with a one to many relationship 
    where one owner can have many pets and tasks to do. An owner should be able to add pets to his/her profile,
    add/remove tasks per pet, and schedule tasks on a calendar. I also added a Scheduler class as well, however, admittedly this was due to the project spec. However, the Scheduler class should be able to add and remove tasks of course with blocked out time periods.
    
- What classes did you include, and what responsibilities did you assign to each?
    Owner: This class represents the user and will have attributes like username, name, email, and a list of pets. You can create and delete this user account as well as see all tasks, and pets under this user

    Pet: This class represents the pet(s) of an owner. Pets can have an id, name, species, breed, age, restrictions, and tasks associated to that individual pet. Moreover, you can add/remove pets, edit the pet, add/remove tasks for this pet.

    Task: The Task class represents individual tasks. A task can have an id, title, description, duration, priority, category, completion flag, and start/end times. You can create/delete a task, edit it, or mark it as complete. 

    Scheduler: The scheduler class represent a log or a schedule for a day. It has an id, date, start/end times. and tasks associated with it. You can add/remove, see conflicts, and all the task for a given allocation. 


**b. Design changes**

- Did your design change during implementation?
    Yes
- If yes, describe at least one change and why you made it.
    Yes, in the initial UML draft, there was no actual link between an owner and schedules. The UML diagram said that the owner manages the schedule, but there was no attribute in the owner class to see which schedules belonged to the owner. Now the Owner class has an attribute called schedules which is a list of scheduler objects.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
    The scheduler works inside a daily time window (8:00-20:00 in the app). A task must fit entirely inside that window, can't run past midnight, and can't overlap a task already placed. It also honors a fixed start time when the owner gives one, and orders everything else by priority (high, medium, low). Separately, `Pet.check_task_constraints()` warns when a task mentions one of the pet's allergies or dietary restrictions.

- How did you decide which constraints mattered most?
    I put priority first because a missed medication matters more than a missed play session, so high priority tasks get first pick of the day. Fixed start times came next because the owner chose them on purpose. Everything else flows around those two into the earliest free gap. Allergy and diet checks only warn, since the owner knows the pet better than my keyword match does.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
    The scheduler is greedy and warn-only. `auto_schedule()` places tasks one at a time, highest priority first, and a task that has a fixed start time is only ever tried at that exact time. If two tasks overlap (for the same pet or different pets), the higher priority task keeps the slot and the other is reported as "could not fit" instead of being moved to the next free slot. `find_conflicts()` likewise only returns warning messages; it never blocks a task or fixes the clash. It does check real overlaps (start/end ranges), not just identical start times, but it compares every timed task in the day and leaves the resolution to the owner.
    When I asked for a simpler version of `find_conflicts()`, the suggestion was `itertools.combinations(timed, 2)` with a one-line list comprehension that calls `Task.overlaps`. It is shorter, but it compares every pair and the warning formatting gets squeezed into the comprehension. I kept my nested loop: because the tasks are sorted by start time it can `break` as soon as a later task starts after the current one ends, and the loop reads top to bottom.

- Why is that tradeoff reasonable for this scenario?
    A pet owner's day has a handful of tasks, so the greedy approach is fast and its result is easy to explain ("the high priority task got the slot"). A backtracking optimizer would be much more complex for little gain. Warning instead of blocking also keeps the owner in control, since they may know a walk and a feeding can really happen together. The cost is that a lower priority task can get dropped even when moving it 20 minutes would have fit it, so a "move to next free slot" option is the first thing I would add.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)? I used AI in the brainstorming of the UML, the skeleton creation, test cases, and logic implementation of the project thus far. 
    
- What kinds of prompts or questions were most helpful?
    I found that my most context-driven prompts yielded the most helpful responses. For example. When brainstorming for the UML diagram and relationships between all the classes, I prompted Claude Code with what each class had as my rough draft, and if there were any logical pitfalls or unclear relationships. It gave me a clear and consies response with considerations I had not thought of. I was able to push back and go back and forth with the AI to iteratevely improve my UML design and details.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
    The `itertools.combinations` version of `find_conflicts()` described in section 2b. It was shorter, but I kept my sorted nested loop because it can stop early and the warning text stays readable.

- How did you evaluate or verify what the AI suggested?
    I read the code before accepting it, then checked it by running things: the test suite, `pytest --cov` to find lines no test touched, and `main.py` to see the real output. When the coverage report showed untested lines (the edit, remove and allergy methods), I had tests written for them and re-ran everything.

**c. AI strategy**

- Which AI coding assistant features were most effective for building your scheduler?
    Three things helped most. Attaching my actual files (`pawpal_system.py`, `main.py`, the tests) meant the suggestions fit my code instead of generic examples. Letting the assistant run the tests, coverage and `main.py` itself meant every change was checked against real output straight away. And it was good at the tedious parts, like writing a long list of edge-case tests (back-to-back tasks, a task ending exactly at the window end, double completion) that I would have skipped or done sloppily.

- Give one example of an AI suggestion you rejected or modified to keep your system design clean.
    When conflicts showed up in the UI, the assistant offered to add an "edit task" control so the owner could change a start time in place. I turned that down and asked for a simpler flow: delete the task and re-add it at a suggested free time. That reuses `Pet.remove_task` and the existing add form, and the suggested time comes from `find_next_available_slot`, so no new editing state or extra re-check logic was needed. The trade-off is retyping a task, which I accepted to keep the app small.

- How did using separate chat sessions for different phases help you stay organized?
    Keeping design, implementation, tests and UI in separate sessions meant each conversation had one clear goal and a small amount of context, so the assistant stayed focused and I could trace which session produced which decision. The UML draft, the logic, and the README each had their own history, and I brought the current files into each new session instead of relying on memory.

- Summarize what you learned about being the "lead architect" when collaborating with powerful AI tools.
    The AI can produce a lot of code quickly, but it doesn't know which trade-offs I want. My job was to decide the structure (who owns tasks, where scheduling logic lives, warn instead of block) and to say no when a suggestion added complexity I didn't need. I also learned to keep asking for the real output and tests as proof, since confident-sounding code can still hide quirks, like recurrence being based on today's date instead of the original date.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
    Five core behaviors: sorting by time (including zero-padding and untimed tasks last), recurring tasks (daily and weekly, no duplicates, unknown id raises), conflict detection (same pet, different pets, back-to-back not flagged, completed and untimed tasks ignored), auto-scheduling (priority order, fixed start times, window edges, midnight) and filtering. I also covered edit, remove and allergy methods, so all 67 tests give 100% coverage of `pawpal_system.py`.

- Why were these tests important?
    These are the behaviors a pet owner relies on. A wrong sort order, a missed conflict or a task that spawns twice would quietly give the owner a bad plan, and boundary cases like a task ending exactly at 20:00 are where off-by-one mistakes hide.

**b. Confidence**

- How confident are you that your scheduler works correctly?
    About 4 out of 5. The features I listed are tested hard, including edge cases, but 100% coverage only means every line ran, not that every situation was considered.

- What edge cases would you test next if you had more time?
    Recurrence that starts from the task's original date instead of today, tasks that span several days, two pets with the same name (filtering by name would mix them up), daylight saving changes, and the Streamlit page itself, which has no automated tests.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
    The scheduler and its test suite. Sorting, conflict warnings, recurrence and auto-scheduling work together, I can show each one in `main.py` and the app, and the tests back them up.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
    I would add a "move to the next free slot" option so a lower priority task isn't dropped when shifting it 20 minutes would fit, an edit control in the UI, and recurrence that counts from the task's original date. I would also let the owner set the daily window in the app instead of fixing it at 8:00-20:00.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
    Design first, then let the AI help build it. Because the classes, relationships and trade-offs were settled in the UML, I could judge every suggestion against that design and keep the code simple. Tests and real output are what let me trust the AI's work.
