# PawPal+ 🐾

A pet care planning assistant. PawPal+ keeps track of every care task across a household of
pets -- walks, feedings, medication, grooming, enrichment, vet visits -- orders them into a
single day, warns when two of them collide, and decides what to drop when there is not
enough time for everything.

Built as a Python logic layer with a Streamlit interface on top. The scheduling logic has
no dependency on the UI and can be driven entirely from the command line.

## Features

**Scheduling**

- **Chronological ordering** across every pet at once, not one pet at a time. Clock times
  are converted to minutes since midnight rather than compared as text, so `"9:00"` cannot
  sort after `"17:30"`.
- **Conflict warnings** based on overlapping time *ranges*, not just identical start times:
  an 08:00 walk lasting 45 minutes is flagged against an 08:15 feeding. Reported as
  warnings, never as errors, with a suggestion of which task to move.
- **Time-budgeted day plans.** Give the scheduler the minutes you actually have and it
  keeps the most important outstanding work, dropping the least important. What gets cut is
  decided by priority, not by position in the day.
- **Plan explanations**: one line per scheduled task saying why it is there, plus a note
  when it overlaps something else.
- **Automatic recurrence.** Completing a `daily` or `weekly` task creates its next
  occurrence by itself, with the due date advanced by `timedelta`. The next date is anchored
  to the task's own `due_date`, not to when it was finished, so a weekly Monday task
  completed late on Thursday stays a Monday task. A task finished weeks late advances in
  whole steps until it lands in the future rather than spawning another overdue copy.
- **Filtering** by completion status or by pet name.
- **Priority-first ordering** as an alternative view: `sort_by_priority()` answers "what
  matters most" where `sort_by_time()` answers "what happens next".
- **Next available slot.** Ask where a task of a given length would fit and the scheduler
  sweeps the 07:00-21:00 care day once, returning the earliest free start time across every
  pet, or `None` when nothing is long enough.

**Persistence**

- **JSON save and load.** The household survives between runs in `data.json`. Dates are
  stored as ISO strings and parsed back into real `date` objects, so a reloaded task still
  computes its own recurrence.

**Presentation**

- **Category, priority, and status glyphs** shared by the CLI and the UI.
- **Aligned CLI tables** measured by terminal display width, not string length.
- **ANSI colour when attached to a terminal only**, so piped output stays clean.

**Data handling**

- **One generalized `Task` type.** A walk, a dose of medication, and a feeding differ by
  field values, not by class, so adding a new kind of care needs no new code.
- **Validation at construction.** An impossible priority, a zero duration, or a time like
  `"25:00"` is refused immediately rather than corrupting a schedule later.
- **Readable errors in the UI.** Duplicate pets and invalid task data surface as messages,
  not tracebacks.

## Architecture

| File | Role |
|------|------|
| `pawpal_system.py` | All four classes and every algorithm. No UI imports. |
| `main.py` | CLI demo: builds a household and exercises each feature. |
| `app.py` | Streamlit UI. Calls class methods only; holds no scheduling logic. |
| `tests/test_pawpal.py` | 22 pytest cases over the logic layer. |
| `diagrams/uml_final.mmd` | Mermaid class diagram of the final design. |
| `data.json` | Saved household, written on demand. Generated at runtime, not committed. |

| Class | Responsibility |
|-------|----------------|
| `Task` | One unit of care. Owns its completion status and validates its own fields. |
| `Pet` | The animal receiving care, and the collection of tasks assigned to it. |
| `Owner` | The household. Flattens every pet's tasks into one list for the scheduler. |
| `Scheduler` | The algorithms. Holds a reference to the owner but stores no task data. |

The data nests from the outside in (`Owner` → `Pet` → `Task`) while `Scheduler` sits beside
it as a service. `Task` stores a `pet_id` rather than a `Pet` reference, which is what lets
`Owner.get_all_tasks()` hand the scheduler one flat list that the UI can still resolve back
to a pet name for display. Full diagram: [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd).

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the CLI demo

```bash
python main.py
```

### Run the Streamlit app

```bash
streamlit run app.py
```

### Run the tests

