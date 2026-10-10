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

My scheduler works with four constraints.

**Clock time** is the backbone. Every task carries a start time and a duration, so the
scheduler knows not just when something begins but when it ends. This is what makes
`detect_conflicts()` useful: an 08:00 walk lasting 45 minutes genuinely collides with an
08:15 feeding, and comparing start times alone would have missed it.

**Priority** decides what survives when there is not enough time. Tasks are `low`,
`medium`, or `high`, and `plan_day()` spends the available minutes on the most important
work first.

**Available time** is the constraint that forces real decisions. `plan_day()` takes a
number of minutes and drops whatever no longer fits, which is the only place the system
genuinely says no to something.

**Caretaker assignment** is tracked on `assigned_to`, but the scheduler does not reason
about it yet. It is recorded and displayed, not enforced.

I decided time mattered most because it is the constraint the owner cannot negotiate with:
a day has a fixed number of minutes, and two tasks at once is physically impossible no
matter how the owner feels about either one. Priority came second because it is what you
need the moment time runs short -- without it the system would have to drop tasks
arbitrarily. Preferences like which caretaker does what came last because getting them
wrong is an inconvenience, while getting the time wrong means a pet does not get fed.

**b. Tradeoffs**

The clearest tradeoff is in `plan_day()`: it fills the time budget greedily by priority,
and it does not try to find the combination of tasks that uses the budget most fully.

A concrete case from my own demo output. With 30 minutes available and these outstanding
tasks -- Evening Kibble (high, 10 min), Ear Drops (medium, 5 min), Wand Play (medium, 15
min), Brush Coat (low, 20 min) -- my scheduler keeps the first three, using exactly 30 of
30 minutes. But the ordering is what matters: it took Wand Play because it is medium
priority, and refused Brush Coat because it is low. If Wand Play had been 25 minutes
instead of 15, the plan would have kept Evening Kibble and Ear Drops for 15 minutes total
and left 15 minutes unused, even though Brush Coat would have fit in that gap. A smarter
algorithm would have packed the day more tightly.

I think that is the right tradeoff here. The alternative is a knapsack-style search that
maximizes minutes used, and "minutes used" is the wrong thing to maximize for pet care --
it would happily fill the day with grooming while skipping medication, because a bigger
number is not a better day for the animal. Greedy-by-priority produces a plan the owner
can predict and trust: the thing that got dropped is always the least important thing, and
the owner can see exactly why. Predictability is worth more than efficiency when the
consequence of a bad answer is a pet missing a dose.

It also means the result is reproducible. Sorting breaks ties on priority and then title,
so the same input always produces the same plan, which made the behavior straightforward
to verify by running the demo.

**A second tradeoff, in conflict detection.** My first version only flagged tasks with
*identical* timestamps. That was simpler, but it was wrong once tasks had durations: an
08:00 walk lasting 45 minutes genuinely collides with an 08:15 feeding, and exact matching
reported nothing. I changed it to compare time ranges (`start_a < end_b and start_b <
end_a`), which catches both the identical-time case and the overlap case. The cost is that
"conflict" is now a judgement about the owner's attention rather than a simple equality
check, and tasks that merely touch end-to-start deliberately do not count.

**Readability versus speed, when I reviewed the code.** I asked for a simplification of
`detect_conflicts()` and was offered a one-line comprehension:

```python
return [(a, b) for a, b in combinations(self.sort_by_time(tasks), 2) if a.overlaps(b)]
```

That is shorter and more Pythonic than my explicit nested loop. I measured both on
identical inputs: results matched exactly, but because the comprehension compares every
pair while my loop sorts first and breaks out as soon as a later task starts after the
current one ends, the loop was roughly 14 times faster on 400 tasks (17ms versus 250ms).

I kept my version, and the reason is not the speed. A pet owner will never have 400 tasks,
so at realistic sizes the difference is a fraction of a millisecond and the one-liner would
have been fine. I kept it because the early break is the thing that makes the algorithm
express *why* sorting matters -- once the list is in time order, you can stop looking. The
comprehension hides that and is quietly quadratic. Four extra lines that state the
reasoning are worth more to me than four fewer lines that conceal it.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code in the terminal for most of the build, in roughly four modes.

**Design review.** After writing my class skeletons I asked it to look for missing
relationships and logic bottlenecks rather than asking it to write code. That single
question produced the most valuable output of the project: it found that my
`Owner.get_all_tasks()` returned `list[tuple[Pet, Task]]` while every `Scheduler` method
took `list[Task]`, so the two halves of my design could not actually be connected. I would
have hit that as a confusing bug an hour into implementation.

**Implementation.** I had it write the method bodies from my skeletons, then checked the
behavior myself by running the demo script and reading the output.

**Investigation.** I asked how `st.session_state` works and how a `Scheduler` should pull
tasks from an `Owner`. These were the questions where I wanted to understand a mechanism,
not receive code.

