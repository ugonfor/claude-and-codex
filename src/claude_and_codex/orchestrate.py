"""Orchestrator that runs actual claude and codex CLI tools as subprocesses.

Protocol:
1. User gives a task
2. Primary agent (Claude) works on it in full-auto mode
3. Self-verify: run tests/checks, fix errors in a loop
4. Second agent (Codex) reviews the work
5. If issues: debate and fix, then re-verify
6. Present polished, verified results to user

Graceful degradation:
- Both CLIs available: full work-verify-review-debate protocol
- Only Claude: work-verify-self_review (no cross-agent review)
- Only Codex: same as above but with Codex as primary

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

MAX_VERIFY_RETRIES = 3
MAX_DEBATE_ROUNDS = 3
CLI_TIMEOUT = 600  # 10 minutes per agent call
VERIFY_TIMEOUT = 120  # 2 minutes for test runs
PROMPT_MAX_CHARS = 50_000  # safety limit for prompt size
CODEX_ARG_LIMIT = 7500  # safe for Windows CreateProcess (~32K total command line)


# ── Helpers ──────────────────────────────────────────────────────────────────


def find_cli(name: str) -> str | None:
    """Find a CLI tool on PATH."""
    return shutil.which(name)


def is_lgtm(text: str | None) -> bool:
    """Check whether a review response indicates approval."""
    if not text:
        return False
    upper = text.upper()
    lower = text.lower()
    return "LGTM" in upper or "looks good" in lower


def is_error_response(text: str | None) -> bool:
    """Check if a response is an error message from an agent."""
    if not text:
        return True
    stripped = text.lstrip()
    return stripped.startswith("[Error") or stripped.startswith("[No output from")


def truncate(text: str, max_len: int = 2000) -> str:
    """Truncate text with an indicator."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n... ({len(text)} chars total)"


def build_context(history: list[tuple[str, str]], max_entries: int = 10) -> str:
    """Build conversation context string from history."""
    labels = {"user": "User", "claude": "Claude", "codex": "Codex"}
    parts: list[str] = []
    for role, content in history[-max_entries:]:
        label = labels.get(role, role)
        parts.append(f"[{label}]: {truncate(content)}")
    return "\n\n".join(parts)