```bash
python -m pytest
```

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
  WHEN         PET   TASK               LENGTH  PRIORITY   REPEATS  DONE  WITH  
  -----------  ----  -----------------  ------  ---------  -------  ----  ------
  08:00-08:45  Milo  🚶 Park Walk       45 min  🔴 high    daily    ⬜    Jordan
  08:15-08:25  Luna  🍖 Morning Kibble  10 min  🔴 high    daily    ⬜    --
  09:00-09:05  Luna  💊 Ear Drops       5 min   🟡 medium  daily    ⬜    Alex
  17:30-17:40  Milo  🍖 Evening Kibble  10 min  🔴 high    daily    ⬜    --
  17:30-17:40  Luna  🍖 Evening Pouch   10 min  🔴 high    daily    ⬜    --
  18:00-18:15  Luna  🧶 Wand Play       15 min  🟡 medium  once     ⬜    --
  19:00-19:20  Milo  🛁 Brush Coat      20 min  🟢 low     weekly   ⬜    --

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

Ordered by priority, then time
------------------------------
  WHEN         PET   TASK               LENGTH  PRIORITY   REPEATS  DONE  WITH
  -----------  ----  -----------------  ------  ---------  -------  ----  ----
  17:30-17:40  Milo  🍖 Evening Kibble  10 min  🔴 high    daily    ⬜    --
  17:30-17:40  Luna  🍖 Evening Pouch   10 min  🔴 high    daily    ⬜    --
  09:00-09:05  Luna  💊 Ear Drops       5 min   🟡 medium  daily    ⬜    Alex
  18:00-18:15  Luna  🧶 Wand Play       15 min  🟡 medium  once     ⬜    --
  19:00-19:20  Milo  🛁 Brush Coat      20 min  🟢 low     weekly   ⬜    --
  high priority first; ties fall back to clock order

Next available slot
-------------------
   15 min: earliest free at 07:00
   30 min: earliest free at 07:00
   90 min: earliest free at 07:00
  240 min: earliest free at 09:05

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
  a weekly task due 2026-09-19 (Saturday) completed three weeks late
  next occurrence skips ahead to 2026-10-17 (Saturday), still a Saturday task and no longer overdue

Saving and loading
------------------
  wrote 2 pets and 10 tasks to data.json
  read back 2 pets and 10 tasks
  round trip identical: True
  dates survive as dates: Brush Coat due datetime.date(2026, 10, 10) (date)
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

35 tests, grouped by the behavior they pin down:

| Group | Tests | What is verified |
|-------|-------|------------------|
| Task state | 4 | `mark_complete()` sets `is_completed` and `mark_pending()` clears it, asserting the starting value first so the test cannot pass against a method that does nothing. `add_task()` grows the list 0 to 1 to 2 and stamps the pet's `id`. `remove_task()` returns `False` for an absent id rather than raising. Invalid input -- priority `"urgent"`, duration `0`, time `"25:00"` or `"noon"` -- is refused at construction. |
| Sorting correctness | 2 | Tasks come back in chronological order, including the case that `"9:00"` must not sort after `"17:30"` the way plain string comparison would. Ties at the same minute order the higher priority first, and re-sorting an already-sorted list returns it unchanged, so a plan is reproducible. |
| Filtering | 2 | `filter_by_status()` returns exactly the done or outstanding set. `filter_by_pet()` resolves a pet name to its id, keeps only that pet's tasks out of the combined household list, and ignores case. |
| Conflict detection | 4 | An 08:00 walk lasting 45 minutes is flagged against an 08:15 feeding for a different pet. Two tasks at the identical 17:30 are flagged. Back-to-back tasks (08:00-08:30 then 08:30-09:00) are *not* flagged. `conflict_warnings()` returns readable strings and raises nothing. |
| Recurrence | 4 | Completing a `daily` task attaches an occurrence due one day later, not completed, with a new id, leaving exactly one pending task. A `weekly` task advances seven days. A `once` task is completed and spawns nothing. `handle_recurring()` returns the new task *without* attaching it, so a loop over `pet.tasks` is never mutated mid-iteration. |
| Planning | 3 | A 30-minute budget keeps the high and medium tasks and drops the low-priority one, even though the dropped task is last in the day -- priority decides, not clock position. With no budget every pending task is returned in clock order, completed ones excluded. A scheduler with no owner raises a clear message. |
| Priority ordering | 2 | `sort_by_priority()` leads with a high-priority task even when it is last in the day, and falls back to clock order inside one priority band. |
| Next available slot | 5 | A 30-minute request lands in the gap after an 07:00-07:30 task; a 45-minute request skips that gap and lands after the next task; a fully booked day returns `None`; a completed task no longer blocks the calendar; a zero-length request raises. |
| Late completion | 3 | A weekly Monday task completed on Thursday still lands on the following Monday, because recurrence anchors to the due date rather than the completion date. A task finished three weeks late advances to a future date instead of spawning another overdue one, keeping its weekday. A task completed on time advances exactly one interval and no further. |
| Persistence | 3 | A saved household reloads equal to the original, including a `due_date` that survives as a real `date` rather than the string JSON stored. A missing file returns `None` so a first run starts empty. A reloaded task is a real `Task`: its methods still work and completing it still spawns the next occurrence. |

