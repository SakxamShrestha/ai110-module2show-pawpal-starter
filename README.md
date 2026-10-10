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
    tasks on file: 3

Today's Schedule
----------------
  08:00-08:45  Milo  Park Walk        45 min  high   todo (with Jordan)
  08:15-08:25  Luna  Morning Kibble   10 min  high   todo
  09:00-09:05  Luna  Ear Drops         5 min  medium todo (with Alex)
  17:30-17:40  Milo  Evening Kibble   10 min  high   todo
  18:00-18:15  Luna  Wand Play        15 min  medium todo
  19:00-19:20  Milo  Brush Coat       20 min  low    todo

Scheduling conflicts
--------------------
  08:00 Milo's Park Walk runs until 08:45, but Luna's Morning Kibble starts 08:15
  the owner cannot be in two places at once, so one needs moving

Progress so far
---------------
  completed (2): Park Walk, Morning Kibble
  remaining (4): Evening Kibble, Brush Coat, Ear Drops, Wand Play

Plan for a 30-minute budget
---------------------------
  09:00-09:05 Ear Drops (5 min) [medium] -- Alex -- medium priority medication for Luna
  17:30-17:40 Evening Kibble (10 min) [high] -- high priority feeding for Milo
  18:00-18:15 Wand Play (15 min) [medium] -- medium priority enrichment for Luna
  uses 30 of 30 minutes
  dropped, lowest priority first:
    Brush Coat (20 min, low priority)

Recurring tasks
---------------
  Park Walk is daily and was completed on 2026-10-10
  next occurrence: milo-park-walk-2026-10-11 due 2026-10-11 at 08:00
```

What each section shows:

- **Today's Schedule** -- `Scheduler.sort_by_time()` merging both pets' tasks into one
  chronological list.
- **Scheduling conflicts** -- `Scheduler.detect_conflicts()` catching an overlap *across*
  pets: Milo's walk runs to 08:45 while Luna's feeding starts at 08:15.
- **Progress so far** -- `Scheduler.filter_by_status()` splitting done from outstanding.
- **Plan for a 30-minute budget** -- `Scheduler.plan_day()` keeping the most important
  work that fits the time available, with `explain_plan()` giving the reason per line and
  `dropped_from_plan()` naming what was cut.
- **Recurring tasks** -- `Scheduler.handle_recurring()` spawning tomorrow's occurrence of
  a completed daily task.

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage of the logic layer:
pytest --cov=pawpal_system --cov-report=term-missing
```

Tests live in `tests/test_pawpal.py`. A `conftest.py` at the project root puts the
project directory on `sys.path`, which is what lets the tests `import pawpal_system`.

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.12.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/sakxamshrestha/Desktop/ai110-module2show-pawpal-starter
plugins: cov-7.1.0, anyio-4.15.1
collected 2 items

tests/test_pawpal.py ..                                                  [100%]

============================== 2 passed in 0.01s ===============================
```

### Test coverage

Both tests pass. They cover the two state changes the rest of the system depends on:

| Test | Behavior verified |
|------|-------------------|
| `test_mark_complete_changes_status` | `Task.mark_complete()` sets `is_completed` to `True`, and `mark_pending()` returns it to `False`. The test asserts the starting state first, so it cannot pass against a method that does nothing. |
| `test_add_task_increases_pet_task_count` | `Pet.add_task()` grows the pet's task list (0 → 1 → 2) and stamps the task with the pet's own `id`, which is the link the scheduler relies on to attribute a task to a pet. |

Line coverage of `pawpal_system.py` is currently **49%** (176 statements, 90 uncovered):

```
Name               Stmts   Miss  Cover
------------------------------------------------
pawpal_system.py     176     90    49%
TOTAL                176     90    49%
```

Covered: `Task` construction and validation, `mark_complete`, `mark_pending`, and
`Pet.add_task`. Not yet covered by automated tests: the `Scheduler` methods
(`sort_by_time`, `filter_by_status`, `detect_conflicts`, `handle_recurring`,
`plan_day`), which are currently verified by running `main.py` and reading its output
rather than by assertions.

## 📐 Smarter Scheduling

All scheduling logic lives on `Scheduler` in `pawpal_system.py`. It stores no task data
of its own: it receives tasks, usually via `Owner.get_all_tasks()`, and returns a result.
Because the owner flattens tasks from every pet into one list, each feature below operates
across the whole household rather than one pet at a time.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Task.start_minutes()` | Chronological. Times are converted to minutes since midnight rather than compared as text, so `"9:00"` cannot sort after `"17:30"`. Ties break on priority then title, so repeat runs give identical output. |
| Filtering | `Scheduler.filter_by_status()`, `Pet.get_pending_tasks()`, `Owner.get_all_pending_tasks()` | Splits done from outstanding. `plan_day()` builds on this to drop work that does not fit the time available. |
| Conflict handling | `Scheduler.detect_conflicts()`, `Task.overlaps()` | Compares time *ranges*, not start times: an 08:00 walk lasting 45 minutes collides with an 08:15 feeding. Returns the task pairs so a caller can act on them. Tasks that merely touch end-to-start do not count as conflicts. |
| Recurring tasks | `Scheduler.handle_recurring()`, `Task.repeats()`, `Task.new_id()` | `daily` advances one day, `weekly` seven, `once` never repeats. Only fires on a completed task. Returns the new occurrence instead of appending it, so a list being iterated is never mutated mid-loop. |
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
