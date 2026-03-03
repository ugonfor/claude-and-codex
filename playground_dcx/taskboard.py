#!/usr/bin/env python3
"""
Collaborative Task Board CLI
Built jointly by Claude-Worker and Codex-Worker.

Usage:
    python taskboard.py add "Task title" --desc "Description" --assignee Claude-Worker
    python taskboard.py list [--status todo|in-progress|done]
    python taskboard.py update <id> --status done --agent Claude-Worker
    python taskboard.py assign <id> --to Codex-Worker --agent Claude-Worker
    python taskboard.py show <id>
    python taskboard.py history [<id>]
    python taskboard.py delete <id>
    python taskboard.py stats
"""

import argparse
import sys

from task_model import TaskStore

# Try to import Codex-Worker's modules (they may not exist yet)
try:
    from task_service import TaskService
    HAS_SERVICE = True
except ImportError:
    HAS_SERVICE = False

try:
    from task_display import TaskDisplay
    HAS_DISPLAY = True
except ImportError:
    HAS_DISPLAY = False


def get_store():
    return TaskStore("tasks.json")


def get_service():
    if HAS_SERVICE:
        return TaskService(get_store())
    return None


# ---- Fallback display functions (used if task_display.py not available) ----

def display_task(task):
    if HAS_DISPLAY:
        print(TaskDisplay.format_task(task))
        return
    status_icons = {"todo": "[ ]", "in-progress": "[~]", "done": "[x]"}
    icon = status_icons.get(task.status, "[?]")
    print(f"  {icon} #{task.id}: {task.title}")
    if task.description:
        print(f"       {task.description}")
    print(f"       Assignee: {task.assignee} | Status: {task.status}")


def display_task_list(tasks):
    if HAS_DISPLAY:
        print(TaskDisplay.format_task_list(tasks))
        return
    if not tasks:
        print("  No tasks found.")
        return
    for task in tasks:
        display_task(task)
        print()


def display_history(entries):
    if HAS_DISPLAY:
        print(TaskDisplay.format_history(entries))
        return
    if not entries:
        print("  No history entries.")
        return
    for entry in entries:
        ts = entry.timestamp if hasattr(entry, 'timestamp') else entry.get('timestamp', '?')
        agent = entry.agent if hasattr(entry, 'agent') else entry.get('agent', '?')
        action = entry.action if hasattr(entry, 'action') else entry.get('action', '?')
        details = entry.details if hasattr(entry, 'details') else entry.get('details', '')
        print(f"  [{ts}] {agent}: {action} - {details}")


def display_stats(tasks):
    if HAS_DISPLAY:
        print(TaskDisplay.format_stats(tasks))
        return
    total = len(tasks)
    by_status = {}
    by_assignee = {}
    for t in tasks:
        by_status[t.status] = by_status.get(t.status, 0) + 1
        by_assignee[t.assignee] = by_assignee.get(t.assignee, 0) + 1
    print(f"\n  Task Board Stats")
    print(f"  ================")
    print(f"  Total tasks: {total}")
    print(f"\n  By status:")
    for status, count in sorted(by_status.items()):
        print(f"    {status}: {count}")
    print(f"\n  By assignee:")
    for assignee, count in sorted(by_assignee.items()):
        print(f"    {assignee}: {count}")


# ---- CLI Commands ----

def cmd_add(args):
    store = get_store()
    assignee = args.assignee or "unassigned"
    desc = args.desc or ""
    task = store.add_task(args.title, desc, assignee)
    print(f"  Created task #{task.id}: {task.title}")
    display_task(task)


def cmd_list(args):
    store = get_store()
    tasks = store.get_all_tasks()
    if args.status:
        tasks = [t for t in tasks if t.status == args.status]
    if args.assignee:
        tasks = [t for t in tasks if t.assignee == args.assignee]
    print(f"\n  Task Board ({len(tasks)} tasks)")
    print(f"  {'=' * 40}")
    display_task_list(tasks)


def cmd_update(args):
    store = get_store()
    agent = args.agent or "unassigned"
    valid_statuses = ["todo", "in-progress", "done"]
    if args.status not in valid_statuses:
        print(f"  Error: status must be one of {valid_statuses}")
        return
    task = store.update_status(args.id, args.status, agent)
    if task:
        print(f"  Updated task #{task.id} -> {args.status}")
        display_task(task)
    else:
        print(f"  Error: task #{args.id} not found")