### Sample test output

```
============================= test session starts ==============================
platform darwin -- Python 3.12.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/sakxamshrestha/Desktop/ai110-module2show-pawpal-starter
plugins: cov-7.1.0, anyio-4.15.1
collected 35 items

tests/test_pawpal.py ...................................                 [100%]

============================== 35 passed in 0.03s ==============================
```

### Coverage

Line coverage of `pawpal_system.py` is **88%** (282 statements, 34 uncovered):

```
Name               Stmts   Miss  Cover
------------------------------------------------
pawpal_system.py     282     34    88%
TOTAL                282     34    88%
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
| Recurring tasks | `Pet.complete_task()`, `Owner.complete_task()`, `next_occurrence()`, `Scheduler.handle_recurring()`, `Task.repeats()`, `Task.new_id()` | `daily` advances one day via `timedelta(days=1)`, `weekly` seven, `once` never repeats. The next date is anchored to the stored `due_date` rather than the completion date, so a late finish does not let the task drift through the calendar, and a badly overdue task advances in whole steps until it is in the future. Completing through `Pet.complete_task()` or `Owner.complete_task()` attaches the follow-up automatically; `Scheduler.handle_recurring()` returns it without attaching, so a list being iterated is never mutated mid-loop. An optional `completed_on` argument lets a caller pin the clock, which is how the CLI demo prints stable dates. |
| Time-budgeted planning | `Scheduler.plan_day()`, `dropped_from_plan()` | Spends a fixed number of available minutes on the most important outstanding tasks first, then returns the kept set in clock order. What gets dropped is decided by priority, not by position in the day. |
| Priority-first ordering | `Scheduler.sort_by_priority()` | The mirror of `sort_by_time()`: most important first, clock order inside a band, title last so repeat runs match. Available in the CLI demo and behind the UI's Order by toggle. |
| Next available slot | `Scheduler.next_available_slot()` | Sweeps the 07:00-21:00 care day once in clock order, carrying a cursor through booked time; the first gap wide enough is the answer. Considers every pet, so the slot offered does not collide with another animal's care, and skips completed tasks. Returns `None` rather than raising when the day is full. |
| Plan explanation | `Scheduler.explain_plan()`, `Task.describe()` | One line per task giving its time window, pet, duration, priority, and why it was scheduled, plus a note when it overlaps another task. |

### Classes

| Class | Responsibility |
|-------|----------------|
| `Task` | One unit of care -- a walk, feeding, medication, vet visit, or grooming -- held as field values rather than as separate subclasses. Owns its own completion status and validates its priority, duration, and clock time on construction. |
| `Pet` | The animal receiving care. Holds identifying details and dietary notes, plus the collection of tasks assigned to it. |
| `Owner` | The household. Holds contact details and the list of pets, and flattens every pet's tasks into one list for the scheduler. |
| `Scheduler` | The algorithmic engine. Holds a reference to the owner but no task data, so the same methods can be tested against a hand-built list of tasks. |

### Priority ordering, side by side

The same tasks, ordered two ways. By clock time, which answers "what is next":

```
Today's Schedule
----------------
  WHEN         PET   TASK               LENGTH  PRIORITY   REPEATS  DONE  WITH  
  -----------  ----  -----------------  ------  ---------  -------  ----  ------
  08:00-08:45  Milo  🚶 Park Walk       45 min  🔴 high    daily    ⬜    Jordan
  08:15-08:25  Luna  🍖 Morning Kibble  10 min  🔴 high    daily    ⬜    --
  09:00-09:05  Luna  💊 Ear Drops       5 min   🟡 medium  daily    ⬜    Alex
  17:30-17:40  Milo  🍖 Evening Kibble  10 min  🔴 high    daily    ⬜    --
  17:30-17:40  Luna  🍖 Evening Pouch   10 min  🔴 high    daily    ⬜    --
  18:00-18:15  Luna  🧶 Wand Play       15 min  🟡 medium  once     ⬜    --
  19:00-19:20  Milo  🛁 Brush Coat      20 min  🟢 low     weekly   ⬜    --