def timestamp() -> str:
    """Return current time as HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")


def elapsed_str(start: float) -> str:
    """Format elapsed time since *start* (time.time())."""
    secs = time.time() - start
    if secs < 60:
        return f"{secs:.1f}s"
    mins = int(secs // 60)
    remaining = secs % 60
    return f"{mins}m{remaining:.0f}s"


# ── CLI runners ──────────────────────────────────────────────────────────────


def run_cli(
    name: str,
    args: list[str],
    cwd: str,
    timeout: int = CLI_TIMEOUT,
    env_overrides: dict[str, str | None] | None = None,
    stdin_text: str | None = None,
) -> str:
    """Run a CLI tool as a subprocess and return its stdout.

    Parameters
    ----------
    name:
        Human-readable name used in error messages (e.g. "Claude", "Codex").
    args:
        Full argument list including the binary path.
    cwd:
        Working directory for the subprocess.
    timeout:
        Maximum seconds to wait before killing the process.
    env_overrides:
        Optional dict of env-var mutations. A value of ``None`` deletes the key.
    stdin_text:
        Optional text to pipe through stdin.  Avoids OS command-line length
        limits on Windows (~8 KB for cmd.exe, ~32 KB for CreateProcess).
    """
    env = os.environ.copy()
    for key, value in (env_overrides or {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value

    try:
        result = subprocess.run(
            args,
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
            encoding="utf-8",
            errors="replace",
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        output = stdout.strip()
        if result.returncode != 0 and stderr.strip():
            output += f"\n[stderr: {stderr.strip()[:500]}]"
        return output or f"[No output from {name}]"
    except subprocess.TimeoutExpired:
        return f"[Error: {name} timed out after {timeout}s]"
    except FileNotFoundError:
        return f"[Error: {name} binary not found at {args[0]}]"
    except PermissionError:
        return f"[Error: Permission denied running {name}]"
    except Exception as e:
        return f"[Error running {name}: {type(e).__name__}: {e}]"


def run_claude(
    prompt: str,
    cwd: str,
    timeout: int = CLI_TIMEOUT,
    images: list[str] | None = None,
) -> str:
    """Run claude in print mode with full auto permissions.

    The prompt is piped via stdin so it is not subject to OS
    command-line length limits.
    """
    claude_bin = find_cli("claude")
    if not claude_bin:
        return "[Error: claude CLI not found on PATH]"

    full_prompt = prompt
    if images:
        image_refs = "\n".join(f"- {img}" for img in images)
        full_prompt += (
            f"\n\nThe following image files are attached. "
            f"Read and analyze them as needed:\n{image_refs}"
        )

    if len(full_prompt) > PROMPT_MAX_CHARS:
        full_prompt = full_prompt[:PROMPT_MAX_CHARS] + "\n[prompt truncated]"

    # -p without a trailing argument reads the prompt from stdin
    return run_cli(
        name="Claude",
        args=[claude_bin, "-p", "--dangerously-skip-permissions"],
        cwd=cwd,
        timeout=timeout,
        env_overrides={"CLAUDECODE": None},
        stdin_text=full_prompt,
    )


def run_codex(
    prompt: str,
    cwd: str,
    timeout: int = CLI_TIMEOUT,
    images: list[str] | None = None,
) -> str:
    """Run codex exec in full-auto mode.

    Short prompts are passed as a positional argument.  Long prompts are
    written to a temp file to avoid OS command-line length limits (Windows
    CreateProcess caps at ~32 KB for the entire command line).
    """
    codex_bin = find_cli("codex")
    if not codex_bin:
        return "[Error: codex CLI not found on PATH]"

    if len(prompt) > PROMPT_MAX_CHARS:
        prompt = prompt[:PROMPT_MAX_CHARS] + "\n[prompt truncated]"

    args = [codex_bin, "exec", "--full-auto"]
    for img in images or []:
        args.extend(["-i", img])

    # Long prompts go through a temp file to stay under OS arg limits
    if len(prompt) > CODEX_ARG_LIMIT:
        prompt_file = Path(cwd) / ".codex_prompt.tmp"
        try:
            prompt_file.write_text(prompt, encoding="utf-8")
            args.append(
                f"Read your full task from the file '{prompt_file}'. "
                f"Execute it. Delete the file when done."
            )
            return run_cli(name="Codex", args=args, cwd=cwd, timeout=timeout)
        finally:
            prompt_file.unlink(missing_ok=True)
    else:
        args.append(prompt)
        return run_cli(name="Codex", args=args, cwd=cwd, timeout=timeout)


# ── Verification ─────────────────────────────────────────────────────────────


def detect_verify_command(cwd: str) -> str | None:
    """Auto-detect the right verification command for the project."""
    p = Path(cwd)

    # Python
    if (p / "pyproject.toml").exists() or (p / "setup.py").exists():
        if (p / "tests").exists() or (p / "test").exists():
            return "python -m pytest -q 2>&1"

    # Node
    if (p / "package.json").exists():
        try:
            pkg = json.loads((p / "package.json").read_text())
            if "test" in pkg.get("scripts", {}):
                return "npm test 2>&1"
        except (json.JSONDecodeError, OSError):
            pass

    # Rust
    if (p / "Cargo.toml").exists():
        return "cargo test 2>&1"

    # Go
    if (p / "go.mod").exists():
        return "go test ./... 2>&1"

    return None


def run_verify(cwd: str, verify_cmd: str | None = None) -> tuple[bool, str]:
    """Run verification (tests/build) and return (passed, output)."""
    cmd = verify_cmd or detect_verify_command(cwd)
    if cmd is None:
        return True, "(no verification command detected -- skipping)"

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=VERIFY_TIMEOUT,
            cwd=cwd,
            encoding="utf-8",
            errors="replace",
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        output = (stdout + stderr).strip()
        return result.returncode == 0, output[:3000]
    except subprocess.TimeoutExpired:
        return False, f"Verification timed out after {VERIFY_TIMEOUT}s"
    except Exception as e:
        return False, f"Verification error: {e}"


# ── Display helpers ──────────────────────────────────────────────────────────


HELP_TEXT = f"""\
{BOLD}Commands:{RESET}
  /help              Show this help message
  /quit              Exit the orchestrator
  /status            Show current configuration
  /clear             Clear conversation history
  /turns <n>         Set max debate rounds (default: {MAX_DEBATE_ROUNDS})
  /verify <cmd>      Set verification command (empty to clear)
  /cd <path>         Change working directory
  /image <path>      Attach image(s) for next task
  /images            List attached images
  /clearimages       Remove all attached images
  /export [md|jsonl] Export conversation history
