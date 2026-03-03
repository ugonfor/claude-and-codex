"""
Task service / operations layer.
Originally proposed for Codex-Worker; built by Claude-Worker to meet deadline.
Codex-Worker: feel free to improve or replace this!
"""

from task_model import TaskStore, Task


class TaskService:
    """Higher-level operations on top of TaskStore."""

    def __init__(self, store: TaskStore):
        self.store = store

    def create_task(self, title: str, description: str = "", assignee: str = "unassigned") -> Task:
        return self.store.add_task(title, description, assignee)

    def get_tasks_by_status(self, status: str) -> list:
        return [t for t in self.store.get_all_tasks() if t.status == status]

    def get_tasks_by_assignee(self, assignee: str) -> list:
        return [t for t in self.store.get_all_tasks() if t.assignee == assignee]

    def move_to_in_progress(self, task_id: int, agent: str) -> Task | None:
        return self.store.update_status(task_id, "in-progress", agent)

    def complete_task(self, task_id: int, agent: str) -> Task | None:
        return self.store.update_status(task_id, "done", agent)

    def get_summary(self) -> dict:
        tasks = self.store.get_all_tasks()
        return {
            "total": len(tasks),
            "todo": len([t for t in tasks if t.status == "todo"]),
            "in_progress": len([t for t in tasks if t.status == "in-progress"]),
            "done": len([t for t in tasks if t.status == "done"]),
            "by_assignee": self._count_by_assignee(tasks),
        }

    def _count_by_assignee(self, tasks: list) -> dict:
        counts = {}
        for t in tasks:
            counts[t.assignee] = counts.get(t.assignee, 0) + 1
        return counts

    def bulk_assign(self, task_ids: list, assignee: str, agent: str) -> list:
        results = []
        for tid in task_ids:
            result = self.store.assign_task(tid, assignee, agent)
            if result:
                results.append(result)
        return results