```

By priority, which answers "what matters most" -- the 17:30 high-priority feeds now lead,
and the 09:00 medication drops below them:

```
Ordered by priority, then time
------------------------------
  WHEN         PET   TASK               LENGTH  PRIORITY   REPEATS  DONE  WITH
  -----------  ----  -----------------  ------  ---------  -------  ----  ----
  17:30-17:40  Milo  🍖 Evening Kibble  10 min  🔴 high    daily    ⬜    --
  17:30-17:40  Luna  🍖 Evening Pouch   10 min  🔴 high    daily    ⬜    --
  09:00-09:05  Luna  💊 Ear Drops       5 min   🟡 medium  daily    ⬜    Alex
  18:00-18:15  Luna  🧶 Wand Play       15 min  🟡 medium  once     ⬜    --
  19:00-19:20  Milo  🛁 Brush Coat      20 min  🟢 low     weekly   ⬜    --
  high priority first; ties fall back to clock order
```

Two things to read carefully here. The priority view lists five tasks, not seven, because
the demo completes the morning walk and feeding before this section runs and the view shows
outstanding work only. And inside one priority band -- the two 17:30 entries -- the tie breaks
on clock time and then title, so the order is stable across runs rather than depending on
which pet happened to be entered first.

### Finding a free slot

```
Next available slot
-------------------
   15 min: earliest free at 07:00
   30 min: earliest free at 07:00
   90 min: earliest free at 07:00
  240 min: earliest free at 09:05