"""


def print_banner() -> None:
    print(f"""
{BOLD}+==========================================+
|         claude-and-codex  v0.4           |
|   Claude Code + Codex CLI orchestrator   |
+=========================================={RESET}

{DIM}Protocol: work -> verify -> review -> debate -> present
Both agents run in full-auto mode. Results are self-verified.
Type /help for available commands.{RESET}
""")


def print_agent(name: str, color: str, text: str) -> None:
    print(f"\n{BOLD}{color}=== {name} ==={RESET}")
    for line in text.split("\n"):
        print(f"{color}  {line}{RESET}")
    print(f"{BOLD}{color}{'=' * (len(name) + 6)}{RESET}")


def print_phase(phase: str) -> None:
    print(f"\n{DIM}{CYAN}[{timestamp()}] {phase}{RESET}")


def print_status(
    claude_ok: bool,
    codex_ok: bool,
    cwd: str,
    verify_cmd: str | None,
    max_debate_rounds: int,
    images: list[str],
) -> None:
    found = f"{GREEN}found{RESET}"
    missing = f"{RED}not found{RESET}"
    print(f"\n{BOLD}Status:{RESET}")
    print(f"  Working dir:   {cwd}")
    print(f"  Claude CLI:    {found if claude_ok else missing}")
    print(f"  Codex CLI:     {found if codex_ok else missing}")
    print(f"  Verify cmd:    {verify_cmd or '(auto-detect)'}")
    print(f"  Debate rounds: {max_debate_rounds}")
    print(f"  Images:        {len(images)} attached")


# ── Export ───────────────────────────────────────────────────────────────────


def export_conversation(
    history: list[tuple[str, str]],
    fmt: str,
    cwd: str,
) -> str | None:
    """Export conversation history to a file.  Returns the file path, or None."""
    if not history:
        print(f"  {YELLOW}No conversation to export.{RESET}")
        return None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        if fmt == "jsonl":
            path = Path(cwd) / f"conversation_{ts}.jsonl"
            with open(path, "w", encoding="utf-8") as f:
                for role, content in history:
                    json.dump({"role": role, "content": content}, f)
                    f.write("\n")
        elif fmt == "md":
            labels = {"user": "User", "claude": "Claude", "codex": "Codex"}
            path = Path(cwd) / f"conversation_{ts}.md"
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# Conversation Export - {ts}\n\n")
                for role, content in history:
                    label = labels.get(role, role)
                    f.write(f"## {label}\n\n{content}\n\n---\n\n")
        else:
            print(f"  {RED}Unknown format: {fmt}. Use 'md' or 'jsonl'.{RESET}")
            return None
    except OSError as e:
        print(f"  {RED}Export failed: {e}{RESET}")
        return None

    return str(path)


# ── Protocol phases ──────────────────────────────────────────────────────────


def phase_work(
    user_context: str,
    cwd: str,
    claude_ok: bool,
    codex_ok: bool,
    history: list[tuple[str, str]],
    images: list[str] | None = None,
) -> str:
    """Phase 1: Primary agent works on the task.

    Falls back to the other agent if the primary one returns an error.
    """
    start = time.time()

    if claude_ok:
        print_phase("Phase 1: Claude working on task...")
        prompt = (
            "You are Claude Code, working on a coding task. "
            "Another AI (Codex) will review your work after you're done. "
            "Do the work thoroughly -- write code, make changes, fix issues. "
            "Do NOT ask the user for clarification. Figure it out yourself.\n\n"
            f"Conversation:\n{user_context}"
        )
        response = run_claude(prompt, cwd, images=images)
        role = "claude"

        # Fallback: if Claude errored and Codex is available, try Codex
        if is_error_response(response) and codex_ok:
            print(f"  {YELLOW}Claude errored, falling back to Codex...{RESET}")
            response = run_codex(prompt, cwd, images=images)
            role = "codex"

    elif codex_ok:
        print_phase("Phase 1: Codex working on task (Claude unavailable)...")
        prompt = (
            "You are working on a coding task. Do the work thoroughly -- "
            "write code, make changes, fix issues. "
            "Do NOT ask the user for clarification. Figure it out yourself.\n\n"
            f"Conversation:\n{user_context}"
        )
        response = run_codex(prompt, cwd, images=images)
        role = "codex"
    else:
        response = "[Error: No CLI agents available]"
        role = "claude"

    print_agent(role.capitalize(), MAGENTA, response)
    print(f"  {DIM}({elapsed_str(start)}){RESET}")
    history.append((role, response))
    return response


def phase_verify(
    cwd: str,
    verify_cmd: str | None,
    claude_ok: bool,
    codex_ok: bool,
    history: list[tuple[str, str]],
) -> bool:
    """Phase 2: Run verification and attempt fixes if it fails."""
    start = time.time()
    print_phase("Phase 2: Self-verification")
    passed, verify_output = run_verify(cwd, verify_cmd)

    if passed:
        print(f"  {GREEN}Verification passed ({elapsed_str(start)}){RESET}")
        return True

    print(f"  {RED}Verification failed. Entering fix loop...{RESET}")

    for attempt in range(1, MAX_VERIFY_RETRIES + 1):
        print_phase(f"Fix attempt {attempt}/{MAX_VERIFY_RETRIES}")

        fix_prompt = (
            "Your previous work produced verification errors. "
            "Fix them. Here are the errors:\n\n"
            f"```\n{verify_output}\n```\n\n"
            "Fix all errors. Do NOT ask the user for help."
        )

        if claude_ok:
            fix_resp = run_claude(fix_prompt, cwd)
        elif codex_ok:
            fix_resp = run_codex(fix_prompt, cwd)
        else:
            fix_resp = "[No agent available to fix]"

        if is_error_response(fix_resp):
            print(f"  {YELLOW}Agent errored during fix. Skipping.{RESET}")
            break

        print(f"  {DIM}Fixing...{RESET}")
        history.append(("claude" if claude_ok else "codex", f"[fix attempt {attempt}]: {fix_resp}"))

        passed, verify_output = run_verify(cwd, verify_cmd)
        if passed:
            print(f"  {GREEN}Verification passed after fix ({elapsed_str(start)}){RESET}")
            return True

        print(f"  {RED}Still failing.{RESET}")

    print(f"  {YELLOW}Could not fix after {MAX_VERIFY_RETRIES} attempts ({elapsed_str(start)}){RESET}")
    return False


def phase_review(
    cwd: str,
    passed: bool,
    claude_ok: bool,
    codex_ok: bool,
    history: list[tuple[str, str]],
    images: list[str] | None = None,
) -> str:
    """Phase 3: Second agent reviews the first agent's work."""
    start = time.time()
    context = build_context(history)

    review_prompt = (
        "You are reviewing another AI's work on a coding task. "
        f"Verification {'passed' if passed else 'FAILED'}.\n\n"
        "Your job:\n"
        "1. Check if the work correctly addresses the user's request\n"
        "2. Look for bugs, edge cases, or missing requirements\n"
        "3. If everything looks good, say 'LGTM' and summarize what was done\n"
        "4. If there are issues, describe them clearly\n"
        "5. Do NOT ask the user anything. Decide yourself.\n\n"
        f"Conversation:\n{context}"
    )

    if codex_ok and claude_ok:
        # Normal path: Codex reviews Claude's work
        print_phase("Phase 3: Codex reviewing Claude's work...")
        review = run_codex(review_prompt, cwd, images=images)
        reviewer = "codex"
    elif claude_ok:
        # Only Claude available: self-review
        print_phase("Phase 3: Claude self-reviewing (no Codex)...")
        review = run_claude(review_prompt, cwd, images=images)
        reviewer = "claude"
    elif codex_ok:
        # Only Codex available: self-review
        print_phase("Phase 3: Codex self-reviewing (no Claude)...")
        review = run_codex(review_prompt, cwd, images=images)
        reviewer = "codex"
    else:
        review = "LGTM (no reviewer available)"
        reviewer = "claude"

    # If the reviewer errored, skip review gracefully
    if is_error_response(review):
        print(f"  {YELLOW}Reviewer errored. Skipping review.{RESET}")
        review = "LGTM (reviewer unavailable due to error)"

    print(f"  {DIM}({elapsed_str(start)}){RESET}")
    history.append((reviewer, review))
    return review


