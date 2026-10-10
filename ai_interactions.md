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
- **Coverage is weaker than it looks.** Two tests pass but line coverage of
  `pawpal_system.py` is 49%, and the scheduler methods are verified by reading demo output
  rather than by assertions. I would rather state that than imply the suite proves more
  than it does.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

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
