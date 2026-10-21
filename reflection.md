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
- How did you decide which constraints mattered most?

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
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
