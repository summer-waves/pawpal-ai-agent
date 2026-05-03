"""
tests/test_pawpal.py - Automated test suite for PawPal+ system.
Run with: python -m pytest
"""

import pytest
from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# Fixtures (reusable test setup)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_owner():
    """Create a basic owner with two pets and several tasks."""
    owner = Owner("Test Owner", "test@email.com")
    dog = Pet("Buddy", "Dog", 2)
    cat = Pet("Whiskers", "Cat", 4)

    today = date.today()
    dog.add_task(Task("Evening walk",    "18:00", 30, "Medium", "daily",  due_date=today))
    dog.add_task(Task("Morning feeding", "08:00", 10, "High",   "daily",  due_date=today))
    dog.add_task(Task("Vet visit",       "10:00", 60, "High",   "once",   due_date=today))

    cat.add_task(Task("Feeding",    "08:30", 5,  "High",   "daily",  due_date=today))
    cat.add_task(Task("Medication", "08:30", 5,  "Medium", "daily",  due_date=today))  # conflict

    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status(sample_owner):
    """Marking a task complete should set completed = True."""
    task = sample_owner.pets[0].tasks[0]
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_count(sample_owner):
    """Adding a task to a pet should increase its task count by 1."""
    dog = sample_owner.pets[0]
    initial_count = len(dog.tasks)
    new_task = Task("Bath time", "11:00", 20, "Low", "once", due_date=date.today())
    dog.add_task(new_task)
    assert len(dog.tasks) == initial_count + 1


# ---------------------------------------------------------------------------
# Sorting tests
# ---------------------------------------------------------------------------

def test_sort_by_time_is_chronological(sample_owner):
    """Tasks sorted by time should be in HH:MM ascending order."""
    scheduler = Scheduler(sample_owner)
    todays = scheduler.get_todays_tasks()
    sorted_tasks = scheduler.sort_by_time(todays)
    times = [task.time for _, task in sorted_tasks]
    assert times == sorted(times)


def test_sort_by_priority_high_first(sample_owner):
    """High priority tasks should appear before Medium and Low."""
    scheduler = Scheduler(sample_owner)
    todays = scheduler.get_todays_tasks()
    sorted_tasks = scheduler.sort_by_priority(todays)
    priorities = [task.priority for _, task in sorted_tasks]
    order = {"High": 0, "Medium": 1, "Low": 2}
    assert priorities == sorted(priorities, key=lambda p: order[p])


# ---------------------------------------------------------------------------
# Recurrence tests
# ---------------------------------------------------------------------------

def test_daily_task_recurs_next_day(sample_owner):
    """Completing a daily task should produce a new task due tomorrow."""
    scheduler = Scheduler(sample_owner)
    dog = sample_owner.pets[0]
    daily_task = next(t for t in dog.tasks if t.frequency == "daily")
    original_count = len(dog.tasks)
    scheduler.mark_task_complete("Buddy", daily_task)
    assert len(dog.tasks) == original_count + 1
    new_task = dog.tasks[-1]
    assert new_task.due_date == daily_task.due_date + timedelta(days=1)
    assert new_task.completed is False


def test_once_task_does_not_recur(sample_owner):
    """Completing a 'once' task should NOT add a new task."""
    scheduler = Scheduler(sample_owner)
    dog = sample_owner.pets[0]
    once_task = next(t for t in dog.tasks if t.frequency == "once")
    original_count = len(dog.tasks)
    scheduler.mark_task_complete("Buddy", once_task)
    assert len(dog.tasks) == original_count  # no new task added


# ---------------------------------------------------------------------------
# Conflict detection tests
# ---------------------------------------------------------------------------

def test_conflict_detected_for_same_time(sample_owner):
    """Two tasks at the same time for the same pet should trigger a warning."""
    scheduler = Scheduler(sample_owner)
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) > 0
    assert "Whiskers" in conflicts[0]


def test_no_conflict_when_times_differ(sample_owner):
    """Pets with no overlapping task times should produce zero conflicts."""
    owner = Owner("Clean Owner", "clean@email.com")
    pet = Pet("Goldie", "Fish", 1)
    today = date.today()
    pet.add_task(Task("Feed", "08:00", 5, "High", "daily", due_date=today))
    pet.add_task(Task("Clean tank", "12:00", 20, "Medium", "weekly", due_date=today))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    assert scheduler.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------

def test_schedule_empty_when_no_pets():
    """An owner with no pets should have an empty schedule."""
    owner = Owner("Empty Owner", "empty@email.com")
    scheduler = Scheduler(owner)
    assert scheduler.get_todays_tasks() == []


def test_filter_by_pet_returns_correct_tasks(sample_owner):
    """Filtering by pet name should only return that pet's tasks."""
    scheduler = Scheduler(sample_owner)
    buddy_tasks = scheduler.filter_by_pet("Buddy")
    assert all(isinstance(t, Task) for t in buddy_tasks)
    assert len(buddy_tasks) == len(sample_owner.pets[0].tasks)
