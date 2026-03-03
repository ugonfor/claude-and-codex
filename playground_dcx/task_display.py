"""
Task display / formatting module.
Originally proposed for Codex-Worker; built by Claude-Worker to meet deadline.
Codex-Worker: feel free to improve or replace this!
"""

from task_model import Task, HistoryEntry


class TaskDisplay:
    """Formats tasks and history for terminal display."""

    STATUS_ICONS = {
        "todo": "[ ]",
        "in-progress": "[~]",
        "done": "[x]",
    }

    COLORS = {
        "todo": "\033[33m",       # yellow
        "in-progress": "\033[36m", # cyan
        "done": "\033[32m",        # green
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
    }

    @classmethod
    def format_task(cls, task: Task, use_color: bool = True) -> str:
        icon = cls.STATUS_ICONS.get(task.status, "[?]")
        if use_color:
            c = cls.COLORS.get(task.status, "")
            r = cls.COLORS["reset"]
            b = cls.COLORS["bold"]
            d = cls.COLORS["dim"]
        else:
            c = r = b = d = ""

        lines = [f"  {c}{icon}{r} {b}#{task.id}{r}: {task.title}"]
        if task.description:
            lines.append(f"       {d}{task.description}{r}")
        lines.append(f"       Assignee: {c}{task.assignee}{r} | Status: {c}{task.status}{r}")
        return "\n".join(lines)

    @classmethod
    def format_task_list(cls, tasks: list, use_color: bool = True) -> str:
        if not tasks:
            return "  No tasks found."
        parts = []
        for task in tasks:
            parts.append(cls.format_task(task, use_color))
        return "\n\n".join(parts)

    @classmethod
    def format_history(cls, entries: list, use_color: bool = True) -> str:
        if not entries:
            return "  No history entries."
        if use_color:
            d = cls.COLORS["dim"]
            r = cls.COLORS["reset"]
        else:
            d = r = ""
        lines = []
        for entry in entries:
            ts = entry.timestamp if hasattr(entry, 'timestamp') else entry.get('timestamp', '?')
            agent = entry.agent if hasattr(entry, 'agent') else entry.get('agent', '?')
            action = entry.action if hasattr(entry, 'action') else entry.get('action', '?')
            details = entry.details if hasattr(entry, 'details') else entry.get('details', '')
            lines.append(f"  {d}[{ts}]{r} {agent}: {action} - {details}")
        return "\n".join(lines)

    @classmethod
    def format_stats(cls, tasks: list, use_color: bool = True) -> str:
        if use_color:
            b = cls.COLORS["bold"]
            r = cls.COLORS["reset"]
        else:
            b = r = ""

        total = len(tasks)
        by_status = {}
        by_assignee = {}
        for t in tasks:
            by_status[t.status] = by_status.get(t.status, 0) + 1
            by_assignee[t.assignee] = by_assignee.get(t.assignee, 0) + 1

        lines = [
            f"\n  {b}Task Board Stats{r}",
            f"  {'=' * 30}",
            f"  Total tasks: {total}",
            "",
            f"  {b}By status:{r}",
        ]
        for status in ["todo", "in-progress", "done"]:
            count = by_status.get(status, 0)
            icon = cls.STATUS_ICONS.get(status, "[?]")
            lines.append(f"    {icon} {status}: {count}")

        lines.append("")
        lines.append(f"  {b}By assignee:{r}")
        for assignee, count in sorted(by_assignee.items()):
            lines.append(f"    {assignee}: {count}")

        return "\n".join(lines)
