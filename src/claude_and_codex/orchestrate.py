"""Orchestrator that runs actual claude and codex CLI tools as subprocesses.

Design: Free-form collaboration. No fixed phases. Both agents see the full
conversation and decide themselves what to do -- write code, review, fix,
run tests, or pass. The orchestrator just manages turns and verification.

Usage: python -m claude_and_codex
  (should be run outside of claude/codex sessions)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

# ── Constants ────────────────────────────────────────────────────────────────

MAX_TURNS = 12          # Max total agent turns per task
CLI_TIMEOUT = 600       # 10 min per agent call
VERIFY_TIMEOUT = 120    # 2 min for test runs
PROMPT_MAX_CHARS = 50_000
CODEX_ARG_LIMIT = 7500

# ANSI escape codes for terminal output
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
WHITE = "\033[37m"
RESET = "\033[0m"

COLLAB_SYSTEM = """\
You are {name}, collaborating with {partner} on a coding task.
You share a workspace. You can see everything the other agent has said and done.

Guidelines:
- Do whatever is most useful right now: write code, fix bugs, review, suggest, run tests.
- Do NOT repeat what the other agent already did.
- Do NOT ask the user for clarification. Figure it out together.
- If you made code changes, mention what files you changed.
- When you think the task is fully complete and verified, say DONE.
- If the other agent already handled everything well, say PASS.
- Be concise. Don't narrate -- just do the work.
"""


# ── Helpers ──────────────────────────────────────────────────────────────────


def find_cli(name: str) -> str | None:
    return shutil.which(name)


def timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def elapsed_str(start: float) -> str:
    secs = time.time() - start
    if secs < 60:
        return f"{secs:.1f}s"
    return f"{int(secs // 60)}m{secs % 60:.0f}s"


def truncate(text: str, max_len: int = 2000) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n... ({len(text)} chars total)"


def build_context(history: list[tuple[str, str]], max_entries: int = 12) -> str:
    labels = {"user": "User", "claude": "Claude", "codex": "Codex", "system": "System"}
    parts: list[str] = []
    for role, content in history[-max_entries:]:
        label = labels.get(role, role)
        parts.append(f"[{label}]: {truncate(content)}")
    return "\n\n".join(parts)


def is_done_or_pass(text: str) -> bool:
    """Check if the agent signals completion."""
    if not text:
        return True
    upper = text.strip().upper()
    # Starts with PASS or DONE (handles "PASS — waiting..." style)
    if upper.startswith("PASS") or upper.startswith("DONE"):
        return True
    # Last line starts with PASS/DONE
    last_line = upper.split("\n")[-1].strip()
    return last_line.startswith("PASS") or last_line.startswith("DONE")


def is_error(text: str | None) -> bool:
    if not text:
        return True
    s = text.lstrip()
    return s.startswith("[Error") or s.startswith("[No output from")


# ── CLI runners ──────────────────────────────────────────────────────────────


def run_cli(
    name: str, args: list[str], cwd: str,
    timeout: int = CLI_TIMEOUT,
    env_overrides: dict[str, str | None] | None = None,
    stdin_text: str | None = None,
) -> str:
    """Run a CLI tool, letting it render directly to terminal.

    The CLI's own stdout goes straight to the user's terminal (inherited).
    We only capture stdout for conversation history via a tee approach.
    """
    env = os.environ.copy()
    for key, value in (env_overrides or {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value

    try:
        # Pipe stdout so we can capture it, but tee each line to terminal
        proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE if stdin_text else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            cwd=cwd, env=env,
            encoding="utf-8", errors="replace",
        )

        if stdin_text and proc.stdin:
            proc.stdin.write(stdin_text)
            proc.stdin.close()

        captured: list[str] = []
        deadline = time.time() + timeout

        for line in iter(proc.stdout.readline, ""):
            if time.time() > deadline:
                proc.kill()
                return f"[Error: {name} timed out after {timeout}s]"
            # Pass through directly — let the CLI's formatting show
            sys.stdout.write(line)
            sys.stdout.flush()
            captured.append(line)

        proc.wait()
        return "".join(captured).strip() or f"[No output from {name}]"
    except Exception as e:
        return f"[Error running {name}: {type(e).__name__}: {e}]"


def run_claude(prompt: str, cwd: str, images: list[str] | None = None) -> str:
    claude_bin = find_cli("claude")
    if not claude_bin:
        return "[Error: claude CLI not found on PATH]"

    full_prompt = prompt
    if images:
        refs = "\n".join(f"- {img}" for img in images)
        full_prompt += f"\n\nAttached images (read as needed):\n{refs}"

    if len(full_prompt) > PROMPT_MAX_CHARS:
        full_prompt = full_prompt[:PROMPT_MAX_CHARS] + "\n[prompt truncated]"

    return run_cli(
        "Claude",
        [claude_bin, "-p", "--dangerously-skip-permissions"],
        cwd, stdin_text=full_prompt,
        env_overrides={"CLAUDECODE": None},
    )


def run_codex(prompt: str, cwd: str, images: list[str] | None = None) -> str:
    codex_bin = find_cli("codex")
    if not codex_bin:
        return "[Error: codex CLI not found on PATH]"

    if len(prompt) > PROMPT_MAX_CHARS:
        prompt = prompt[:PROMPT_MAX_CHARS] + "\n[prompt truncated]"

    args = [codex_bin, "exec", "--full-auto"]
    for img in images or []:
        args.extend(["-i", img])

    if len(prompt) > CODEX_ARG_LIMIT:
        prompt_file = Path(cwd) / ".codex_prompt.tmp"
        try:
            prompt_file.write_text(prompt, encoding="utf-8")
            args.append(
                f"Read your full task from '{prompt_file}'. Execute it. "
                f"Delete the file when done."
            )
            return run_cli("Codex", args, cwd)
        finally:
            prompt_file.unlink(missing_ok=True)
    else:
        args.append(prompt)
        return run_cli("Codex", args, cwd)


# ── Verification ─────────────────────────────────────────────────────────────


def detect_verify_command(cwd: str) -> str | None:
    p = Path(cwd)
    if (p / "pyproject.toml").exists() or (p / "setup.py").exists():
        if (p / "tests").exists() or (p / "test").exists():
            return "python -m pytest -q 2>&1"
    if (p / "package.json").exists():
        try:
            pkg = json.loads((p / "package.json").read_text())
            if "test" in pkg.get("scripts", {}):
                return "npm test 2>&1"
        except (json.JSONDecodeError, OSError):
            pass
    if (p / "Cargo.toml").exists():
        return "cargo test 2>&1"
    if (p / "go.mod").exists():
        return "go test ./... 2>&1"
    return None


def run_verify(cwd: str, verify_cmd: str | None = None) -> tuple[bool, str]:
    cmd = verify_cmd or detect_verify_command(cwd)
    if cmd is None:
        return True, "(no verify command)"

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=VERIFY_TIMEOUT, cwd=cwd,
            encoding="utf-8", errors="replace",
        )
        output = ((result.stdout or "") + (result.stderr or "")).strip()
        return result.returncode == 0, output[:3000]
    except subprocess.TimeoutExpired:
        return False, f"Verification timed out after {VERIFY_TIMEOUT}s"
    except Exception as e:
        return False, f"Verification error: {e}"


# ── Display ──────────────────────────────────────────────────────────────────

AGENT_STYLES = {
    "Claude": "magenta",
    "Codex": "green",
}


def print_agent(name: str, color: str, text: str, duration: str = "") -> None:
    """Display agent output in a Rich panel."""
    style = AGENT_STYLES.get(name, color)
    subtitle = f"{duration}" if duration else None
    content = Markdown(text) if any(c in text for c in ["```", "**", "- ", "# "]) else Text(text)
    console.print(Panel(
        content,
        title=f"[bold]{name}[/bold]",
        subtitle=subtitle,
        border_style=style,
        padding=(0, 1),
    ))


def print_banner() -> None:
    console.print()
    console.print(Panel(
        "[dim]Both agents collaborate freely on your task.\n"
        "No fixed workflow -- they decide what to do.\n"
        "Type /help for commands.[/dim]",
        title="[bold]claude-and-codex v0.5[/bold]",
        subtitle="Free-form AI collaboration",
        border_style="cyan",
        padding=(1, 2),
    ))


def print_help() -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Command", style="bold cyan")
    table.add_column("Description")
    table.add_row("/help", "Show this help")
    table.add_row("/quit", "Exit")
    table.add_row("/status", "Show configuration")
    table.add_row("/clear", "Clear conversation history")
    table.add_row(f"/turns <n>", f"Set max turns per task (default: {MAX_TURNS})")
    table.add_row("/verify <cmd>", "Set verification command (empty = auto-detect)")
    table.add_row("/cd <path>", "Change working directory")
    table.add_row("/image <path>", "Attach image(s) for next task")
    table.add_row("/images", "List attached images")
    table.add_row("/clearimages", "Remove all attached images")
    console.print(Panel(table, title="[bold]Commands[/bold]", border_style="dim"))


def print_status(claude_ok, codex_ok, cwd, verify_cmd, max_turns, images):
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("Working dir", cwd)
    table.add_row("Claude CLI", "[green]found[/green]" if claude_ok else "[red]not found[/red]")
    table.add_row("Codex CLI", "[green]found[/green]" if codex_ok else "[red]not found[/red]")
    table.add_row("Verify cmd", verify_cmd or "[dim](auto-detect)[/dim]")
    table.add_row("Max turns", str(max_turns))
    table.add_row("Images", f"{len(images)} attached")
    console.print(Panel(table, title="[bold]Status[/bold]", border_style="dim"))


# ── Image handling ───────────────────────────────────────────────────────────

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}


def resolve_image_path(path_str: str, cwd: str) -> str | None:
    p = Path(path_str)
    if not p.is_absolute():
        p = (Path(cwd) / p).resolve()
    if not p.exists():
        console.print(f"  [red]Image not found: {p}[/red]")
        return None
    if p.suffix.lower() not in IMAGE_EXTENSIONS:
        console.print(f"  [yellow]Warning: {p.name} may not be an image[/yellow]")
    return str(p)


# ── Core collaboration loop ─────────────────────────────────────────────────


def collaborate(
    cwd: str,
    claude_ok: bool,
    codex_ok: bool,
    history: list[tuple[str, str]],
    images: list[str],
    verify_cmd: str | None,
    max_turns: int,
) -> None:
    """Free-form collaboration loop.

    Agents take turns. Each agent's CLI output renders directly to terminal
    (no capture/re-render). The orchestrator just adds thin headers and
    manages turn order.
    """
    agents = []
    if claude_ok:
        agents.append(("claude", "Claude", "Codex", run_claude))
    if codex_ok:
        agents.append(("codex", "Codex", "Claude", run_codex))

    if not agents:
        console.print("[red]No agents available.[/red]")
        return

    consecutive_done = 0
    turn = 0

    while turn < max_turns:
        role, name, partner, runner = agents[turn % len(agents)]
        turn += 1

        context = build_context(history)
        system = COLLAB_SYSTEM.format(name=name, partner=partner)
        prompt = f"{system}\nConversation so far:\n{context}"

        # Verification after changes
        if turn > 1 and turn % len(agents) == 1:
            passed, verify_output = run_verify(cwd, verify_cmd)
            if not passed:
                prompt += (
                    f"\n\n[System]: Verification FAILED:\n"
                    f"```\n{verify_output}\n```\nFix these errors."
                )
                history.append(("system", f"Verification failed:\n{verify_output}"))
                console.print("[red]Verification failed[/red]")
            else:
                history.append(("system", "Verification passed."))
                console.print("[green]Verification passed[/green]")
            context = build_context(history)
            prompt = f"{system}\nConversation so far:\n{context}"

        # Header
        style = AGENT_STYLES.get(name, "white")
        console.rule(f"[{style} bold]{name}[/{style} bold]  [dim]turn #{turn}[/dim]", style=style)

        start = time.time()
        img = images if turn <= len(agents) else None
        response = runner(prompt, cwd, images=img)
        duration = elapsed_str(start)

        console.print(f"[dim]({duration})[/dim]")
        history.append((role, response))

        if is_error(response):
            consecutive_done = 0
            continue

        if is_done_or_pass(response):
            consecutive_done += 1
            if consecutive_done >= len(agents):
                console.print(f"\n[bold cyan]All agents agree: task complete.[/bold cyan]")
                break
        else:
            consecutive_done = 0

    else:
        console.print(f"\n[yellow]Reached max turns ({max_turns}).[/yellow]")

    # Final verification
    passed, verify_output = run_verify(cwd, verify_cmd)
    if passed:
        console.print(f"\n[bold green]Final verification: passed[/bold green]")
    else:
        console.print(f"\n[bold red]Final verification: FAILED[/bold red]")
        console.print(f"[dim]{verify_output[:500]}[/dim]")


# ── Command handling ─────────────────────────────────────────────────────────


def handle_command(
    user_input: str, max_turns: int, verify_cmd: str | None,
    images: list[str], cwd: str, history: list[tuple[str, str]],
    claude_ok: bool, codex_ok: bool,
) -> tuple[bool, int, str | None, str]:
    """Returns (is_command, max_turns, verify_cmd, cwd)."""

    if user_input == "/quit":
        console.print("[dim]Goodbye![/dim]")
        sys.exit(0)

    if user_input == "/help":
        print_help()
        return True, max_turns, verify_cmd, cwd

    if user_input == "/status":
        print_status(claude_ok, codex_ok, cwd, verify_cmd, max_turns, images)
        return True, max_turns, verify_cmd, cwd

    if user_input == "/clear":
        history.clear()
        console.print("  [dim]Conversation cleared.[/dim]")
        return True, max_turns, verify_cmd, cwd

    if user_input.startswith("/turns "):
        try:
            max_turns = int(user_input.split()[1])
            console.print(f"  [dim]Max turns set to {max_turns}[/dim]")
        except ValueError:
            console.print("  [red]Usage: /turns <number>[/red]")
        return True, max_turns, verify_cmd, cwd

    if user_input == "/verify" or user_input.startswith("/verify "):
        verify_cmd = user_input[7:].strip() or None
        console.print(f"  [dim]Verify: {verify_cmd or '(auto-detect)'}[/dim]")
        return True, max_turns, verify_cmd, cwd

    if user_input.startswith("/cd "):
        target = Path(user_input[4:].strip())
        if not target.is_absolute():
            target = (Path(cwd) / target).resolve()
        if target.is_dir():
            cwd = str(target)
            verify_cmd = detect_verify_command(cwd)
            console.print(f"  [dim]Working dir: {cwd}[/dim]")
        else:
            console.print(f"  [red]Not a directory: {target}[/red]")
        return True, max_turns, verify_cmd, cwd

    if user_input.startswith("/image "):
        for raw in user_input[7:].strip().split():
            resolved = resolve_image_path(raw, cwd)
            if resolved:
                images.append(resolved)
                console.print(f"  [dim]Attached: {resolved}[/dim]")
        return True, max_turns, verify_cmd, cwd

    if user_input == "/images":
        if images:
            for img in images:
                console.print(f"  [dim]{img}[/dim]")
        else:
            console.print("  [dim]No images attached.[/dim]")
        return True, max_turns, verify_cmd, cwd

    if user_input == "/clearimages":
        images.clear()
        console.print("  [dim]Images cleared.[/dim]")
        return True, max_turns, verify_cmd, cwd

    if user_input.startswith("/"):
        console.print("  [yellow]Unknown command. Type /help[/yellow]")
        return True, max_turns, verify_cmd, cwd

    return False, max_turns, verify_cmd, cwd


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    if os.environ.get("CLAUDECODE"):
        console.print("[yellow]Warning: Running inside a Claude Code session.\nclaude -p may not work. Run this directly in your terminal.[/yellow]")

    claude_ok = find_cli("claude") is not None
    codex_ok = find_cli("codex") is not None

    print_banner()

    cwd = os.getcwd()
    verify_cmd = detect_verify_command(cwd)
    max_turns = MAX_TURNS
    history: list[tuple[str, str]] = []
    images: list[str] = []

    print_status(claude_ok, codex_ok, cwd, verify_cmd, max_turns, images)

    if not claude_ok and not codex_ok:
        console.print("\n[red bold]Error: No CLI agents found. Install claude or codex.[/red bold]")
        sys.exit(1)

    console.print()

    while True:
        try:
            user_input = console.input("[bold white]You > [/bold white]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        is_cmd, max_turns, verify_cmd, cwd = handle_command(
            user_input, max_turns, verify_cmd, images, cwd,
            history, claude_ok, codex_ok,
        )
        if is_cmd:
            continue

        # Run collaboration
        total_start = time.time()
        history.append(("user", user_input))

        try:
            collaborate(
                cwd, claude_ok, codex_ok, history, images,
                verify_cmd, max_turns,
            )
        except KeyboardInterrupt:
            console.print(f"\n[yellow]Task interrupted.[/yellow]")

        console.print(f"\n[dim]Total: {elapsed_str(total_start)}[/dim]")

        if images:
            images.clear()


if __name__ == "__main__":
    main()
