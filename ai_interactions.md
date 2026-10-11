# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**Agent used:** Claude Code (Opus 5) in the terminal, agent mode.

**What task did you give the agent?**

I worked through the project in phases and gave the agent a scoped task at each one rather
than one large instruction:

1. Turn my four identified classes into a Mermaid class diagram.
2. Convert that diagram into Python dataclass skeletons with empty method stubs.
3. Review the skeleton for missing relationships and logic bottlenecks.
4. Implement the method bodies for all four classes.
5. Build a CLI demo script and paste its output into the README.
6. Write two pytest cases for task completion and task addition.
7. Wire the Streamlit UI to the logic layer using `st.session_state`.

**What did the agent do?**

Files created or modified:

| File | What changed |
|------|--------------|
| `diagrams/uml.mmd` | Mermaid class diagram, rewritten twice as the design changed |
| `pawpal_system.py` | All four classes: skeletons first, then full implementations (~330 lines) |
| `main.py` | CLI demo building one owner, two pets, six tasks, exercising every scheduler feature |
| `tests/test_pawpal.py` | Two pytest cases |
| `conftest.py` | Empty file at the project root so tests can import `pawpal_system` |
| `app.py` | Replaced the placeholder UI with forms and controls calling my class methods |
| `README.md` | Sample output, testing section, scheduling feature table, classes table |
| `reflection.md` | Draft prose for sections 1 and 2-5 |
| `requirements.txt` | Added `pytest-cov` |
| `.gitignore` | Added `grading_scheme.md` |

Commands it ran: `python main.py` and `python -m pytest` repeatedly to verify behavior,
`pytest --cov` for the coverage figure, a headless Streamlit `AppTest` harness to confirm
the UI actually creates `Pet` and `Task` objects, and the git commands to commit and push.

The most useful single step was step 3, the review. I asked it to critique my skeleton
rather than extend it, and it found six structural problems. The one that mattered most:
`Owner.get_all_tasks()` returned `list[tuple[Pet, Task]]` while every `Scheduler` method
took `list[Task]`, so the two halves of my design could not be connected. Fixing it meant
adding a `pet_id` field to `Task`. The others were a missing duration and priority on
`Task` (my UI was already collecting both), no date for recurrence to advance, conflict
detection that compared exact timestamps instead of time ranges, and no method that
composed the primitives into a day plan.

**What did you have to verify or fix manually?**

- **The demo hid the feature it was meant to show.** The first version used a 60-minute
  time budget, and every outstanding task happened to fit, so nothing was ever dropped and
  the filtering behavior was invisible in the output. I had it changed to 30 minutes so a
  task is actually cut.
- **I rejected one suggestion outright.** It proposed a `Caretaker` class to replace the
  `assigned_to` string. Reasonable in principle, but nothing here queries a caretaker's
  workload and a class to hold one name is more structure than my problem needs.
- **I overrode its file layout.** It first built the classes as a `pawpal/` package split
  across `models.py` and `scheduler.py`. I asked for everything in a single
  `pawpal_system.py` instead, which meant the package had to be discarded.
- **A safety hook blocked the cleanup.** The agent could not delete the leftover `pawpal/`
  folder -- a pre-commit guard in my environment refused the `git rm` on every attempt --
  so the stale duplicate files reached `main` and had to be cleared by hand outside the
  agent.
- **Test import path.** The tests failed with `ModuleNotFoundError` until a root
  `conftest.py` was added, because pytest puts the *test file's* directory on `sys.path`,
  not the project root.
- **I verified rather than trusted.** I read the demo output against what I expected:
  tasks from both pets merged chronologically, the 08:00-08:45 walk flagged against the
  08:15 feeding, a completed daily task spawning tomorrow's date, and a low-priority
  20-minute task dropped while a medium-priority 15-minute one survived. I also checked
  that invalid input (priority "urgent", duration 0, time "25:00" or "noon") raises a clear
  error.