def cmd_assign(args):
    store = get_store()
    agent = args.agent or "unassigned"
    task = store.assign_task(args.id, args.to, agent)
    if task:
        print(f"  Assigned task #{task.id} to {args.to}")
        display_task(task)
    else:
        print(f"  Error: task #{args.id} not found")


def cmd_show(args):
    store = get_store()
    task = store.get_task(args.id)
    if task:
        print(f"\n  Task Details")
        print(f"  {'=' * 40}")
        display_task(task)
        print(f"\n  History:")
        display_history(task.history)
    else:
        print(f"  Error: task #{args.id} not found")


def cmd_history(args):
    store = get_store()
    if args.id:
        task = store.get_task(args.id)
        if task:
            print(f"\n  History for task #{task.id}: {task.title}")
            display_history(task.history)
        else:
            print(f"  Error: task #{args.id} not found")
    else:
        # Show all history across all tasks
        tasks = store.get_all_tasks()
        all_history = []
        for t in tasks:
            for h in t.history:
                all_history.append((t.id, h))
        all_history.sort(
            key=lambda x: (
                x[1].timestamp if hasattr(x[1], 'timestamp') else x[1].get('timestamp', '')
            )
        )
        print(f"\n  Full History Log")
        print(f"  {'=' * 40}")
        for task_id, entry in all_history:
            ts = entry.timestamp if hasattr(entry, 'timestamp') else entry.get('timestamp', '?')
            agent = entry.agent if hasattr(entry, 'agent') else entry.get('agent', '?')
            action = entry.action if hasattr(entry, 'action') else entry.get('action', '?')
            details = entry.details if hasattr(entry, 'details') else entry.get('details', '')
            print(f"  [{ts}] Task #{task_id} | {agent}: {action} - {details}")


def cmd_delete(args):
    store = get_store()
    if store.delete_task(args.id):
        print(f"  Deleted task #{args.id}")
    else:
        print(f"  Error: task #{args.id} not found")


def cmd_stats(args):
    store = get_store()
    tasks = store.get_all_tasks()
    display_stats(tasks)


def main():
    parser = argparse.ArgumentParser(
        description="Collaborative Task Board - Built by Claude-Worker & Codex-Worker"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # add
    p_add = subparsers.add_parser("add", help="Add a new task")
    p_add.add_argument("title", help="Task title")
    p_add.add_argument("--desc", help="Task description")
    p_add.add_argument("--assignee", help="Assignee (Claude-Worker or Codex-Worker)")
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = subparsers.add_parser("list", help="List tasks")
    p_list.add_argument("--status", help="Filter by status")
    p_list.add_argument("--assignee", help="Filter by assignee")
    p_list.set_defaults(func=cmd_list)

    # update
    p_update = subparsers.add_parser("update", help="Update task status")
    p_update.add_argument("id", type=int, help="Task ID")
    p_update.add_argument("--status", required=True, help="New status")
    p_update.add_argument("--agent", help="Agent making the change")
    p_update.set_defaults(func=cmd_update)

    # assign
    p_assign = subparsers.add_parser("assign", help="Assign task to agent")
    p_assign.add_argument("id", type=int, help="Task ID")
    p_assign.add_argument("--to", required=True, help="Assignee")
    p_assign.add_argument("--agent", help="Agent making the change")
    p_assign.set_defaults(func=cmd_assign)

    # show
    p_show = subparsers.add_parser("show", help="Show task details")
    p_show.add_argument("id", type=int, help="Task ID")
    p_show.set_defaults(func=cmd_show)

    # history
    p_history = subparsers.add_parser("history", help="Show history log")
    p_history.add_argument("id", type=int, nargs="?", help="Task ID (optional)")
    p_history.set_defaults(func=cmd_history)

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete a task")
    p_delete.add_argument("id", type=int, help="Task ID")
    p_delete.set_defaults(func=cmd_delete)

    # stats
    p_stats = subparsers.add_parser("stats", help="Show task board statistics")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
