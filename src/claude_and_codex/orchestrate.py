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

# ── ANSI colors (disabled for non-TTY) ──────────────────────────────────────

_IS_TTY = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

MAGENTA = "\033[35m" if _IS_TTY else ""
GREEN = "\033[32m" if _IS_TTY else ""
YELLOW = "\033[33m" if _IS_TTY else ""
WHITE = "\033[37m" if _IS_TTY else ""
CYAN = "\033[36m" if _IS_TTY else ""
RED = "\033[31m" if _IS_TTY else ""
BOLD = "\033[1m" if _IS_TTY else ""
DIM = "\033[2m" if _IS_TTY else ""
RESET = "\033[0m" if _IS_TTY else ""

# ── Constants ────────────────────────────────────────────────────────────────

MAX_TURNS = 12          # Max total agent turns per task
CLI_TIMEOUT = 600       # 10 min per agent call
VERIFY_TIMEOUT = 120    # 2 min for test runs
PROMPT_MAX_CHARS = 50_000
CODEX_ARG_LIMIT = 7500

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
    stripped = text.strip().upper()
    # Check if the response is just DONE or PASS (possibly with punctuation)
    if stripped in ("DONE", "PASS", "DONE.", "PASS."):
        return True
    # Also check if the last line says DONE
    last_line = text.strip().split("\n")[-1].strip().upper()
    return last_line in ("DONE", "PASS", "DONE.", "PASS.")


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
    env = os.environ.copy()
    for key, value in (env_overrides or {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value

    try:
        result = subprocess.run(
            args, input=stdin_text,
            capture_output=True, text=True, timeout=timeout,
            cwd=cwd, env=env, encoding="utf-8", errors="replace",
        )
        output = (result.stdout or "").strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n[stderr: {result.stderr.strip()[:500]}]"
        return output or f"[No output from {name}]"
    except subprocess.TimeoutExpired:
        return f"[Error: {name} timed out after {timeout}s]"
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


def print_agent(name: str, color: str, text: str, duration: str = "") -> None:
    suffix = f"  {DIM}({duration}){RESET}" if duration else ""
    print(f"\n{BOLD}{color}=== {name} ==={suffix}{RESET}")
    for line in text.split("\n"):
        print(f"{color}  {line}{RESET}")
    print(f"{BOLD}{color}{'=' * (len(name) + 6)}{RESET}")


def print_banner() -> None:
    print(f"""
{BOLD}+==========================================+
|         claude-and-codex  v0.5           |
|    Free-form AI collaboration engine     |
+=========================================={RESET}

{DIM}Both agents collaborate freely on your task.
No fixed workflow -- they decide what to do.
Type /help for commands.{RESET}
""")


HELP_TEXT = f"""\
{BOLD}Commands:{RESET}
  /help              Show this help
  /quit              Exit
  /status            Show configuration
  /clear             Clear conversation history
  /turns <n>         Set max turns per task (default: {MAX_TURNS})
  /verify <cmd>      Set verification command (empty = auto-detect)
  /cd <path>         Change working directory
  /image <path>      Attach image(s) for next task
  /images            List attached images
  /clearimages       Remove all attached images
"""


def print_status(claude_ok, codex_ok, cwd, verify_cmd, max_turns, images):
    found = f"{GREEN}found{RESET}"
    missing = f"{RED}not found{RESET}"
    print(f"\n{BOLD}Status:{RESET}")
    print(f"  Working dir: {cwd}")
    print(f"  Claude CLI:  {found if claude_ok else missing}")
    print(f"  Codex CLI:   {found if codex_ok else missing}")
    print(f"  Verify cmd:  {verify_cmd or '(auto-detect)'}")
    print(f"  Max turns:   {max_turns}")
    print(f"  Images:      {len(images)} attached")


# ── Image handling ───────────────────────────────────────────────────────────

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}


def resolve_image_path(path_str: str, cwd: str) -> str | None:
    p = Path(path_str)
    if not p.is_absolute():
        p = (Path(cwd) / p).resolve()
    if not p.exists():
        print(f"  {RED}Image not found: {p}{RESET}")
        return None
    if p.suffix.lower() not in IMAGE_EXTENSIONS:
        print(f"  {YELLOW}Warning: {p.name} may not be an image{RESET}")
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

    Both agents take turns. Each sees the full conversation and decides
    what to do. Loop ends when both signal DONE/PASS, or max turns reached.
    """
    agents = []
    if claude_ok:
        agents.append(("claude", "Claude", "Codex", MAGENTA, run_claude))
    if codex_ok:
        agents.append(("codex", "Codex", "Claude", GREEN, run_codex))

    if not agents:
        print(f"{RED}No agents available.{RESET}")
        return

    consecutive_done = 0
    turn = 0
    last_had_changes = False

    while turn < max_turns:
        # Alternate agents
        role, name, partner, color, runner = agents[turn % len(agents)]
        turn += 1

        context = build_context(history)
        system = COLLAB_SYSTEM.format(name=name, partner=partner)

        prompt = f"{system}\nConversation so far:\n{context}"

        # If verification failed last round, tell the agent
        if last_had_changes:
            passed, verify_output = run_verify(cwd, verify_cmd)
            if not passed:
                prompt += (
                    f"\n\n[System]: Verification FAILED after recent changes:\n"
                    f"```\n{verify_output}\n```\n"
                    f"Fix these errors."
                )
                history.append(("system", f"Verification failed:\n{verify_output}"))
            else:
                prompt += "\n\n[System]: Verification passed after recent changes."
                history.append(("system", "Verification passed."))
            last_had_changes = False

        print(f"\n{DIM}[{timestamp()}] {name}'s turn (#{turn})...{RESET}")
        start = time.time()

        # Only pass images on first turn for each agent
        img = images if turn <= len(agents) else None
        response = runner(prompt, cwd, images=img)
        duration = elapsed_str(start)

        if is_error(response):
            print(f"  {YELLOW}{name} errored: {response[:200]}{RESET}")
            history.append((role, response))
            # Don't count errors as DONE
            consecutive_done = 0
            continue

        print_agent(name, color, response, duration)
        history.append((role, response))

        # Check if agent signals completion
        if is_done_or_pass(response):
            consecutive_done += 1
            if consecutive_done >= len(agents):
                print(f"\n{BOLD}{CYAN}All agents agree: task complete.{RESET}")
                break
        else:
            consecutive_done = 0
            # Heuristic: if response mentions file operations, mark as having changes
            lower = response.lower()
            if any(kw in lower for kw in ["wrote", "created", "modified", "updated", "fixed", "changed", "edited"]):
                last_had_changes = True

    else:
        print(f"\n{YELLOW}Reached max turns ({max_turns}). Stopping.{RESET}")

    # Final verification
    passed, verify_output = run_verify(cwd, verify_cmd)
    if passed:
        print(f"\n{GREEN}Final verification: passed{RESET}")
    else:
        print(f"\n{RED}Final verification: FAILED{RESET}")
        print(f"{DIM}{verify_output[:500]}{RESET}")


# ── Command handling ─────────────────────────────────────────────────────────


def handle_command(
    user_input: str, max_turns: int, verify_cmd: str | None,
    images: list[str], cwd: str, history: list[tuple[str, str]],
    claude_ok: bool, codex_ok: bool,
) -> tuple[bool, int, str | None, str]:
    """Returns (is_command, max_turns, verify_cmd, cwd)."""

    if user_input == "/quit":
        print(f"{DIM}Goodbye!{RESET}")
        sys.exit(0)

    if user_input == "/help":
        print(HELP_TEXT)
        return True, max_turns, verify_cmd, cwd

    if user_input == "/status":
        print_status(claude_ok, codex_ok, cwd, verify_cmd, max_turns, images)
        return True, max_turns, verify_cmd, cwd

    if user_input == "/clear":
        history.clear()
        print(f"  {DIM}Conversation cleared.{RESET}")
        return True, max_turns, verify_cmd, cwd

    if user_input.startswith("/turns "):
        try:
            max_turns = int(user_input.split()[1])
            print(f"  {DIM}Max turns set to {max_turns}{RESET}")
        except ValueError:
            print(f"  {RED}Usage: /turns <number>{RESET}")
        return True, max_turns, verify_cmd, cwd

    if user_input == "/verify" or user_input.startswith("/verify "):
        verify_cmd = user_input[7:].strip() or None
        print(f"  {DIM}Verify: {verify_cmd or '(auto-detect)'}{RESET}")
        return True, max_turns, verify_cmd, cwd

    if user_input.startswith("/cd "):
        target = Path(user_input[4:].strip())
        if not target.is_absolute():
            target = (Path(cwd) / target).resolve()
        if target.is_dir():
            cwd = str(target)
            verify_cmd = detect_verify_command(cwd)
            print(f"  {DIM}Working dir: {cwd}{RESET}")
        else:
            print(f"  {RED}Not a directory: {target}{RESET}")
        return True, max_turns, verify_cmd, cwd

    if user_input.startswith("/image "):
        for raw in user_input[7:].strip().split():
            resolved = resolve_image_path(raw, cwd)
            if resolved:
                images.append(resolved)
                print(f"  {DIM}Attached: {resolved}{RESET}")
        return True, max_turns, verify_cmd, cwd

    if user_input == "/images":
        if images:
            for img in images:
                print(f"  {DIM}{img}{RESET}")
        else:
            print(f"  {DIM}No images attached.{RESET}")
        return True, max_turns, verify_cmd, cwd

    if user_input == "/clearimages":
        images.clear()
        print(f"  {DIM}Images cleared.{RESET}")
        return True, max_turns, verify_cmd, cwd

    if user_input.startswith("/"):
        print(f"  {YELLOW}Unknown command. Type /help{RESET}")
        return True, max_turns, verify_cmd, cwd

    return False, max_turns, verify_cmd, cwd


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    if os.environ.get("CLAUDECODE"):
        print(f"{YELLOW}Warning: Running inside a Claude Code session.")
        print(f"claude -p may not work. Run this directly in your terminal.{RESET}")

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
        print(f"\n{RED}Error: No CLI agents found. Install claude or codex.{RESET}")
        sys.exit(1)

    print()

    while True:
        try:
            user_input = input(f"{BOLD}{WHITE}You > {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}Goodbye!{RESET}")
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
            print(f"\n{YELLOW}Task interrupted.{RESET}")

        print(f"\n{DIM}Total: {elapsed_str(total_start)}{RESET}")

        if images:
            images.clear()


if __name__ == "__main__":
    main()
