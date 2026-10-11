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

**Task compared.** How a weekly recurring task should behave when it is completed late.
PawPal+ adds `timedelta(days=7)` to the stored `due_date`, so I asked both models: if a
weekly task due Monday is not completed until Thursday, should the next occurrence be the
following Monday (seven days from the due date) or the following Thursday (seven days from
completion)? I asked each for the reasoning on both sides, a recommendation, and code.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | Claude Opus 5, via Claude Code in the terminal (agent mode, with access to the repository) | Google Gemini, via the web chat (no access to the repository) |
| **Prompt** | Identical wording for both: the weekly-Monday-completed-Thursday question above, asking for reasoning on both sides, a recommendation, and Python code. | Same prompt. |
| **Response summary** | Recommended anchoring to `due_date` to stop the task drifting through the calendar, and implemented it directly in `pawpal_system.py`. | Framed it as two distinct task types -- *cadence-driven* (weighing, flea treatment: keep the weekday) and *cooldown-driven* (medicated bath: needs a real seven-day gap). Recommended anchoring to `due_date` by default, adding a `strict_cooldown: bool` field for the cooldown case, and advancing the date in whole steps until it lands in the future when a task is badly overdue. |
| **What was useful** | It could read my actual code, so its answer matched my field names, my `next_occurrence()` structure, and my existing id-generation scheme. It also ran the result. | Two things my own code did not have. First, the **overdue catch-up loop** -- `while next_due <= completed_on: next_due += step` -- which is a genuine bug report, not a preference. Second, the cadence-versus-cooldown framing, which named *why* the two answers both feel right: they are correct for different kinds of task. The worked examples with weekday names made the behavior easy to check. |
| **Problems noticed** | Being inside the repository made it agree with the shape of what was already there. It defended anchoring to `due_date` without raising the overdue case at all, which is the weakness of asking a model to review code it just wrote. | Its code is a standalone `Task` class, not mine: no `pet_id`, no id regeneration, no `Pet` to attach the new occurrence to, so it could not be pasted in. `strict_cooldown` deliberately skips the catch-up loop, which is defensible but undocumented in its answer. And it offered `strict_cooldown` as a default-off flag without saying what should happen to the many existing tasks that have no opinion either way. |
| **Decision** | Kept its anchoring choice. | **Adopted the catch-up loop. Declined the `strict_cooldown` flag.** |

**Which approach did you use in your final implementation and why?**

I took Gemini's catch-up loop and rejected its `strict_cooldown` flag.

The catch-up loop fixes a real defect, and I verified it was real before changing anything.
A weekly task due 7 September, completed on 10 October, produced a next occurrence of 14
September -- a task spawned already three weeks overdue. That is not a design preference, it
is wrong, and neither I nor the assistant working inside my repository had noticed it.
`next_occurrence()` now advances in whole weekly steps until the date is in the future,
which also preserves the weekday: the 7 September task was a Monday and the follow-up lands
on Monday 12 October. Three tests cover it, including one asserting the weekday survives.

I declined `strict_cooldown` on scope grounds, the same reasoning I used earlier for the
`Caretaker` class. It is a genuine distinction -- a medicated bath really does need a true
seven-day gap, and repeating it four days early could irritate a dog's skin, which is a
better argument than I expected from a model that could not see my code. But PawPal+ has no
task today that needs it, adding a per-task boolean means every form, table, and
serialization path has to carry a field that is almost always `False`, and a flag with no
current user is a liability. I wrote the reasoning down so the option is visible if a real
need appears.

One process note worth recording: the useful finding came from the model that could *not*
see my code. Claude Code had written `next_occurrence()` and then reviewed it, and reviewing
your own work has the same blind spot whether you are a person or a model. Gemini came to
the question cold and asked what happens in the awkward case. That is the strongest argument
I found for the exercise -- not that one model is better, but that a reviewer with no
investment in the existing answer looks in different places.

**Code change this produced** (`pawpal_system.py`, `next_occurrence()`):

```python
today = completed_on or date.today()
step = timedelta(days=_FREQUENCY_DAYS[task.frequency])
base = task.due_date or today
next_date = base + step
while next_date <= today:        # adopted from the comparison
    next_date += step
```

`completed_on` was added as an injectable parameter at the same time, so the CLI demo can
pin the clock and print identical dates on every run instead of depending on when it is
executed.
