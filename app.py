"""PawPal+ Streamlit UI.

Thin presentation layer over pawpal_system.py. Every button and form here calls
a method on Owner, Pet, Task, or Scheduler -- no scheduling logic lives in this
file.
"""

from datetime import date, time

import streamlit as st

from main import build_household
from pawpal_system import (
    DATA_FILE,
    PRIORITIES,
    Owner,
    Pet,
    Scheduler,
    Task,
    format_minutes,
)

CATEGORIES = ("walk", "feeding", "medication", "grooming", "enrichment", "vet", "other")
FREQUENCIES = ("once", "daily", "weekly")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")


def slugify(text: str) -> str:
    """Turn a display name into an id, e.g. "Mr Milo" -> "mr-milo"."""
    return "-".join(text.lower().split())


def task_rows(scheduler: Scheduler, tasks: list, by_priority: bool = False) -> list:
    """Turn tasks into table rows, ordered by time or by importance."""
    ordered = (
        scheduler.sort_by_priority(tasks) if by_priority else scheduler.sort_by_time(tasks)
    )
    return [
        {
            "Time": f"{task.time_str}-{format_minutes(task.end_minutes())}",
            "Pet": scheduler.pet_name_for(task),
            "Task": f"{task.icon()} {task.title}",
            "Minutes": task.duration_minutes,
            "Priority": f"{task.priority_icon()} {task.priority}",
            "Repeats": task.frequency,
            "With": task.assigned_to or "--",
            "Done": task.status_icon(),
        }
        for task in ordered
    ]


def get_owner() -> Owner:
    """Return the Owner held in session state, creating it on first run.

    Streamlit re-runs this script top to bottom on every interaction, so a
    plain `Owner(...)` here would be rebuilt empty each time. Stashing the
    instance in st.session_state -- which behaves like a dictionary that
    survives re-runs -- is what makes added pets and tasks persist.
    """
    if "owner" not in st.session_state:
        st.session_state.owner = Owner(name="")
    return st.session_state.owner


owner = get_owner()

# The Scheduler stores no data of its own, so rebuilding it each run is free and
# guarantees it always points at the current Owner.
scheduler = Scheduler(owner=owner)

st.title("🐾 PawPal+")
st.caption("Plan care tasks across every pet in the household.")

# --------------------------------------------------------------------------
# Owner profile
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("Owner")
    owner.name = st.text_input("Name", value=owner.name, placeholder="Jordan Vega")
    owner.email = st.text_input("Email", value=owner.email)
    owner.phone = st.text_input("Phone", value=owner.phone)

    st.divider()
    st.caption(f"{len(owner.pets)} pets, {len(owner.get_all_tasks())} tasks on file")

    if not owner.pets and st.button("Load sample household"):
        sample, _ = build_household()
        st.session_state.owner = sample
        st.rerun()

    if owner.pets and st.button("Clear everything"):
        st.session_state.owner = Owner(name=owner.name, email=owner.email)
        st.rerun()

    st.divider()
    st.subheader("Saved data")
    st.caption(f"Stored in `{DATA_FILE}` beside the app.")

    save_col, load_col = st.columns(2)
    if save_col.button("Save", use_container_width=True, disabled=not owner.pets):
        path = owner.save_to_json()
        st.success(f"Saved to {path}.")

    if load_col.button("Load", use_container_width=True):
        restored = Owner.load_from_json()
        if restored is None:
            st.warning(f"No {DATA_FILE} yet. Save first.")
        else:
            st.session_state.owner = restored
            st.rerun()

# --------------------------------------------------------------------------
# Add a pet
# --------------------------------------------------------------------------
st.subheader("Pets")