def phase_debate(
    cwd: str,
    review: str,
    verify_cmd: str | None,
    max_rounds: int,
    claude_ok: bool,
    codex_ok: bool,
    history: list[tuple[str, str]],
) -> None:
    """Phase 4: Debate between agents until agreement or round limit."""
    latest_review = review
    rounds_completed = 0

    for round_num in range(1, max_rounds + 1):
        start = time.time()
        rounds_completed = round_num
        print_phase(f"Phase 4: Debate round {round_num}/{max_rounds}")

        # Worker addresses reviewer's feedback
        context = build_context(history)
        fix_prompt = (
            "A reviewer found issues with your work. "
            "Address their feedback. Fix the problems. "
            "Do NOT ask the user. Handle it yourself.\n\n"
            f"Review feedback:\n{latest_review}\n\n"
            f"Full conversation:\n{context}"
        )

        if claude_ok:
            worker_resp = run_claude(fix_prompt, cwd)
        elif codex_ok:
            worker_resp = run_codex(fix_prompt, cwd)
        else:
            break

        history.append(("claude" if claude_ok else "codex", worker_resp))

        if is_error_response(worker_resp):
            print(f"  {YELLOW}Worker errored. Stopping debate.{RESET}")
            break

        if not worker_resp or worker_resp.strip().upper() == "PASS":
            print(f"  {DIM}Worker passed ({elapsed_str(start)}){RESET}")
            break

        print(f"  {DIM}Worker addressed feedback. Re-verifying...{RESET}")

        # Re-verify after fixes
        passed, verify_output = run_verify(cwd, verify_cmd)
        if not passed:
            print(f"  {RED}Verification failed after fix. Auto-fixing...{RESET}")
            fix_resp = None
            if claude_ok:
                fix_resp = run_claude(
                    f"Verification failed:\n```\n{verify_output}\n```\nFix it.",
                    cwd,
                )
                history.append(("claude", f"[auto-fix]: {fix_resp}"))
            elif codex_ok:
                fix_resp = run_codex(
                    f"Verification failed:\n```\n{verify_output}\n```\nFix it.",
                    cwd,
                )
                history.append(("codex", f"[auto-fix]: {fix_resp}"))
            if fix_resp and not is_error_response(fix_resp):
                passed, _ = run_verify(cwd, verify_cmd)

        # Reviewer re-reviews
        context = build_context(history)
        re_review_prompt = (
            "The worker addressed your feedback. "
            f"Verification {'passed' if passed else 'FAILED'}. "
            "Re-review. If satisfied, say 'LGTM'. Otherwise, describe remaining issues. "
            "Do NOT ask the user.\n\n"
            f"Conversation:\n{context}"
        )

        if codex_ok:
            latest_review = run_codex(re_review_prompt, cwd)
        elif claude_ok:
            latest_review = run_claude(re_review_prompt, cwd)
        else:
            latest_review = "LGTM"

        history.append(("codex" if codex_ok else "claude", latest_review))
        print(f"  {DIM}({elapsed_str(start)}){RESET}")

        if is_error_response(latest_review):
            print(f"  {YELLOW}Reviewer errored. Ending debate.{RESET}")
            break

        if is_lgtm(latest_review):
            print_agent("Reviewer", GREEN, latest_review)
            print(f"\n{BOLD}{CYAN}Both agents agree. Work complete.{RESET}")
            return

        print_agent("Reviewer (re-review)", YELLOW, latest_review)

    print(f"\n{YELLOW}Debate ended after {rounds_completed} round(s).{RESET}")
    print_agent("Reviewer (final)", YELLOW, latest_review)


