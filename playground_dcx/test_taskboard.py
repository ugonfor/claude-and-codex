"""
Tests for the collaborative task board.
Built by Claude-Worker.
"""

import json
import os
import tempfile
import pytest

from task_model import Task, TaskStore, HistoryEntry, TaskStatus, Agent


@pytest.fixture
def temp_store(tmp_path):
    """Create a TaskStore with a temporary file."""
    filepath = str(tmp_path / "test_tasks.json")
    return TaskStore(filepath)


class TestTask:
    def test_create_task(self):
        task = Task(id=1, title="Test task")
        assert task.id == 1
        assert task.title == "Test task"
        assert task.status == "todo"
        assert task.assignee == "unassigned"

    def test_task_to_dict(self):
        task = Task(id=1, title="Test", description="A test task")
        d = task.to_dict()
        assert d["id"] == 1
        assert d["title"] == "Test"
        assert d["description"] == "A test task"
        assert d["status"] == "todo"

    def test_task_from_dict(self):
        data = {
            "id": 1,
            "title": "Test",
            "description": "Desc",
            "status": "in-progress",
            "assignee": "Claude-Worker",
            "created_at": "2026-03-04T00:00:00",
            "history": [],
        }
        task = Task.from_dict(data)
        assert task.id == 1
        assert task.status == "in-progress"
        assert task.assignee == "Claude-Worker"

    def test_task_roundtrip(self):
        task = Task(id=5, title="Roundtrip", description="Test roundtrip")
        d = task.to_dict()
        restored = Task.from_dict(d)
        assert restored.id == task.id
        assert restored.title == task.title
        assert restored.description == task.description


class TestHistoryEntry:
    def test_create_entry(self):
        entry = HistoryEntry(
            timestamp="2026-03-04T00:00:00",
            agent="Claude-Worker",
            action="created",
            details="Task created",
        )
        assert entry.agent == "Claude-Worker"
        assert entry.action == "created"

    def test_entry_roundtrip(self):
        entry = HistoryEntry(
            timestamp="2026-03-04T00:00:00",
            agent="Codex-Worker",
            action="status_changed",
            details="todo -> done",
        )
        d = entry.to_dict()
        restored = HistoryEntry.from_dict(d)
        assert restored.agent == entry.agent
        assert restored.action == entry.action


class TestTaskStore:
    def test_add_task(self, temp_store):
        task = temp_store.add_task("First task", "Description", "Claude-Worker")
        assert task.id == 1
        assert task.title == "First task"
        assert task.assignee == "Claude-Worker"
        assert len(task.history) == 1

    def test_add_multiple_tasks(self, temp_store):
        t1 = temp_store.add_task("Task 1")
        t2 = temp_store.add_task("Task 2")
        t3 = temp_store.add_task("Task 3")
        assert t1.id == 1
        assert t2.id == 2
        assert t3.id == 3

    def test_get_all_tasks(self, temp_store):
        temp_store.add_task("Task A")
        temp_store.add_task("Task B")
        tasks = temp_store.get_all_tasks()
        assert len(tasks) == 2

    def test_get_task(self, temp_store):
        temp_store.add_task("Find me")
        task = temp_store.get_task(1)
        assert task is not None
        assert task.title == "Find me"

    def test_get_nonexistent_task(self, temp_store):
        assert temp_store.get_task(999) is None

    def test_update_status(self, temp_store):
        temp_store.add_task("Update me")
        task = temp_store.update_status(1, "in-progress", "Claude-Worker")
        assert task.status == "in-progress"
        assert len(task.history) == 2  # created + status_changed

    def test_assign_task(self, temp_store):
        temp_store.add_task("Assign me")
        task = temp_store.assign_task(1, "Codex-Worker", "Claude-Worker")
        assert task.assignee == "Codex-Worker"
        assert len(task.history) == 2

    def test_delete_task(self, temp_store):
        temp_store.add_task("Delete me")
        assert temp_store.delete_task(1) is True
        assert temp_store.get_task(1) is None

    def test_delete_nonexistent(self, temp_store):
        assert temp_store.delete_task(999) is False

    def test_persistence(self, tmp_path):
        filepath = str(tmp_path / "persist_test.json")
        store1 = TaskStore(filepath)
        store1.add_task("Persistent task", "Should survive reload")

        store2 = TaskStore(filepath)
        tasks = store2.get_all_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "Persistent task"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
