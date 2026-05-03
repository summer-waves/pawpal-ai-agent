"""
PawPal+ System - Core Logic Layer
Manages owners, pets, tasks, and scheduling for a pet care app.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """Represents a single pet care activity."""

    description: str            # e.g. "Feed Bella"
    time: str                   # "HH:MM" format, e.g. "08:00"
    duration: int               # duration in minutes, e.g. 30
    priority: str               # "Low", "Medium", or "High"
    frequency: str              # "once", "daily", or "weekly"
    due_date: date = field(default_factory=date.today)
    completed: bool = False

    def mark_complete(self):
        """Mark this task complete and return the next recurrence if applicable."""
        self.completed = True
        if self.frequency == "daily":
            return Task(self.description, self.time, self.duration,
                        self.priority, self.frequency,
                        due_date=self.due_date + timedelta(days=1))
        elif self.frequency == "weekly":
            return Task(self.description, self.time, self.duration,
                        self.priority, self.frequency,
                        due_date=self.due_date + timedelta(weeks=1))
        return None  # "once" tasks don't recur

    def __str__(self):
        status = "✅" if self.completed else "⬜"
        priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(self.priority, "⚪")
        return (f"{status} {priority_emoji} [{self.time}] {self.description} "
                f"({self.duration} min, {self.frequency}) — due {self.due_date}")


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet belonging to an owner."""

    name: str
    species: str                # e.g. "dog", "cat"
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task):
        """Remove a specific task from this pet's task list."""
        if task in self.tasks:
            self.tasks.remove(task)

    def get_pending_tasks(self) -> List[Task]:
        """Return only tasks that have not been completed."""
        return [t for t in self.tasks if not t.completed]

    def __str__(self):
        return f"{self.name} ({self.species}, age {self.age}) — {len(self.tasks)} task(s)"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents a pet owner who manages one or more pets."""

    def __init__(self, name: str, email: str):
        """Initialize an owner with a name, email, and an empty pet list."""
        self.name = name
        self.email = email
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet):
        """Add a pet to this owner's collection."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str):
        """Remove a pet by name."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Find and return a pet by name, or None if not found."""
        for pet in self.pets:
            if pet.name.lower() == pet_name.lower():
                return pet
        return None

    def get_all_tasks(self) -> List[Task]:
        """Return every task across all pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def __str__(self):
        return f"Owner: {self.name} ({self.email}) — {len(self.pets)} pet(s)"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


class Scheduler:
    """The brain of PawPal+. Organizes and analyzes tasks across all pets."""

    def __init__(self, owner: Owner):
        """Initialize the scheduler with a reference to an Owner."""
        self.owner = owner

    def get_todays_tasks(self) -> List[tuple]:
        """Return all tasks due today as (pet_name, task) tuples."""
        today = date.today()
        results = []
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.due_date == today:
                    results.append((pet.name, task))
        return results

    def sort_by_time(self, tasks: List[tuple]) -> List[tuple]:
        """Sort (pet_name, task) tuples chronologically by task time (HH:MM)."""
        return sorted(tasks, key=lambda x: x[1].time)

    def sort_by_priority(self, tasks: List[tuple]) -> List[tuple]:
        """Sort (pet_name, task) tuples by priority (High first), then by time."""
        return sorted(tasks, key=lambda x: (PRIORITY_ORDER.get(x[1].priority, 99), x[1].time))

    def filter_by_pet(self, pet_name: str) -> List[Task]:
        """Return all tasks for a specific pet by name."""
        pet = self.owner.get_pet(pet_name)
        return pet.tasks if pet else []

    def filter_by_status(self, completed: bool) -> List[tuple]:
        """Return (pet_name, task) tuples filtered by completion status."""
        results = []
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.completed == completed:
                    results.append((pet.name, task))
        return results

    def mark_task_complete(self, pet_name: str, task: Task):
        """Mark a task complete and schedule the next recurrence if applicable."""
        next_task = task.mark_complete()
        if next_task:
            pet = self.owner.get_pet(pet_name)
            if pet:
                pet.add_task(next_task)

    def detect_conflicts(self) -> List[str]:
        """
        Check for tasks scheduled at the same time for the same pet.
        Returns a list of human-readable warning strings.
        """
        warnings = []
        for pet in self.owner.pets:
            seen_times = {}
            for task in pet.tasks:
                if task.time in seen_times:
                    warnings.append(
                        f"⚠️ Conflict for {pet.name}: '{seen_times[task.time]}' "
                        f"and '{task.description}' are both at {task.time}"
                    )
                else:
                    seen_times[task.time] = task.description
        return warnings

    def generate_daily_plan(self) -> str:
        """
        Generate a human-readable explanation of today's schedule,
        sorted by priority then time, with reasoning for the order.
        """
        todays = self.get_todays_tasks()
        if not todays:
            return "No tasks scheduled for today."

        sorted_tasks = self.sort_by_priority(todays)
        lines = ["Here's today's plan, ordered by priority then time:\n"]
        for pet_name, task in sorted_tasks:
            lines.append(f"  🐾 {pet_name}: {task}")
        return "\n".join(lines)

    def print_schedule(self):
        """Print today's full schedule to the terminal in a readable format."""
        print(f"\n{'='*50}")
        print(f"  📅 Today's Schedule for {self.owner.name}")
        print(f"{'='*50}")
        print(self.generate_daily_plan())

        conflicts = self.detect_conflicts()
        if conflicts:
            print()
            for warning in conflicts:
                print(f"  {warning}")

        print(f"{'='*50}\n")