- **Coverage was weaker than it looked.** The first suite was two passing tests and 49%
  line coverage, with every scheduler method verified only by reading demo output. I had
  the suite expanded to 22 tests covering sorting, both filters, all three conflict cases,
  recurrence for daily, weekly and one-off tasks, and the budget plan, which took coverage
  to 86%. The remaining gap is display formatting and one known bug (a task crossing
  midnight) that I chose to document rather than hide.

### Second agent pass: optional extensions

**What task did you give the agent?**

Four of the five optional extensions, as one brief: a third algorithmic capability, JSON
persistence, priority-first scheduling, and professional output formatting.

**Files modified**

| File | Change |
|------|--------|
| `pawpal_system.py` | `sort_by_priority()`, `next_available_slot()`, `to_dict()` / `from_dict()` on `Task`, `Pet` and `Owner`, `save_to_json()`, `load_from_json()`, and the `CATEGORY_ICONS` / `PRIORITY_ICONS` / `STATUS_ICONS` constants with their accessors |
| `main.py` | `render_table()`, `display_width()`, `paint()`, and three new demo sections: priority ordering, next available slot, and the save/load round trip |
| `app.py` | Glyphs in every table, an Order by toggle, sidebar Save and Load buttons, and a free-slot hint in the add-task form |
| `tests/test_pawpal.py` | Ten more tests, taking the suite from 22 to 32 |
| `README.md` | Data Persistence and Output Formatting sections, priority CLI comparison, refreshed outputs |
| `.gitignore` | `data.json` |

**What did the agent complete?**

All four. The two new algorithms are `sort_by_priority()`, which orders by importance and
falls back to clock time inside a band, and `next_available_slot()`, which sweeps the
07:00-21:00 care day once carrying a cursor through booked time and returns the first gap
wide enough for a task of a given length, or `None` when the day is full. Persistence is
hand-written `to_dict()` / `from_dict()` pairs rather than a library, because the one field
that actually needs handling is `due_date`: JSON has no date type, so it is stored as an ISO
string and parsed back with `date.fromisoformat()`.

**What did you have to verify or fix manually?**

- **The emoji tables came out crooked.** The first version padded columns with `len()`,
  which is wrong twice: an ANSI colour code costs characters but no display columns, and an
  emoji costs one character but two columns. I had it replaced with a `display_width()`
  helper that strips escape codes and consults `unicodedata.east_asian_width()`.
- **One glyph was still misaligned after that fix.** The feeding icon was 🍽️, which is two
  code points (U+1F37D plus a variation selector), so its cells held one more character
  than the single-code-point icons. Terminals handled it; a Markdown code block would not.
  Swapped for 🍖.
- **Colour had to become conditional.** Escape codes are useful in a terminal and garbage
  in a README. I had `paint()` gated on `sys.stdout.isatty()`, so piping `main.py` into a
  file produces clean text.
- **I checked the slot-finding logic against cases rather than trusting it.** With tasks at
  07:00-07:30 and 08:00-08:45, a 30-minute request should return 07:30 and a 45-minute
  request should skip that gap and return 08:45. Both correct. A fully booked day returns
  `None` rather than raising, and a completed task stops blocking the calendar.
- **I questioned one piece of output in the README.** The priority table shows five tasks
  where the time table shows seven, because the demo completes two morning tasks before
  that section runs. That is correct behavior but reads as a bug, so I had the surrounding
  text explain it rather than leaving a reader to wonder.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

**Not attempted.** This project was built with a single assistant (Claude Code), so there
is no second model's output to compare against. The table below is left blank rather than
filled with a guess at what another model would have said.

A good candidate task if this is revisited: the weekly rescheduling logic in
`handle_recurring()` / `next_occurrence()`, specifically what should happen when a weekly
task is completed several days late -- does the next occurrence fall seven days from the
original due date, or seven days from today? PawPal+ currently advances from the stored
`due_date`, which means a task completed late keeps its original weekday. That is a real
design question with defensible answers on both sides, which makes it worth putting to two
models.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
