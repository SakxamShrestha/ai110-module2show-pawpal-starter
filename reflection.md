# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

Three core actions that a user should be able to perform are: 
- Add a pet to the app
- See his pet daily scheduled tasks 
- Schedule a walk for his pet 

My initial UML design has four classes: `Owner`, `Pet`, `Task`, and `Scheduler`. The data
classes nest from the outside in, and the scheduler sits beside them as a service.

**`Task`** is the unit of care. Every kind of care activity is one `Task`, so a walk, a
feeding, a dose of medication, and a vet visit are all the same type with different field
values. It holds an `id`, `title`, `description`, `category`, `time_str`, `frequency`,
`assigned_to`, and `is_completed`, and it owns only its own state through `mark_complete()`
and `mark_pending()`. This was the decision I thought hardest about. My first instinct was
to put methods like `assign_walker()` and `assign_food()` on `Pet`, but that would mean a
new method on `Pet` for every new kind of care, and `Pet` would end up knowing the rules
for all of them. Treating care activities as parameterized `Task` objects means adding a
category costs nothing in code.

**`Pet`** is the animal receiving care and the owner of its own task list. It holds
identifying info and traits -- `id`, `name`, `species`, `breed`, `age`, `dietary_notes` --
plus `tasks`, and manages that list through `add_task()`, `remove_task()`, and
`get_pending_tasks()`. It is responsible for which tasks belong to it, not for when they
happen.

**`Owner`** is the household and the top-level container. It holds contact info and a list
of `Pet` objects, and exposes `add_pet()`, `find_pet()`, and `get_all_tasks()`.
`get_all_tasks()` is the important one: it returns `(Pet, Task)` pairs rather than bare
tasks, so a cross-pet view can still say which pet each task belongs to. Without the pet
attached, a combined schedule would list "Morning Kibble" twice with no way to tell whose
it is.

**`Scheduler`** is the algorithmic engine, and it deliberately stores no task data of its
own. It receives a list of tasks and returns a result: `sort_by_time()` orders tasks
chronologically, `filter_by_status()` separates done from pending, `detect_conflicts()`
flags tasks booked at the same time, and `handle_recurring()` spawns the next occurrence of
a completed recurring task. Keeping it stateless means there is one place that owns the
data (`Owner` and `Pet`) and a separate place that reasons about it, so I can test the
scheduling rules on a hand-built list of tasks without constructing a whole household.

For relationships, `Owner` composes `Pet` and `Pet` composes `Task`, because a task has no
meaning without the pet it belongs to and deleting a pet should take its tasks with it. The
`Scheduler` only depends on the others -- it reads them as arguments and holds no permanent
link.

**b. Design changes**

Yes. I asked an AI assistant to review my skeleton for missing relationships and logic
bottlenecks, and I accepted six of its findings. All of them were structural problems that
would have surfaced later as wrong output rather than as crashes, which is why I wanted them
fixed before writing any logic.

**1. Added `pet_id` to `Task`.** This was the most important change. My original `Owner`
returned `list[tuple[Pet, Task]]` from `get_all_tasks()`, but every `Scheduler` method took
`list[Task]`, so the two halves of my design could not actually be connected. Stripping the
pets off to call `sort_by_time()` left me with bare tasks and no way to say whose they were,
so a combined schedule would print "Morning Kibble" twice with nothing to distinguish the
entries. Giving `Task` a `pet_id` lets `get_all_tasks()` return a flat `list[Task]` that the
scheduler can consume directly, while `Owner.find_pet_by_id()` recovers the pet for display.
I preferred this over passing pairs everywhere because it keeps the scheduler signatures
simple.

**2. Added `duration_minutes` and `priority` to `Task`.** The project brief lists available
time as a constraint, but with no duration on a task there is no way to measure a plan
against a time budget, so "skip tasks when time runs out" was impossible to implement. The
Streamlit starter UI was already collecting both fields, so my model was behind my UI.

**3. Added `due_date`, plus `start_minutes()`, `end_minutes()`, and `new_id()` to `Task`.**
My `handle_recurring()` was supposed to advance a daily task by one day, but `time_str`
holds only "HH:MM" -- there was no date for a `timedelta` to apply to. I also had no way to
generate an id for the spawned occurrence, even though `id` is required. Separately, sorting
`"HH:MM"` as a string is only correct when every value is zero-padded, so `"9:00"` would
have sorted after `"17:30"` and silently reordered the day; converting to minutes since
midnight removes that trap.

**4. Changed `detect_conflicts()` to compare time ranges instead of exact timestamps, and
to return `list[tuple[Task, Task]]` instead of `list[str]`.** Comparing timestamps for
equality misses the real case: an 08:00 walk lasting an hour genuinely collides with an
08:30 feeding. Once durations existed, exact matching was not merely incomplete, it was
wrong. Returning the task pairs instead of prose also means a future time-blocking feature
can act on a conflict, not just print it; formatting belongs at the display layer.

**5. Added `plan_day()` and `explain_plan()` to `Scheduler`.** I had four useful primitives
and nothing that composed them, so there was no single entry point that produced a daily
plan or justified it -- both of which the brief asks for. `plan_day()` is also what finally
justifies the `owner` reference the class holds; before this, that field was unused, which
contradicted my own description of the scheduler as stateless.

**6. Added `find_pet_by_id()` and documented `find_pet()` as first-match.** Looking a pet up
by name is ambiguous for a household with two cats named Luna, and `Pet` already had an `id`
that the lookup ignored.

I also moved everything into a single `pawpal_system.py` module rather than a package of
separate files, to keep the blueprint readable in one place at this stage.

One suggestion I did not take was introducing a `Caretaker` class to replace the
`assigned_to` string. It would prevent "Alex" and "alex" becoming two different people, but
nothing in this project needs to query a caretaker's full workload, and a whole class to
hold one name is more structure than the problem justifies right now.

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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

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