with st.form("add_pet", clear_on_submit=True):
    name_col, species_col, breed_col = st.columns(3)
    pet_name = name_col.text_input("Pet name", placeholder="Milo")
    pet_species = species_col.selectbox("Species", ("dog", "cat", "rabbit", "other"))
    pet_breed = breed_col.text_input("Breed", placeholder="Beagle")

    age_col, diet_col = st.columns([1, 3])
    pet_age = age_col.number_input("Age (years)", min_value=0, max_value=30, value=1)
    pet_diet = diet_col.text_input("Dietary notes", placeholder="grain-free kibble only")

    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("A pet needs a name.")
        else:
            new_pet = Pet(
                id=slugify(pet_name),
                name=pet_name.strip(),
                species=pet_species,
                breed=pet_breed.strip(),
                age=int(pet_age),
                dietary_notes=pet_diet.strip(),
            )
            try:
                # Owner.add_pet owns the registration rules, including the
                # duplicate-id guard, so the UI just reports what it raises.
                owner.add_pet(new_pet)
            except ValueError as error:
                st.error(str(error))
            else:
                st.success(f"Added {new_pet.label()}.")
                st.rerun()

if not owner.pets:
    st.info("No pets yet. Add one above, or load the sample household from the sidebar.")
    st.stop()

for pet in owner.pets:
    pending = len(pet.get_pending_tasks())
    st.markdown(
        f"**{pet.label()}** -- {pet.species}, age {pet.age} -- "
        f"{len(pet.tasks)} tasks, {pending} outstanding"
    )
    if pet.dietary_notes:
        st.caption(f"Diet: {pet.dietary_notes}")

# --------------------------------------------------------------------------
# Add a task
# --------------------------------------------------------------------------
st.subheader("Add a task")

with st.form("add_task", clear_on_submit=True):
    pet_names = [pet.name for pet in owner.pets]
    target_name = st.selectbox("For which pet?", pet_names)

    title_col, category_col = st.columns(2)
    task_title = title_col.text_input("Task title", placeholder="Park Walk")
    task_category = category_col.selectbox("Category", CATEGORIES)

    suggestion = scheduler.next_available_slot(30)
    if suggestion:
        st.caption(
            f"Earliest 30-minute gap in today's 07:00-21:00 care day: **{suggestion}**"
        )

    time_col, duration_col, priority_col = st.columns(3)
    task_time = time_col.time_input("Start time", value=time(8, 0))
    task_duration = duration_col.number_input(
        "Duration (minutes)", min_value=1, max_value=240, value=20
    )
    task_priority = priority_col.selectbox(
        "Priority", PRIORITIES, index=PRIORITIES.index("medium")
    )

    frequency_col, assignee_col = st.columns(2)
    task_frequency = frequency_col.selectbox("Frequency", FREQUENCIES)
    task_assignee = assignee_col.text_input("Assigned to", placeholder="Jordan")

    if st.form_submit_button("Add task"):
        target_pet = owner.find_pet(target_name)
        if not task_title.strip():
            st.error("A task needs a title.")
        elif target_pet is None:
            st.error(f"No pet named {target_name}.")
        else:
            when = task_time.strftime("%H:%M")
            try:
                new_task = Task(
                    id=Task.new_id(target_pet.id, task_title, when),
                    pet_id=target_pet.id,
                    title=task_title.strip(),
                    category=task_category,
                    time_str=when,
                    duration_minutes=int(task_duration),
                    priority=task_priority,
                    frequency=task_frequency,
                    due_date=date.today(),
                    assigned_to=task_assignee.strip() or None,
                )
                # Pet.add_task appends and stamps the task with this pet's id.
                target_pet.add_task(new_task)
            except ValueError as error:
                st.error(str(error))
            else:
                st.success(f"Added {new_task.title} for {target_pet.name}.")
                st.rerun()

# --------------------------------------------------------------------------
# Today's schedule
# --------------------------------------------------------------------------
st.subheader("Today's Schedule")

all_tasks = owner.get_all_tasks()
if not all_tasks:
    st.info("No tasks yet. Add one above.")
    st.stop()

pending_count = len(owner.get_all_pending_tasks())
done_count = len(all_tasks) - pending_count
summary = st.columns(3)
summary[0].metric("Tasks today", len(all_tasks))
summary[1].metric("Outstanding", pending_count)
summary[2].metric("Done", done_count)

order = st.radio(
    "Order by",
    ("Time", "Priority"),
    horizontal=True,
    help="Time uses Scheduler.sort_by_time(); Priority uses sort_by_priority().",
)
st.table(task_rows(scheduler, all_tasks, by_priority=order == "Priority"))

