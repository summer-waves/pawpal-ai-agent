import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling for busy owners.")

# ---------------------------------------------------------------------------
# Session State — keeps data alive between button clicks
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# Step 1: Owner Setup
# ---------------------------------------------------------------------------

st.header("👤 Owner Setup")

if st.session_state.owner is None:
    with st.form("owner_form"):
        name  = st.text_input("Your name")
        email = st.text_input("Your email")
        submitted = st.form_submit_button("Create Profile")
        if submitted and name and email:
            st.session_state.owner = Owner(name, email)
            st.rerun()
else:
    owner = st.session_state.owner
    st.success(f"Welcome back, **{owner.name}**! ({owner.email})")
    if st.button("Reset / Start Over"):
        st.session_state.owner = None
        st.rerun()

# Stop here if no owner yet
if st.session_state.owner is None:
    st.stop()

owner = st.session_state.owner
scheduler = Scheduler(owner)

# ---------------------------------------------------------------------------
# Step 2: Add a Pet
# ---------------------------------------------------------------------------

st.divider()
st.header("🐶 Add a Pet")

with st.form("pet_form"):
    col1, col2, col3 = st.columns(3)
    pet_name    = col1.text_input("Pet name")
    pet_species = col2.text_input("Species (e.g. Dog, Cat)")
    pet_age     = col3.number_input("Age", min_value=0, max_value=30, value=1)
    add_pet = st.form_submit_button("Add Pet")
    if add_pet and pet_name and pet_species:
        if owner.get_pet(pet_name):
            st.warning(f"A pet named {pet_name} already exists.")
        else:
            owner.add_pet(Pet(pet_name, pet_species, int(pet_age)))
            st.rerun()

if owner.pets:
    st.write("**Your pets:**")
    for pet in owner.pets:
        st.write(f"- {pet}")
else:
    st.info("No pets added yet.")

# ---------------------------------------------------------------------------
# Step 3: Add a Task
# ---------------------------------------------------------------------------

st.divider()
st.header("📋 Add a Task")

if not owner.pets:
    st.info("Add a pet first before scheduling tasks.")
else:
    with st.form("task_form"):
        pet_names   = [p.name for p in owner.pets]
        selected_pet = st.selectbox("Choose a pet", pet_names)

        col1, col2 = st.columns(2)
        task_desc     = col1.text_input("Task description (e.g. Morning walk)")
        task_time     = col2.text_input("Time (HH:MM, e.g. 08:00)")

        col3, col4, col5 = st.columns(3)
        task_duration  = col3.number_input("Duration (min)", min_value=1, max_value=240, value=15)
        task_priority  = col4.selectbox("Priority", ["High", "Medium", "Low"])
        task_frequency = col5.selectbox("Frequency", ["daily", "weekly", "once"])

        task_date = st.date_input("Due date", value=date.today())
        add_task  = st.form_submit_button("Add Task")

        if add_task and task_desc and task_time:
            pet = owner.get_pet(selected_pet)
            pet.add_task(Task(
                description=task_desc,
                time=task_time,
                duration=int(task_duration),
                priority=task_priority,
                frequency=task_frequency,
                due_date=task_date,
            ))
            st.rerun()

# ---------------------------------------------------------------------------
# Step 4: Today's Schedule
# ---------------------------------------------------------------------------

st.divider()
st.header("📅 Today's Schedule")

todays = scheduler.sort_by_priority(scheduler.get_todays_tasks())

if not todays:
    st.info("No tasks scheduled for today. Add some tasks above!")
else:
    # Build a display table
    rows = []
    for pet_name, task in todays:
        rows.append({
            "Pet":         pet_name,
            "Time":        task.time,
            "Task":        task.description,
            "Duration":    f"{task.duration} min",
            "Priority":    task.priority,
            "Frequency":   task.frequency,
            "Done":        "✅" if task.completed else "⬜",
        })
    st.table(rows)

    # Conflict warnings
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            st.warning(warning)
    else:
        st.success("✅ No scheduling conflicts detected.")

# ---------------------------------------------------------------------------
# Step 5: Mark Tasks Complete
# ---------------------------------------------------------------------------

st.divider()
st.header("✅ Mark Tasks Complete")

pending = scheduler.filter_by_status(completed=False)

if not pending:
    st.info("No pending tasks!")
else:
    for pet_name, task in scheduler.sort_by_time(pending):
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{pet_name}** — [{task.time}] {task.description} ({task.priority})")
        if col2.button("Done", key=f"{pet_name}_{task.description}_{task.time}"):
            scheduler.mark_task_complete(pet_name, task)
            st.rerun()

# ---------------------------------------------------------------------------
# Step 6: Filter by Pet
# ---------------------------------------------------------------------------

st.divider()
st.header("🔍 Filter Tasks by Pet")

if owner.pets:
    selected = st.selectbox("Select a pet to view all their tasks", [p.name for p in owner.pets])
    filtered = scheduler.filter_by_pet(selected)
    if filtered:
        for task in filtered:
            st.write(f"- {task}")
    else:
        st.info(f"No tasks for {selected} yet.")