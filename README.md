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

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