def phase_present(history: list[tuple[str, str]], total_start: float) -> None:
    """Phase 5: Present a clean summary to the user."""
    print(f"\n{'=' * 52}")
    print(f"{BOLD}  Task Complete  ({elapsed_str(total_start)} total){RESET}")
    print(f"{'=' * 52}")

    # Show the last meaningful agent response as a summary
    for role, content in reversed(history):
        if role != "user" and not is_error_response(content):
            print(f"\n{DIM}Summary ({role}):{RESET}")
            print(truncate(content, 1000))
            break


# ── Command handling ─────────────────────────────────────────────────────────


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}


def resolve_image_path(path_str: str, cwd: str) -> str | None:
    """Resolve an image path to absolute, return None if invalid."""
    p = Path(path_str)
    if not p.is_absolute():
        p = (Path(cwd) / p).resolve()
    if not p.exists():
        print(f"  {RED}Image not found: {p}{RESET}")
        return None
    if p.suffix.lower() not in IMAGE_EXTENSIONS:
        print(f"  {YELLOW}Warning: {p.name} may not be an image{RESET}")
    return str(p)


def handle_command(
    user_input: str,
    max_debate_rounds: int,
    verify_cmd: str | None,
    images: list[str],
    cwd: str,
    history: list[tuple[str, str]],
    claude_ok: bool,
    codex_ok: bool,
) -> tuple[bool, int, str | None, str]:
    """Handle slash commands.

    Returns (is_command, max_debate_rounds, verify_cmd, cwd).
    *is_command* is True when the input was handled here and the main loop
    should skip to the next prompt.
    """
    if user_input == "/quit":
        print(f"{DIM}Goodbye!{RESET}")
        sys.exit(0)

    if user_input == "/help":
        print(HELP_TEXT)
        return True, max_debate_rounds, verify_cmd, cwd

    if user_input == "/status":
        print_status(claude_ok, codex_ok, cwd, verify_cmd, max_debate_rounds, images)
        return True, max_debate_rounds, verify_cmd, cwd

    if user_input == "/clear":
        history.clear()
        print(f"  {DIM}Conversation cleared.{RESET}")
        return True, max_debate_rounds, verify_cmd, cwd

    if user_input.startswith("/turns "):
        try:
            max_debate_rounds = int(user_input.split()[1])
            print(f"  {DIM}Debate rounds set to {max_debate_rounds}{RESET}")
        except ValueError:
            print(f"  {RED}Usage: /turns <number>{RESET}")
        return True, max_debate_rounds, verify_cmd, cwd

    if user_input == "/verify" or user_input.startswith("/verify "):
        arg = user_input[7:].strip()
        verify_cmd = arg or None
        print(f"  {DIM}Verify command: {verify_cmd or '(auto-detect)'}{RESET}")
        return True, max_debate_rounds, verify_cmd, cwd

    if user_input.startswith("/cd "):
        new_dir = user_input[4:].strip()
        target = Path(new_dir)
        if not target.is_absolute():
            target = (Path(cwd) / target).resolve()
        if target.is_dir():
            cwd = str(target)
            verify_cmd = detect_verify_command(cwd)
            print(f"  {DIM}Working directory: {cwd}{RESET}")
            if verify_cmd:
                print(f"  {DIM}Auto-detected verify: {verify_cmd}{RESET}")
        else:
            print(f"  {RED}Not a directory: {target}{RESET}")
        return True, max_debate_rounds, verify_cmd, cwd

    if user_input.startswith("/export"):
        parts = user_input.split()
        fmt = parts[1] if len(parts) > 1 else "md"
        if fmt == "both":
            for f in ("md", "jsonl"):
                path = export_conversation(history, f, cwd)
                if path:
                    print(f"  {GREEN}Exported: {path}{RESET}")
        else:
            path = export_conversation(history, fmt, cwd)
            if path:
                print(f"  {GREEN}Exported: {path}{RESET}")
        return True, max_debate_rounds, verify_cmd, cwd

    if user_input.startswith("/image "):
        paths = user_input[7:].strip().split()
        for raw in paths:
            resolved = resolve_image_path(raw, cwd)
            if resolved:
                images.append(resolved)
                print(f"  {DIM}Attached: {resolved}{RESET}")
        if images:
            print(f"  {DIM}Total images: {len(images)}{RESET}")
        return True, max_debate_rounds, verify_cmd, cwd

    if user_input == "/images":
        if images:
            for img in images:
                print(f"  {DIM}{img}{RESET}")
        else:
            print(f"  {DIM}No images. Use /image <path> to add.{RESET}")
        return True, max_debate_rounds, verify_cmd, cwd

    if user_input == "/clearimages":
        images.clear()
        print(f"  {DIM}Images cleared.{RESET}")
        return True, max_debate_rounds, verify_cmd, cwd

    # Catch-all for unknown slash commands
    if user_input.startswith("/"):
        print(f"  {YELLOW}Unknown command: {user_input.split()[0]}. Type /help{RESET}")
        return True, max_debate_rounds, verify_cmd, cwd

    return False, max_debate_rounds, verify_cmd, cwd


