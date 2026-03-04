"""Replay experiment timeline logs.

Usage:
  python replay.py logs/<ts>/<setting>/timeline.jsonl          # replay at 1x speed
  python replay.py logs/<ts>/<setting>/timeline.jsonl --speed 5 # 5x speed
  python replay.py logs/<ts>/<setting>/timeline.jsonl --no-wait # instant (no delays)
  python replay.py logs/<ts>/<setting>/timeline.jsonl --summary # just print summary
"""

from __future__ import annotations
import json, sys, time
from pathlib import Path

# ANSI colors
C_RESET = "\033[0m"
C_DIM = "\033[2m"
C_BOLD = "\033[1m"
C_BLUE = "\033[34m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_RED = "\033[31m"
C_CYAN = "\033[36m"
C_MAGENTA = "\033[35m"

AGENT_COLORS = {
    "Claude-A": C_MAGENTA, "Claude-B": C_CYAN,
    "Claude": C_MAGENTA, "Codex": C_GREEN,
    "Director": C_YELLOW, "Claude-Worker": C_MAGENTA, "Codex-Worker": C_GREEN,
}


def load_timeline(path: Path) -> list[dict]:
    events = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def format_event(event: dict) -> str:
    t = event.get("elapsed_s", 0)
    ts = f"{C_DIM}[{t:7.1f}s]{C_RESET}"
    etype = event["type"]

    if etype == "note":
        return f"{ts} {C_BOLD}{event['message']}{C_RESET}"

    elif etype == "agent_start":
        agent = event["agent"]
        color = AGENT_COLORS.get(agent, "")
        prompt_preview = event.get("prompt", "")[:80].replace("\n", " ")
        return f"{ts} {color}{C_BOLD}{agent}{C_RESET} started | prompt: {C_DIM}{prompt_preview}...{C_RESET}"

    elif etype == "agent_end":
        agent = event["agent"]
        color = AGENT_COLORS.get(agent, "")
        rc = event.get("returncode", "?")
        elapsed = event.get("elapsed_s", 0)
        return f"{ts} {color}{C_BOLD}{agent}{C_RESET} ended | rc={rc} | {elapsed:.1f}s"

    elif etype == "agent_output":
        agent = event["agent"]
        color = AGENT_COLORS.get(agent, "")
        content = event.get("content", "")
        if len(content) > 120:
            content = content[:117] + "..."
        return f"{ts} {color}{agent}{C_RESET} | {content}"

    elif etype == "fs_event":
        fs_type = event.get("fs_type", "?")
        path = event.get("path", "?")
        size = event.get("size_bytes", None)
        icons = {"created": f"{C_GREEN}+", "modified": f"{C_YELLOW}~", "deleted": f"{C_RED}-"}
        icon = icons.get(fs_type, "?")
        size_str = f" ({size}B)" if size else ""
        content_preview = ""
        if "content" in event and event["content"]:
            first_line = event["content"].split("\n")[0][:60]
            content_preview = f" {C_DIM}| {first_line}{C_RESET}"
        return f"{ts} {icon} {fs_type:8}{C_RESET} {C_BOLD}{path}{C_RESET}{size_str}{content_preview}"

    return f"{ts} {C_DIM}{json.dumps(event)}{C_RESET}"


def print_summary(events: list[dict]):
    """Print a summary of the timeline."""
    agents = set()
    agent_lines = {}
    fs_creates = 0
    fs_modifies = 0
    total_elapsed = 0

    for e in events:
        if e["type"] == "agent_start":
            agents.add(e["agent"])
        elif e["type"] == "agent_output":
            agent_lines[e["agent"]] = agent_lines.get(e["agent"], 0) + 1
        elif e["type"] == "fs_event":
            if e.get("fs_type") == "created":
                fs_creates += 1
            elif e.get("fs_type") == "modified":
                fs_modifies += 1
        elif e["type"] == "agent_end":
            total_elapsed = max(total_elapsed, e.get("elapsed_s", 0))

    print(f"\n{C_BOLD}Timeline Summary{C_RESET}")
    print(f"  Total events: {len(events)}")
    print(f"  Duration: {total_elapsed:.1f}s")
    print(f"  Agents: {', '.join(sorted(agents))}")
    for agent, lines in sorted(agent_lines.items()):
        color = AGENT_COLORS.get(agent, "")
        print(f"    {color}{agent}{C_RESET}: {lines} output lines")
    print(f"  Files created: {fs_creates}")
    print(f"  Files modified: {fs_modifies}")


def replay(events: list[dict], speed: float = 1.0, no_wait: bool = False):
    """Replay events with timing."""
    prev_elapsed = 0.0

    for event in events:
        elapsed = event.get("elapsed_s", 0)

        # Wait proportionally
        if not no_wait and elapsed > prev_elapsed:
            delay = (elapsed - prev_elapsed) / speed
            if delay > 0.01:
                time.sleep(min(delay, 2.0))  # cap at 2s real time
        prev_elapsed = elapsed

        print(format_event(event))


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay.py <timeline.jsonl> [--speed N] [--no-wait] [--summary]")
        print("\nAvailable logs:")
        logs_dir = Path(__file__).resolve().parent / "logs"
        if logs_dir.exists():
            for tl in sorted(logs_dir.rglob("timeline.jsonl")):
                print(f"  {tl.relative_to(logs_dir.parent)}")
        sys.exit(1)

    path = Path(sys.argv[1])
    speed = 1.0
    no_wait = False
    summary_only = False

    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == "--speed" and i + 1 < len(sys.argv):
            speed = float(sys.argv[i + 1])
        elif arg == "--no-wait":
            no_wait = True
        elif arg == "--summary":
            summary_only = True

    # Fix Windows encoding
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    events = load_timeline(path)
    print(f"{C_BOLD}Loaded {len(events)} events from {path}{C_RESET}\n")

    if summary_only:
        print_summary(events)
    else:
        print_summary(events)
        print(f"\n{C_BOLD}--- Replay (speed={speed}x) ---{C_RESET}\n")
        replay(events, speed=speed, no_wait=no_wait)


if __name__ == "__main__":
    main()
