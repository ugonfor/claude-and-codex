"""Director - Team Leader - Teammate orchestration engine.

Architecture:
  Director (User) -> Team Leader (claude -p) -> Teammates (claude -p, codex exec)

The Team Leader is an intelligent Claude instance that:
  - Understands the Director's intent
  - Breaks down tasks and dispatches to Teammates
  - Reviews teammate output and decides next steps
  - Runs verification
  - Only reports to Director when work is complete

Teammates are CLI subprocesses that do the actual work in full-auto mode.
Their output streams directly to the terminal so the Director can observe.

Usage: python -m claude_and_codex
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

console = Console()

# ── Constants ────────────────────────────────────────────────────────────────

MAX_ROUNDS = 8          # Max team leader reasoning rounds per task
CLI_TIMEOUT = 600       # 10 min per CLI call
VERIFY_TIMEOUT = 120    # 2 min for test runs
PROMPT_MAX_CHARS = 50_000
CODEX_ARG_LIMIT = 7500

TEAM_LEADER_SYSTEM = """\
You are the TEAM LEADER in a Director-Team Leader-Teammate system.

The DIRECTOR (user) gives you tasks. You have two TEAMMATES:
- Claude Code (via DISPATCH_CLAUDE) -- strong at analysis, architecture, careful code
- Codex (via DISPATCH_CODEX) -- strong at fast iteration, generation, different perspective