# ── Main loop ────────────────────────────────────────────────────────────────


def main() -> None:
    # Check we're not inside a claude/codex session
    if os.environ.get("CLAUDECODE"):
        print(f"{YELLOW}Warning: Running inside a Claude Code session.")
        print(f"claude -p may not work. Run this script directly in your terminal.{RESET}")

    claude_ok = find_cli("claude") is not None
    codex_ok = find_cli("codex") is not None

    print_banner()

    cwd = os.getcwd()
    verify_cmd = detect_verify_command(cwd)
    max_debate_rounds = MAX_DEBATE_ROUNDS
    history: list[tuple[str, str]] = []
    images: list[str] = []

    print_status(claude_ok, codex_ok, cwd, verify_cmd, max_debate_rounds, images)

    if not claude_ok and not codex_ok:
        print(f"\n{RED}Error: Neither claude nor codex CLI found. Install at least one.{RESET}")
        sys.exit(1)

    if not claude_ok:
        print(f"\n{YELLOW}Note: Claude CLI not found. Running in Codex-only mode.{RESET}")
    elif not codex_ok:
        print(f"\n{YELLOW}Note: Codex CLI not found. Running in Claude-only mode (no cross-review).{RESET}")

    print()

    while True:
        try:
            user_input = input(f"{BOLD}{WHITE}You > {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}Goodbye!{RESET}")
            break

        if not user_input:
            continue

        # Slash commands
        is_cmd, max_debate_rounds, verify_cmd, cwd = handle_command(
            user_input, max_debate_rounds, verify_cmd, images, cwd,
            history, claude_ok, codex_ok,
        )
        if is_cmd:
            continue

        # ── Run the full protocol ──
        total_start = time.time()
        history.append(("user", user_input))
        context = build_context(history)

        try:
            # Phase 1: Work
            phase_work(context, cwd, claude_ok, codex_ok, history, images=images)

            # Phase 2: Verify (with fix loop)
            passed = phase_verify(cwd, verify_cmd, claude_ok, codex_ok, history)

            # Phase 3: Review
            review = phase_review(cwd, passed, claude_ok, codex_ok, history, images=images)

            # Phase 4: Debate (only if reviewer found issues)
            if is_lgtm(review):
                print_agent("Reviewer", GREEN, review)
                print(f"\n{BOLD}{CYAN}Agents agree. Work complete.{RESET}")
            else:
                print_agent("Reviewer", YELLOW, review)
                phase_debate(
                    cwd, review, verify_cmd, max_debate_rounds,
                    claude_ok, codex_ok, history,
                )

            # Phase 5: Present
            phase_present(history, total_start)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Task interrupted.{RESET}")

        # Clear images after each task
        if images:
            images.clear()
            print(f"{DIM}(Images cleared for next task){RESET}")


if __name__ == "__main__":
    main()