if done_count == len(all_tasks):
    st.success("Everything on today's list is done.")

with st.expander("Mark done or remove a task"):
    for task in scheduler.sort_by_time(all_tasks):
        done_col, text_col, remove_col = st.columns([1, 8, 1])

        is_done = done_col.checkbox(
            "done",
            value=task.is_completed,
            key=f"done-{task.id}",
            label_visibility="hidden",
        )
        if is_done != task.is_completed:
            if is_done:
                # Owner.complete_task marks it done and, for a daily or weekly
                # task, attaches the next occurrence by itself.
                follow_up = owner.complete_task(task.id)
                if follow_up is not None:
                    st.toast(
                        f"Next {follow_up.title} scheduled for {follow_up.due_date}."
                    )
            else:
                task.mark_pending()
            st.rerun()

        label = (
            f"`{task.time_str}` **{task.title}** -- {scheduler.pet_name_for(task)}, "
            f"{task.duration_minutes} min, {task.priority} priority"
        )
        text_col.markdown(f"~~{label}~~" if task.is_completed else label)

        if remove_col.button("✕", key=f"remove-{task.id}", help="Remove this task"):
            pet = owner.find_pet_by_id(task.pet_id)
            if pet is not None and pet.remove_task(task.id):
                st.rerun()

# --------------------------------------------------------------------------
# One pet at a time
# --------------------------------------------------------------------------
with st.expander("Filter by pet"):
    chosen = st.selectbox(
        "Show tasks for", [pet.name for pet in owner.pets], key="filter-pet"
    )
    mine = scheduler.filter_by_pet(all_tasks, chosen)
    st.caption(f"{len(mine)} tasks for {chosen}")
    if mine:
        st.table(task_rows(scheduler, mine))
    else:
        st.info(f"{chosen} has nothing scheduled.")

# --------------------------------------------------------------------------
# Conflicts
# --------------------------------------------------------------------------
conflicts = scheduler.detect_conflicts(all_tasks)
if conflicts:
    st.subheader("Scheduling conflicts")
    st.caption(
        f"{len(conflicts)} clash(es). Nothing is blocked -- these are warnings for you "
        "to resolve."
    )
    for first, second in conflicts:
        # The less important task is the one worth moving, so say which it is
        # rather than leaving the owner to work it out.
        movable = second if second.priority_rank() <= first.priority_rank() else first
        keeper = first if movable is second else second
        st.warning(
            f"**{first.time_str} {first.title}** "
            f"({scheduler.pet_name_for(first)}) runs to "
            f"{format_minutes(first.end_minutes())}, but "
            f"**{second.time_str} {second.title}** "
            f"({scheduler.pet_name_for(second)}) starts then.\n\n"
            f"Suggestion: move *{movable.title}* ({movable.priority} priority) and keep "
            f"*{keeper.title}* ({keeper.priority} priority) where it is."
        )
else:
    st.success("No scheduling conflicts today.")

# --------------------------------------------------------------------------
# Plan the day against a time budget
# --------------------------------------------------------------------------
st.subheader("Build a plan")

budget = st.slider("Minutes of care time available", 10, 300, 60, step=5)
if st.button("Generate plan", type="primary"):
    plan = scheduler.plan_day(minutes_available=budget)
    if not plan:
        st.info("Nothing outstanding fits that budget.")
    else:
        used = sum(task.duration_minutes for task in plan)
        st.success(
            f"{len(plan)} tasks fit, using {used} of {budget} minutes "
            f"({budget - used} spare)."
        )
        st.table(task_rows(scheduler, plan))
        st.markdown("**Why these tasks**")
        for line in scheduler.explain_plan(plan):
            st.markdown(f"- {line}")

    dropped = scheduler.dropped_from_plan(plan)
    if dropped:
        st.warning(
            "Dropped because the time ran out, least important first: "
            + ", ".join(
                f"{task.title} ({task.duration_minutes} min, {task.priority})"
                for task in sorted(dropped, key=lambda t: t.priority_rank())
            )
        )