**Documentation.** I had it draft README sections and reflection prose from work that
already existed, then edited for voice.

The most useful prompts were the ones that asked for a critique of something I had already
written, not the ones that asked for new code. "Review this for missing relationships and
bottlenecks" produced six concrete, checkable problems. "Write me a scheduler" would have
produced something I did not understand well enough to defend. The second most useful
pattern was asking *how* something works -- "how should the Scheduler retrieve tasks from
the Owner" -- because the answer taught me a principle I then applied myself, rather than
handing me a line to paste.

What did not work as well was accepting long code generations without running them. Every
time I ran the code and read the actual output, I found something worth changing.

**b. Judgment and verification**

The suggestion I turned down was introducing a `Caretaker` class to replace my
`assigned_to` string field. The reasoning offered was sound in the abstract -- a free
string means "Alex", "alex", and "Alex " become three different people, and you cannot
reliably ask "what is Alex responsible for". But nothing in this project needs to query a
caretaker's workload, and adding a whole class to hold one name is more structure than my
problem has. I kept the string and wrote down why, so the decision is visible rather than
accidental.

I also pushed back on a smaller one: the AI's first time-budget demo used 60 minutes, and
every outstanding task happened to fit, so the output showed nothing being dropped. The
code was correct but the demo proved nothing. I had it lowered to 30 minutes so the
filtering behavior actually appears in the output a grader reads.

For verification I did not rely on the code looking plausible. Three things:

**I ran it and read the output.** The demo script prints a start-and-end window for every
task, which is what let me confirm by eye that the 08:00-08:45 walk and the 08:15 feeding
are flagged as a conflict, and that Brush Coat is the task dropped from a 30-minute budget
while the shorter medium-priority task survives.

**I checked the boundaries deliberately.** I verified that a task set to `once` returns
`None` from `handle_recurring()`, that a task not yet complete also returns `None`, that
`remove_task()` on an id that does not exist returns `False` rather than raising, and that
invalid input -- a priority of "urgent", a duration of 0, a time of "25:00" or "noon" --
raises a clear `ValueError` instead of being silently accepted.

**I wrote tests for the things everything else depends on.** The completion test asserts
the starting state before calling `mark_complete()`, because a test that only checks the
end state would pass against a method that does nothing at all.

One thing I was honest about while building: for a while automated coverage of
`pawpal_system.py` sat at 49%, with the `Scheduler` methods verified only by running the
demo and reading the output. That caught real problems, but it is weaker evidence than a
test suite, so I went back and wrote assertions for every algorithmic method. Coverage is
now 86%.

---

## 4. Testing and Verification

**a. What you tested**

Twenty-two automated tests, all passing. I started with the two the project asked for and
expanded the suite once the scheduler had real algorithms in it.

The two foundational ones came first. `test_mark_complete_changes_status` checks that
`Task.mark_complete()` sets `is_completed` to `True` and `mark_pending()` returns it to
`False`, asserting the starting value first -- which matters more than it looks, because
without that assertion the test would still pass if `is_completed` defaulted to `True` and
the method did nothing. `test_add_task_increases_pet_task_count` checks that
`Pet.add_task()` grows the list from 0 to 1 to 2 and stamps the task with the pet's `id`.

Those two are the foundation everything else stands on. Completion status is what
`filter_by_status()` reads, what `plan_day()` uses to decide what is still outstanding, and
what recurrence gates on -- if that flag is wrong, three features are wrong and all of them
fail quietly rather than loudly. The `pet_id` stamp is the relationship that lets a flat
list of tasks still say which pet each one belongs to.

The rest of the suite covers the algorithms, and I deliberately aimed at the cases where I
thought I might be wrong rather than the cases I was confident about:

- **Sorting**: that `"9:00"` does not sort after `"17:30"`, which is exactly what plain
  string comparison would do. Also that re-sorting an already-sorted list returns it
  unchanged, so a plan is reproducible.
- **Conflict detection**: an overlap across two different pets, two tasks at the identical
  minute, and -- the one I most wanted proof of -- that back-to-back tasks at 08:00-08:30
  and 08:30-09:00 are *not* reported. That is a strict-inequality detail I did not want to
  be holding only in my head.
- **Recurrence**: a daily task advancing exactly one day, a weekly one advancing seven, a
  `once` task spawning nothing, and `handle_recurring()` returning the new task *without*
  attaching it, so a caller looping over `pet.tasks` cannot mutate the list it is walking.
- **Planning**: that a 30-minute budget drops the low-priority task and keeps the
  medium-priority one even though the dropped task comes last in the day. Priority decides,
  not clock position, and a test is the only way to keep that true.
- **Validation**: that a priority of `"urgent"`, a duration of `0`, and times of `"25:00"`
  or `"noon"` are all refused at construction rather than accepted and surfacing later as a
  broken schedule.

Line coverage of `pawpal_system.py` is 86%. What remains uncovered is mostly display
formatting, which I verify by running `main.py` and reading the output.

