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

Run the CLI demo with:

```bash
python main.py
```

`main.py` builds one owner, two pets, and six tasks, then exercises every scheduler
feature. Output:

```
PawPal+ -- Jordan Vega (jordan@example.com)
-------------------------------------------
  Milo (Beagle), dog, age 4
    diet: grain-free kibble only
    tasks on file: 3
  Luna (Tabby), cat, age 2
    diet: allergic to chicken
    tasks on file: 4

As entered (unsorted)
---------------------
  19:00  Milo: Brush Coat
  08:00  Milo: Park Walk
  17:30  Milo: Evening Kibble
  08:15  Luna: Morning Kibble
  09:00  Luna: Ear Drops
  18:00  Luna: Wand Play
  17:30  Luna: Evening Pouch

Today's Schedule
----------------
  08:00-08:45  Milo  Park Walk        45 min  high   todo (with Jordan)
  08:15-08:25  Luna  Morning Kibble   10 min  high   todo
  09:00-09:05  Luna  Ear Drops         5 min  medium todo (with Alex)
  17:30-17:40  Milo  Evening Kibble   10 min  high   todo
  17:30-17:40  Luna  Evening Pouch    10 min  high   todo
  18:00-18:15  Luna  Wand Play        15 min  medium todo
  19:00-19:20  Milo  Brush Coat       20 min  low    todo

Filtered by pet
---------------
  Milo (3 tasks)
    08:00  Park Walk
    17:30  Evening Kibble
    19:00  Brush Coat
  Luna (4 tasks)
    08:15  Morning Kibble
    09:00  Ear Drops
    17:30  Evening Pouch
    18:00  Wand Play

Scheduling conflicts
--------------------
  WARNING: Milo and Luna both need attention at once -- Park Walk runs 08:00-08:45 but Morning Kibble starts 08:15
  WARNING: Milo and Luna both need attention at once -- Evening Kibble runs 17:30-17:40 but Evening Pouch starts 17:30
  reported as warnings, so the program keeps running

Progress so far
---------------
  completed (2): Park Walk, Morning Kibble
  remaining (5): Brush Coat, Evening Kibble, Ear Drops, Wand Play, Evening Pouch

Plan for a 30-minute budget
---------------------------
  09:00-09:05 Ear Drops (5 min) [medium] -- Alex -- medium priority medication for Luna
  17:30-17:40 Evening Kibble (10 min) [high] -- high priority feeding for Milo; overlaps another task, so one needs moving
  17:30-17:40 Evening Pouch (10 min) [high] -- high priority feeding for Luna; overlaps another task, so one needs moving
  uses 25 of 30 minutes
  dropped, lowest priority first:
    Brush Coat (20 min, low priority)
    Wand Play (15 min, medium priority)

Recurring tasks
---------------
  completed milo-feed-pm, which is a daily task
  follow-up created automatically: milo-evening-kibble-2026-10-11
  due 2026-10-11 at 17:30, not completed
  Milo's task count went 3 -> 4
```

What each section shows:

- **As entered (unsorted)** -- the tasks in insertion order. They are deliberately added
  out of order (Milo's 19:00 grooming first), so the next section proves the sorting is
  real rather than an accident of how they were entered.
- **Today's Schedule** -- `Scheduler.sort_by_time()` merging both pets' tasks into one
  chronological list.
- **Filtered by pet** -- `Scheduler.filter_by_pet()` pulling one pet's tasks back out of
  the combined list.
- **Scheduling conflicts** -- `Scheduler.conflict_warnings()` reporting two kinds of clash:
  an overlap (Milo's walk runs to 08:45 while Luna's feeding starts 08:15) and an identical
  start time (both pets' evening feeds at 17:30). Returned as warning strings, so the
  program keeps running.
- **Progress so far** -- `Scheduler.filter_by_status()` splitting done from outstanding.
- **Plan for a 30-minute budget** -- `Scheduler.plan_day()` keeping the most important
  work that fits the time available, with `explain_plan()` giving the reason per line and
  `dropped_from_plan()` naming what was cut.
- **Recurring tasks** -- `Owner.complete_task()` completing a daily task and creating its
  follow-up automatically; Milo's task count goes from 3 to 4 without the caller asking
  for a new task.

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# Run with coverage of the logic layer:
python -m pytest --cov=pawpal_system --cov-report=term-missing
```

Tests live in `tests/test_pawpal.py`. A `conftest.py` at the project root puts the
project directory on `sys.path`, which is what lets the tests `import pawpal_system`.

### What the tests cover

22 tests, grouped by the behavior they pin down:

| Group | Tests | What is verified |
|-------|-------|------------------|
| Task state | 4 | `mark_complete()` sets `is_completed` and `mark_pending()` clears it, asserting the starting value first so the test cannot pass against a method that does nothing. `add_task()` grows the list 0 to 1 to 2 and stamps the pet's `id`. `remove_task()` returns `False` for an absent id rather than raising. Invalid input -- priority `"urgent"`, duration `0`, time `"25:00"` or `"noon"` -- is refused at construction. |
| Sorting correctness | 2 | Tasks come back in chronological order, including the case that `"9:00"` must not sort after `"17:30"` the way plain string comparison would. Ties at the same minute order the higher priority first, and re-sorting an already-sorted list returns it unchanged, so a plan is reproducible. |
| Filtering | 2 | `filter_by_status()` returns exactly the done or outstanding set. `filter_by_pet()` resolves a pet name to its id, keeps only that pet's tasks out of the combined household list, and ignores case. |
| Conflict detection | 4 | An 08:00 walk lasting 45 minutes is flagged against an 08:15 feeding for a different pet. Two tasks at the identical 17:30 are flagged. Back-to-back tasks (08:00-08:30 then 08:30-09:00) are *not* flagged. `conflict_warnings()` returns readable strings and raises nothing. |
| Recurrence | 4 | Completing a `daily` task attaches an occurrence due one day later, not completed, with a new id, leaving exactly one pending task. A `weekly` task advances seven days. A `once` task is completed and spawns nothing. `handle_recurring()` returns the new task *without* attaching it, so a loop over `pet.tasks` is never mutated mid-iteration. |
| Planning | 3 | A 30-minute budget keeps the high and medium tasks and drops the low-priority one, even though the dropped task is last in the day -- priority decides, not clock position. With no budget every pending task is returned in clock order, completed ones excluded. A scheduler with no owner raises a clear message. |

### Sample test output

```
============================= test session starts ==============================
platform darwin -- Python 3.12.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/sakxamshrestha/Desktop/ai110-module2show-pawpal-starter
plugins: cov-7.1.0, anyio-4.15.1
collected 22 items

tests/test_pawpal.py ......................                              [100%]

============================== 22 passed in 0.04s ==============================
```

### Coverage

Line coverage of `pawpal_system.py` is **86%** (209 statements, 29 uncovered):

```
Name               Stmts   Miss  Cover
------------------------------------------------
pawpal_system.py     209     29    86%
TOTAL                209     29    86%
```

The uncovered lines are mostly display helpers (`Task.describe()`, `Pet.label()`,
`Scheduler.explain_plan()`), which are exercised by running `main.py` and reading its
output, plus a few defensive branches such as `find_pet()` returning `None`.

### Confidence level

**4 out of 5 stars** -- four, deliberately, not five.

What earns the four: every algorithmic feature has assertions behind it, including the
awkward edges -- unpadded clock times, identical timestamps, back-to-back tasks that must
*not* count as a clash, and a `once` task that must spawn nothing. The suite pins down
behavior I would otherwise only have eyeballed in demo output.

What holds back the fifth star: a task crossing midnight is still wrong. A 23:30 task
lasting 45 minutes ends at minute 1455, and comparing that against an early-morning task
fails because minutes-since-midnight has no concept of a day boundary. I know about it,
there is no test for it yet, and fixing it properly means moving from `"HH:MM"` strings to
real `datetime` values. The Streamlit layer also has no tests in this suite; it was
verified manually through Streamlit's `AppTest` harness during development.

## 📐 Smarter Scheduling

All scheduling logic lives on `Scheduler` in `pawpal_system.py`. It stores no task data
of its own: it receives tasks, usually via `Owner.get_all_tasks()`, and returns a result.
Because the owner flattens tasks from every pet into one list, each feature below operates
across the whole household rather than one pet at a time.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Task.start_minutes()` | Chronological. Times are converted to minutes since midnight rather than compared as text, so `"9:00"` cannot sort after `"17:30"`. Ties break on priority then title, so repeat runs give identical output. |
| Filtering by status | `Scheduler.filter_by_status()`, `Pet.get_pending_tasks()`, `Owner.get_all_pending_tasks()` | Splits done from outstanding. `plan_day()` builds on this to drop work that does not fit the time available. |
| Filtering by pet | `Scheduler.filter_by_pet()` | Pulls one pet's tasks out of the combined household list. Resolves a pet *name* to its id through the owner, and falls back to matching `pet_id` directly so it still works on a hand-built list with no owner attached. |
| Conflict handling | `Scheduler.detect_conflicts()`, `Scheduler.conflict_warnings()`, `Task.overlaps()` | Compares time *ranges*, not start times: an 08:00 walk lasting 45 minutes collides with an 08:15 feeding, and two tasks at the same 17:30 collide too. `detect_conflicts()` returns the task pairs so a caller can act on them; `conflict_warnings()` wraps them as readable strings and never raises, because a clash is the owner's to resolve, not a program error. Tasks that merely touch end-to-start do not count. |
| Recurring tasks | `Pet.complete_task()`, `Owner.complete_task()`, `next_occurrence()`, `Scheduler.handle_recurring()`, `Task.repeats()`, `Task.new_id()` | `daily` advances one day via `timedelta(days=1)`, `weekly` seven, `once` never repeats. Completing a recurring task through `Pet.complete_task()` or `Owner.complete_task()` attaches the follow-up automatically. `Scheduler.handle_recurring()` is the manual form: it returns the new occurrence without attaching it, so a list being iterated is never mutated mid-loop. |
| Time-budgeted planning | `Scheduler.plan_day()`, `dropped_from_plan()` | Spends a fixed number of available minutes on the most important outstanding tasks first, then returns the kept set in clock order. What gets dropped is decided by priority, not by position in the day. |
| Plan explanation | `Scheduler.explain_plan()`, `Task.describe()` | One line per task giving its time window, pet, duration, priority, and why it was scheduled, plus a note when it overlaps another task. |

### Classes

| Class | Responsibility |
|-------|----------------|
| `Task` | One unit of care -- a walk, feeding, medication, vet visit, or grooming -- held as field values rather than as separate subclasses. Owns its own completion status and validates its priority, duration, and clock time on construction. |
| `Pet` | The animal receiving care. Holds identifying details and dietary notes, plus the collection of tasks assigned to it. |
| `Owner` | The household. Holds contact details and the list of pets, and flattens every pet's tasks into one list for the scheduler. |
| `Scheduler` | The algorithmic engine. Holds a reference to the owner but no task data, so the same methods can be tested against a hand-built list of tasks. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
