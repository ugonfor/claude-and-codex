"""
Task data model and JSON storage layer.
Built by Claude-Worker as part of the collaborative task board project.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional


class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in-progress"
    DONE = "done"


class Agent(Enum):
    CLAUDE = "Claude-Worker"
    CODEX = "Codex-Worker"
    UNASSIGNED = "unassigned"


@dataclass
class HistoryEntry:
    timestamp: str
    agent: str
    action: str
    details: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "agent": self.agent,
            "action": self.action,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(**data)


@dataclass
class Task:
    id: int
    title: str
    description: str = ""
    status: str = "todo"
    assignee: str = "unassigned"
    created_at: str = ""
    history: list = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "assignee": self.assignee,
            "created_at": self.created_at,
            "history": [
                h.to_dict() if isinstance(h, HistoryEntry) else h
                for h in self.history
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        history = [
            HistoryEntry.from_dict(h) if isinstance(h, dict) else h
            for h in data.get("history", [])
        ]
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            status=data.get("status", "todo"),
            assignee=data.get("assignee", "unassigned"),
            created_at=data.get("created_at", ""),
            history=history,
        )


class TaskStore:
    """JSON file-backed task storage."""

    def __init__(self, filepath: str = "tasks.json"):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            self._write_data({"tasks": [], "next_id": 1})

    def _read_data(self) -> dict:
        with open(self.filepath, "r") as f:
            return json.load(f)

    def _write_data(self, data: dict):
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=2)

    def add_task(self, title: str, description: str = "", assignee: str = "unassigned") -> Task:
        data = self._read_data()
        task_id = data["next_id"]
        task = Task(
            id=task_id,
            title=title,
            description=description,
            assignee=assignee,
        )
        entry = HistoryEntry(
            timestamp=datetime.now().isoformat(),
            agent=assignee,
            action="created",
            details=f"Task '{title}' created",
        )
        task.history.append(entry)
        data["tasks"].append(task.to_dict())
        data["next_id"] = task_id + 1
        self._write_data(data)
        return task

    def get_all_tasks(self) -> list:
        data = self._read_data()
        return [Task.from_dict(t) for t in data["tasks"]]

    def get_task(self, task_id: int) -> Optional[Task]:
        for t in self.get_all_tasks():
            if t.id == task_id:
                return t
        return None

    def update_status(self, task_id: int, new_status: str, agent: str = "unassigned") -> Optional[Task]:
        data = self._read_data()
        for t in data["tasks"]:
            if t["id"] == task_id:
                old_status = t["status"]
                t["status"] = new_status
                entry = HistoryEntry(
                    timestamp=datetime.now().isoformat(),
                    agent=agent,
                    action="status_changed",
                    details=f"Status: {old_status} -> {new_status}",
                )
                t["history"].append(entry.to_dict())
                self._write_data(data)
                return Task.from_dict(t)
        return None

    def assign_task(self, task_id: int, assignee: str, agent: str = "unassigned") -> Optional[Task]:
        data = self._read_data()
        for t in data["tasks"]:
            if t["id"] == task_id:
                old_assignee = t["assignee"]
                t["assignee"] = assignee
                entry = HistoryEntry(
                    timestamp=datetime.now().isoformat(),
                    agent=agent,
                    action="assigned",
                    details=f"Assigned: {old_assignee} -> {assignee}",
                )
                t["history"].append(entry.to_dict())
                self._write_data(data)
                return Task.from_dict(t)
        return None

    def delete_task(self, task_id: int) -> bool:
        data = self._read_data()
        original_len = len(data["tasks"])
        data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
        if len(data["tasks"]) < original_len:
            self._write_data(data)
            return True
        return False