Beyond the automated tests I checked the Streamlit UI end to end, confirming that adding a
pet in the browser creates a real `Pet` object that survives a page re-run, that completing
a daily task there creates its follow-up by itself, and that a duplicate pet shows a
readable error instead of a traceback.

**b. Confidence**

Moderately confident, and more confident about some parts than others.

I am confident about sorting, conflict detection, and the time-budget plan, because I have
watched them produce correct output on data I built specifically to stress them -- an
overlapping morning, a mix of priorities, and a budget tight enough to force a drop. I am
confident about input validation because I deliberately fed it bad values and watched each
one raise.

I am less confident about recurrence. I have verified one daily task rolling over by one
day, and that is a single case of several that exist.

With more time, the edge cases I would test next, roughly in order:

- **Recurrence across a month or year boundary.** A weekly task completed on 29 December
  should land in January. `timedelta` should handle it, but I have not proved it.
- **A task with no `due_date` at all.** `handle_recurring()` falls back to `date.today()`,
  which means the spawned date depends on when the code runs -- that deserves a test
  pinning the behavior down.
- **Tasks that touch end-to-start.** An 08:00-08:30 task and an 08:30-09:00 task should
  *not* be a conflict. I believe my comparison is correct because it uses strict
  inequalities, but that is exactly the kind of off-by-one that belongs in a test rather
  than in my head.
- **A task crossing midnight.** A 23:30 task lasting 45 minutes ends at 00:15 the next
  day. My `end_minutes()` returns a value past 1440 and `format_minutes()` wraps it, so
  the display is right but overlap logic against an early-morning task would be wrong. I
  think this is a genuine bug I have not fixed.
- **An exactly-full time budget**, and a budget of zero, to confirm nothing is kept by
  accident.
- **Two pets with the same name**, since `find_pet()` returns the first match. I added
  `find_pet_by_id()` for the unambiguous case but the name lookup is still a trap.

The honest summary: the paths I exercised work, and the paths I have not exercised are
where I would expect to find problems. Writing the test suite moved coverage from 49% to
86% and turned most of "I watched it work" into "it is asserted", but the midnight case
above is a real bug that no test currently catches.

---

## 5. Reflection

**a. What went well**

The decision to make `Task` a single generalized class instead of putting
`assign_walker()` and `assign_food()` methods on `Pet`. A walk, a feeding, a dose of
medication, and a vet visit are the same shape -- something that happens at a time, takes a
while, matters a certain amount, and is either done or not. Treating them as one type with
different field values means adding a new kind of care costs nothing: the Streamlit
category dropdown has seven options and not one of them required a code change.

I am also satisfied that the scheduler holds no task data. Keeping it a service over a list
of tasks rather than a store of them meant I could verify its behavior against hand-built
lists without constructing a whole household, and it kept one clear answer to the question
of who owns the data.

**b. What you would improve**

Three things, in the order I would do them.

**Fix the midnight boundary.** This is now the most concrete known bug: a 23:30 task
lasting 45 minutes ends past minute 1440, and overlap comparison against an early-morning
task silently fails. I would write the failing test first, then fix it.

**Replace the `time_str` string with a real `datetime`.** I patched around the string by
parsing it to minutes since midnight and validating it on construction, which fixed the
sorting trap. But the midnight-crossing bug I described above exists because minutes since
midnight has no concept of a day boundary. A `datetime` would remove that whole class of
problem instead of guarding one symptom.

**Make conflict handling do something.** `detect_conflicts()` reports overlaps and stops
there. Since it returns the task pairs rather than text, the next step is a method that
proposes a new time for the lower-priority task in each pair, which is the feature an owner
would actually want.

If there were a fourth, I would add JSON persistence. Everything currently lives in
`st.session_state` and disappears when the browser session ends, which is fine for a demo
and useless for real use.

**c. Key takeaway**

Designing the data first, and only then the behavior, decided how the whole project went
-- and the most valuable thing AI did was catch a flaw in that data design before I built
anything on top of it.

The specific moment: my skeleton had `Owner.get_all_tasks()` returning `list[tuple[Pet,
Task]]` while every `Scheduler` method accepted `list[Task]`. Both looked reasonable in
isolation, and the mismatch only existed in the gap between them. I would not have seen it
by rereading either class, because neither class was wrong. I found it by asking for a
review of the relationships rather than of the code.

The broader lesson about working with AI is that it was most useful as a critic of work I
had already done, and least useful when I let it generate something I had not thought
about myself. The design review found six real problems. The generated code was good but
needed running before I trusted it -- and when I ran it I found that the demo's 60-minute
budget hid the very behavior it was supposed to demonstrate. Code that looks right and code
that is right are different things, and the only way I closed that gap was executing it and
reading the output.

The other half of that lesson is that I had to stay the one making decisions. I turned down
the `Caretaker` class because the structure was not worth the problem it solved, not
because the suggestion was wrong. Being able to say why I rejected something was what made
the design mine.