```

The 07:00-08:00 window is free, so anything up to 60 minutes starts at 07:00. A 240-minute
request cannot use it and is offered 09:05 instead, the first point after the morning's
booked tasks.

## 💾 Data Persistence

PawPal+ remembers pets and tasks between runs by writing them to `data.json`.

### Workflow

1. **Save.** `Owner.save_to_json(path="data.json")` converts the household to plain
   dictionaries and writes them with `json.dump`. It returns the path it wrote.
2. **Load.** `Owner.load_from_json(path="data.json")` reads the file and rebuilds real
   `Owner`, `Pet`, and `Task` objects. It returns `None` when the file does not exist, so
   a first run starts empty instead of crashing. A file that exists but is corrupt raises,
   because silently discarding saved pets would be worse than failing loudly.
3. **In the app.** The sidebar has *Save* and *Load* buttons. Save is disabled until there
   is at least one pet.
4. **In the CLI.** `python main.py` ends with a "Saving and loading" section that writes
   the demo household, reads it back, and confirms the round trip.

### How the conversion works

No serialization library. Each class has a matching pair of methods:

| Class | Methods |
|-------|---------|
| `Task` | `to_dict()` / `from_dict()` |
| `Pet` | `to_dict()` / `from_dict()` -- recurses into its tasks |
| `Owner` | `to_dict()` / `from_dict()` -- recurses into its pets |

`Task.to_dict()` starts from `dataclasses.asdict()` and then overwrites one field, because
`due_date` is a `datetime.date` and JSON has no date type:

```python
data["due_date"] = self.due_date.isoformat() if self.due_date else None
```

`from_dict()` reverses it with `date.fromisoformat()`. That one field is the whole reason a
hand-written pair of methods beats a generic dump: a reloaded task has to be a real `Task`
with a real `date`, or `handle_recurring()` cannot add a day to it. The test
`test_saved_task_keeps_working_after_a_reload` asserts exactly that -- it reloads a task and
completes it, checking the follow-up lands on the right date.

### Files modified for persistence

| File | Change |
|------|--------|
| `pawpal_system.py` | `to_dict()` / `from_dict()` on all three data classes, `Owner.save_to_json()`, `Owner.load_from_json()`, `DATA_FILE` constant |
| `app.py` | Save and Load buttons in the sidebar |
| `main.py` | `print_persistence()` demonstrating the round trip |
| `tests/test_pawpal.py` | Three persistence tests |
| `.gitignore` | `data.json` ignored, since it is runtime data |

## 🎨 Output Formatting

Shared glyphs, defined once in `pawpal_system.py` and used by both the CLI and the UI:

| Constant | Used for | Accessor |
|----------|----------|----------|
| `CATEGORY_ICONS` | 🚶 walk, 🍖 feeding, 💊 medication, 🛁 grooming, 🧶 enrichment, 🩺 vet, 📌 other | `Task.icon()` |
| `PRIORITY_ICONS` | 🔴 high, 🟡 medium, 🟢 low | `Task.priority_icon()` |
| `STATUS_ICONS` | ✅ done, ⬜ outstanding | `Task.status_icon()` |

### CLI formatting

`main.py` builds its own tables rather than taking a dependency on `tabulate`, which keeps
the install to two packages. Three functions do the work:

- `render_table(headers, rows)` measures each column from its widest cell and prints an
  aligned table with a dim rule under the header.
- `display_width(text)` is why the tables actually line up. `len()` is the wrong measure
  twice over: an ANSI colour code costs characters but no columns, and an emoji costs one
  character but two columns. This strips the escape codes with a regex and consults
  `unicodedata.east_asian_width()` for every character, skipping combining marks and
  variation selectors.
- `paint(text, code)` applies ANSI colour, but only when `sys.stdout.isatty()` is true.
  Piping the demo into a file -- which is how the output above was captured -- produces clean
  text with no escape codes in it.

One detail worth recording: the feeding glyph was originally 🍽️, which is two code points
(U+1F37D plus a variation selector). Terminals align it correctly but a Markdown code block
may not, so it was swapped for 🍖, a single code point. Every row then holds the same number
of characters per emoji column and the table reads straight in both places.

### UI formatting

`app.py` uses `st.table` for the schedule, the per-pet view, and the generated plan;
`st.metric` for the three counters; `st.success` for a clear day; `st.warning` for conflicts
and dropped tasks; and `st.toast` when completing a recurring task creates its follow-up.
Conflict warnings name which of the two tasks to move rather than only reporting the clash.

## 📸 Demo Walkthrough

### What the interface offers

Launch with `streamlit run app.py`.

- **Sidebar -- owner profile.** Name, email, and phone, plus a running count of pets and
  tasks. A *Load sample household* button fills the app with two pets and seven tasks so
  the scheduling features can be seen immediately, and *Clear everything* empties it again.
- **Pets.** A form taking name, species, breed, age, and dietary notes. Each registered pet
  is listed with its task count and how many are still outstanding.
- **Add a task.** Pick the pet, then set a title, category, start time, duration, priority,
  frequency, and who is responsible.
- **Today's Schedule.** Three counters (tasks today, outstanding, done) above a table of
  every task in clock order. A collapsible panel underneath holds a checkbox to complete
  each task and a ✕ to remove it.
- **Filter by pet.** A dropdown narrowing the table to one pet.
- **Scheduling conflicts.** Yellow warnings naming both clashing tasks and suggesting which
  one to move. A green confirmation appears when there are none.
- **Build a plan.** A slider for the minutes available and a button that produces the plan
  as a table, the reasoning line by line, and a warning listing anything that had to be
  dropped.

### An example workflow

1. Open the app and enter your name in the sidebar.
2. Add a pet: `Milo`, dog, Beagle, age 4, "grain-free kibble only". Add a second: `Luna`,
   cat, Tabby, age 2, "allergic to chicken".
3. Add a task for Milo: *Park Walk*, category `walk`, 08:00, 45 minutes, high priority,
   daily, assigned to Jordan.
4. Add a task for Luna: *Morning Kibble*, category `feeding`, 08:15, 10 minutes, high
   priority, daily.
5. Look at **Today's Schedule**. Both pets' tasks appear in one table, ordered by time --
   even though they were entered pet by pet.
6. A **conflict warning** appears straight away: Milo's walk runs to 08:45 but Luna's
   feeding starts at 08:15, and the owner cannot do both. The warning names the task to
   move.
7. Add a few more tasks across the day, then set the **slider** to 30 minutes and press
   *Generate plan*. The scheduler keeps the most important outstanding tasks that fit and
   warns about what it dropped.
8. Tick the checkbox beside *Park Walk*. Because it is a daily task, a toast confirms that
   tomorrow's occurrence has been created, and the task count rises by one.
9. Use **Filter by pet** to check one animal's day on its own.

### Scheduler behavior this demonstrates

| Behavior | Where you see it |
|----------|------------------|
| Sorting across pets | Today's Schedule table, ordered by time regardless of entry order |
| Conflict detection | The 08:00/08:15 overlap, and two tasks sharing a 17:30 start |
| Status filtering | The outstanding/done counters, and the plan ignoring completed tasks |
| Filtering by pet | The Filter by pet dropdown |
| Time-budgeted planning | Generate plan, with the dropped-tasks warning |
| Plan explanation | The "Why these tasks" list under the plan |
| Automatic recurrence | Completing a daily task, and the follow-up toast |

### Sample CLI output

The same logic, driven from the terminal with `python main.py`:

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

**Screenshots** *(optional)*: <!-- Add screenshots here for human reviewers if you like -->