Your job:
1. Understand what the Director wants
2. Break down the task if needed
3. Dispatch work to teammates using commands
4. Review their output (you'll see it in the conversation)
5. Run verification when code changes are made
6. Continue until the task is fully complete
7. Report the final result to the Director

COMMANDS (put these on their own line, exactly as shown):

  DISPATCH_CLAUDE: <instruction for Claude Code>
  DISPATCH_CODEX: <instruction for Codex>
  VERIFY
  DONE: <summary for the Director>

Rules:
- You can dispatch to one or both teammates in a single response
- After dispatching, you'll see their output and can decide next steps
- ALWAYS verify after code changes before reporting DONE
- If a teammate's work has issues, dispatch a fix (to same or other teammate)
- Do NOT do the coding work yourself -- dispatch to teammates
- Be concise in your reasoning. Focus on coordination, not narration.
- NEVER ask the Director for clarification. Figure it out yourself.
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
    stream: bool = True,
) -> str:
    """Run a CLI tool. Streams output to terminal if stream=True."""
    env = os.environ.copy()
    for key, value in (env_overrides or {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value

    try:
        if stream:
            proc = subprocess.Popen(
                args,
                stdin=subprocess.PIPE if stdin_text else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
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
                sys.stdout.write(line)
                sys.stdout.flush()
                captured.append(line)
            proc.wait()
            return "".join(captured).strip() or f"[No output from {name}]"
        else:
            result = subprocess.run(
                args, input=stdin_text,
                capture_output=True, text=True, timeout=timeout,
                cwd=cwd, env=env, encoding="utf-8", errors="replace",
            )
            output = (result.stdout or "").strip()
            if result.returncode != 0 and result.stderr:
                output += f"\n[stderr: {result.stderr.strip()[:500]}]"
            return output or f"[No output from {name}]"
    except Exception as e:
        return f"[Error running {name}: {type(e).__name__}: {e}]"


def run_claude(prompt: str, cwd: str, images: list[str] | None = None,
               stream: bool = True) -> str:
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
        stream=stream,
    )


def run_codex(prompt: str, cwd: str, images: list[str] | None = None,
              stream: bool = True) -> str:
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
            return run_cli("Codex", args, cwd, stream=stream)
        finally:
            prompt_file.unlink(missing_ok=True)
    else:
        args.append(prompt)
        return run_cli("Codex", args, cwd, stream=stream)


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


# ── Command parsing ──────────────────────────────────────────────────────────


def parse_leader_commands(response: str) -> list[tuple[str, str]]:
    """Parse structured commands from the Team Leader's response.

    Returns list of (command, argument) tuples.
    Commands: DISPATCH_CLAUDE, DISPATCH_CODEX, VERIFY, DONE
    """
    commands: list[tuple[str, str]] = []
    for line in response.split("\n"):
        stripped = line.strip()
        if stripped.startswith("DISPATCH_CLAUDE:"):
            commands.append(("DISPATCH_CLAUDE", stripped[16:].strip()))
        elif stripped.startswith("DISPATCH_CODEX:"):
            commands.append(("DISPATCH_CODEX", stripped[15:].strip()))
        elif stripped.strip() == "VERIFY":
            commands.append(("VERIFY", ""))
        elif stripped.startswith("DONE:"):
            commands.append(("DONE", stripped[5:].strip()))
        elif stripped == "DONE":
            commands.append(("DONE", "Task complete."))
    return commands


# ── Display ──────────────────────────────────────────────────────────────────


def print_banner() -> None:
    console.print()
    console.print(Panel(
        "[dim]Director-Team Leader-Teammate model.\n"
        "You (Director) give tasks. The Team Leader coordinates.\n"
        "Teammates (Claude Code + Codex) do the work.\n"
        "Type /help for commands.[/dim]",
        title="[bold]claude-and-codex v0.6[/bold]",
        subtitle="AI Team Collaboration",
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
    table.add_row("/rounds <n>", f"Set max rounds per task (default: {MAX_ROUNDS})")
    table.add_row("/verify <cmd>", "Set verification command (empty = auto-detect)")
    table.add_row("/cd <path>", "Change working directory")
    table.add_row("/image <path>", "Attach image(s) for next task")
    table.add_row("/images", "List attached images")
    table.add_row("/clearimages", "Remove all attached images")
    console.print(Panel(table, title="[bold]Commands[/bold]", border_style="dim"))


def print_status(claude_ok, codex_ok, cwd, verify_cmd, max_rounds, images):
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("Working dir", cwd)
    table.add_row("Claude CLI", "[green]found[/green]" if claude_ok else "[red]not found[/red]")
    table.add_row("Codex CLI", "[green]found[/green]" if codex_ok else "[red]not found[/red]")
    table.add_row("Verify cmd", verify_cmd or "[dim](auto-detect)[/dim]")
    table.add_row("Max rounds", str(max_rounds))
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


# ── Core: Team Leader loop ──────────────────────────────────────────────────


def run_task(
    user_request: str,
    cwd: str,
    claude_ok: bool,
    codex_ok: bool,
    history: list[tuple[str, str]],
    images: list[str],
    verify_cmd: str | None,
    max_rounds: int,
) -> None:
    """Run the Director-Team Leader-Teammate loop for one task."""

    # Build conversation log for the team leader
    # (separate from the director-facing history)
    team_log: list[str] = []
    team_log.append(f"[Director's request]: {user_request}")

    for round_num in range(1, max_rounds + 1):
        console.rule(
            f"[cyan bold]Team Leader[/cyan bold]  [dim]round {round_num}/{max_rounds}[/dim]",
            style="cyan",
        )

        # Ask Team Leader what to do
        leader_prompt = (
            f"{TEAM_LEADER_SYSTEM}\n\n"
            f"Working directory: {cwd}\n"
            f"Available teammates: "
            f"{'Claude Code' if claude_ok else '(unavailable)'}, "
            f"{'Codex' if codex_ok else '(unavailable)'}\n\n"
            f"Conversation log:\n" + "\n\n".join(team_log)
        )

        # Team Leader thinks (captured, not streamed — it's coordination, not work)
        console.print("[dim]Team Leader thinking...[/dim]")
        start = time.time()
        leader_response = run_claude(leader_prompt, cwd, stream=False)
        console.print(f"[dim]({elapsed_str(start)})[/dim]")

        if is_error(leader_response):
            console.print(f"[red]Team Leader error: {leader_response[:300]}[/red]")
            break

        # Show the Team Leader's reasoning
        console.print(Panel(
            leader_response,
            title="[bold cyan]Team Leader[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        ))

        team_log.append(f"[Team Leader]: {leader_response}")

        # Parse and execute commands
        commands = parse_leader_commands(leader_response)

        if not commands:
            # No commands found — leader is just thinking/responding
            team_log.append("[System]: No commands detected. Continue or use DONE.")
            continue

        done = False
        for cmd, arg in commands:
            if cmd == "DISPATCH_CLAUDE":
                if not claude_ok:
                    team_log.append("[System]: Claude not available.")
                    console.print("[yellow]Claude not available, skipping.[/yellow]")
                    continue
                console.rule("[magenta bold]Claude Code[/magenta bold]  [dim]teammate[/dim]", style="magenta")
                start = time.time()
                img = images if round_num == 1 else None
                result = run_claude(arg, cwd, images=img, stream=True)
                console.print(f"\n[dim]({elapsed_str(start)})[/dim]")
                team_log.append(f"[Claude Code output]: {truncate(result)}")
                history.append(("claude", result))

            elif cmd == "DISPATCH_CODEX":
                if not codex_ok:
                    team_log.append("[System]: Codex not available.")
                    console.print("[yellow]Codex not available, skipping.[/yellow]")
                    continue
                console.rule("[green bold]Codex[/green bold]  [dim]teammate[/dim]", style="green")
                start = time.time()
                img = images if round_num == 1 else None
                result = run_codex(arg, cwd, images=img, stream=True)
                console.print(f"\n[dim]({elapsed_str(start)})[/dim]")
                team_log.append(f"[Codex output]: {truncate(result)}")
                history.append(("codex", result))

            elif cmd == "VERIFY":
                console.print("[dim]Running verification...[/dim]")
                passed, verify_output = run_verify(cwd, verify_cmd)
                if passed:
                    console.print("[bold green]Verification: passed[/bold green]")
                    team_log.append("[Verification]: PASSED")
                else:
                    console.print("[bold red]Verification: FAILED[/bold red]")
                    console.print(f"[dim]{verify_output[:500]}[/dim]")
                    team_log.append(f"[Verification]: FAILED\n{verify_output}")

            elif cmd == "DONE":
                console.print()
                console.print(Panel(
                    arg or "Task complete.",
                    title="[bold cyan]Result[/bold cyan]",
                    border_style="cyan",
                    padding=(0, 1),
                ))
                history.append(("system", f"Task complete: {arg}"))
                done = True
                break

        if done:
            break
    else:
        console.print(f"\n[yellow]Reached max rounds ({max_rounds}).[/yellow]")


# ── Command handling ─────────────────────────────────────────────────────────


def handle_command(
    user_input: str, max_rounds: int, verify_cmd: str | None,
    images: list[str], cwd: str, history: list[tuple[str, str]],
    claude_ok: bool, codex_ok: bool,
) -> tuple[bool, int, str | None, str]:
    """Returns (is_command, max_rounds, verify_cmd, cwd)."""

    if user_input == "/quit":
        console.print("[dim]Goodbye![/dim]")
        sys.exit(0)

    if user_input == "/help":
        print_help()
        return True, max_rounds, verify_cmd, cwd

    if user_input == "/status":
        print_status(claude_ok, codex_ok, cwd, verify_cmd, max_rounds, images)
        return True, max_rounds, verify_cmd, cwd

    if user_input == "/clear":
        history.clear()
        console.print("  [dim]Conversation cleared.[/dim]")
        return True, max_rounds, verify_cmd, cwd

    if user_input.startswith("/rounds "):
        try:
            max_rounds = int(user_input.split()[1])
            console.print(f"  [dim]Max rounds set to {max_rounds}[/dim]")
        except ValueError:
            console.print("  [red]Usage: /rounds <number>[/red]")
        return True, max_rounds, verify_cmd, cwd

    if user_input == "/verify" or user_input.startswith("/verify "):
        verify_cmd = user_input[7:].strip() or None
        console.print(f"  [dim]Verify: {verify_cmd or '(auto-detect)'}[/dim]")
        return True, max_rounds, verify_cmd, cwd

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
        return True, max_rounds, verify_cmd, cwd

    if user_input.startswith("/image "):
        for raw in user_input[7:].strip().split():
            resolved = resolve_image_path(raw, cwd)
            if resolved:
                images.append(resolved)
                console.print(f"  [dim]Attached: {resolved}[/dim]")
        return True, max_rounds, verify_cmd, cwd

    if user_input == "/images":
        if images:
            for img in images:
                console.print(f"  [dim]{img}[/dim]")
        else:
            console.print("  [dim]No images attached.[/dim]")
        return True, max_rounds, verify_cmd, cwd

    if user_input == "/clearimages":
        images.clear()
        console.print("  [dim]Images cleared.[/dim]")
        return True, max_rounds, verify_cmd, cwd

    if user_input.startswith("/"):
        console.print("  [yellow]Unknown command. Type /help[/yellow]")
        return True, max_rounds, verify_cmd, cwd

    return False, max_rounds, verify_cmd, cwd


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    if os.environ.get("CLAUDECODE"):
        console.print("[yellow]Warning: Running inside a Claude Code session.\nclaude -p may not work. Run this directly in your terminal.[/yellow]")

    claude_ok = find_cli("claude") is not None
    codex_ok = find_cli("codex") is not None

    print_banner()

    cwd = os.getcwd()
    verify_cmd = detect_verify_command(cwd)
    max_rounds = MAX_ROUNDS
    history: list[tuple[str, str]] = []
    images: list[str] = []

    print_status(claude_ok, codex_ok, cwd, verify_cmd, max_rounds, images)

    if not claude_ok:
        console.print("\n[red bold]Error: Claude CLI required for Team Leader. Install claude.[/red bold]")
        sys.exit(1)

    console.print()

    while True:
        try:
            user_input = console.input("[bold white]Director > [/bold white]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        is_cmd, max_rounds, verify_cmd, cwd = handle_command(
            user_input, max_rounds, verify_cmd, images, cwd,
            history, claude_ok, codex_ok,
        )
        if is_cmd:
            continue

        total_start = time.time()
        history.append(("user", user_input))

        try:
            run_task(
                user_input, cwd, claude_ok, codex_ok,
                history, images, verify_cmd, max_rounds,
            )
        except KeyboardInterrupt:
            console.print(f"\n[yellow]Task interrupted.[/yellow]")

        console.print(f"\n[dim]Total: {elapsed_str(total_start)}[/dim]")

        if images:
            images.clear()


if __name__ == "__main__":
    main()
