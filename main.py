"""
main.py - CLI demo script to verify PawPal+ logic works before connecting the UI.
Run with: python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner = Owner(name="Alex", email="alex@email.com")

dog = Pet(name="Bella", species="Dog", age=3)
cat = Pet(name="Mochi", species="Cat", age=5)

owner.add_pet(dog)
owner.add_pet(cat)

today = date.today()

# --- Add tasks (intentionally out of order to test sorting) ---
dog.add_task(Task("Afternoon walk",  "14:00", 30, "Medium", "daily",  due_date=today))
dog.add_task(Task("Morning feeding", "08:00", 10, "High",   "daily",  due_date=today))
dog.add_task(Task("Vet appointment", "10:00", 60, "High",   "once",   due_date=today))
dog.add_task(Task("Evening walk",    "18:00", 30, "Medium", "daily",  due_date=today))

cat.add_task(Task("Morning feeding", "08:30", 5,  "High",   "daily",  due_date=today))
cat.add_task(Task("Medication",      "08:30", 5,  "High",   "daily",  due_date=today))  # conflict!
cat.add_task(Task("Playtime",        "16:00", 20, "Low",    "weekly", due_date=today))

# --- Run the scheduler ---
scheduler = Scheduler(owner)
scheduler.print_schedule()

# --- Demo: mark a task complete and check recurrence ---
print("Marking Bella's morning feeding as complete...")
morning_feed = dog.tasks[1]
scheduler.mark_task_complete("Bella", morning_feed)
print(f"  Task status: {'✅ Done' if morning_feed.completed else '⬜ Pending'}")
print(f"  Bella now has {len(dog.tasks)} tasks (recurrence added for tomorrow)\n")

# --- Demo: filter pending tasks ---
pending = scheduler.filter_by_status(completed=False)
print(f"Pending tasks across all pets: {len(pending)}")
for pet_name, task in scheduler.sort_by_time(pending):
    print(f"  {pet_name}: {task}")
