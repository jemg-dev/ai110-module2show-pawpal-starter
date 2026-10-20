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
- Why is that tradeoff reasonable for this scenario?

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
