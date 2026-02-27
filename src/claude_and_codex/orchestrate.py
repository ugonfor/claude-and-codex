"""Orchestrator that runs actual claude and codex CLI tools as subprocesses.

Protocol:
1. User gives a task
2. Claude works on it (full auto, no permission prompts)
3. Self-verify: run tests/checks, fix errors in a loop
4. Codex reviews Claude's work
5. If issues: debate and fix, then re-verify
6. Only present polished, verified results to user

Usage: python -m claude_and_codex.orchestrate
  (must be run outside of claude/codex sessions)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ── ANSI colors ──────────────────────────────────────────────────────────────

MAGENTA = "\033[35m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
WHITE = "\033[37m"
CYAN = "\033[36m"
RED = "\033[31m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# ── Constants ────────────────────────────────────────────────────────────────

MAX_VERIFY_RETRIES = 3
MAX_DEBATE_ROUNDS = 3


# ── Helpers ──────────────────────────────────────────────────────────────────


def find_cli(name: str) -> str | None:
    """Find a CLI tool on PATH."""
    return shutil.which(name)


def is_lgtm(text: str) -> bool:
    """Check whether a review response indicates approval."""
    upper = text.upper()
    lower = text.lower()
    return "LGTM" in upper or "looks good" in lower


def build_context(history: list[tuple[str, str]], max_entries: int = 10) -> str:
    """Build conversation context string from history."""
    labels = {"user": "User", "claude": "Claude", "codex": "Codex"}
    parts: list[str] = []
    for role, content in history[-max_entries:]:
        label = labels.get(role, role)
        truncated = content[:2000] + "..." if len(content) > 2000 else content
        parts.append(f"[{label}]: {truncated}")
    return "\n\n".join(parts)


# ── CLI runners ──────────────────────────────────────────────────────────────


def run_cli(
    name: str,
    args: list[str],
    cwd: str,
    timeout: int = 600,
    env_overrides: dict[str, str | None] | None = None,
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
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n[stderr: {result.stderr.strip()[:500]}]"
        return output or f"[No output from {name}]"
    except subprocess.TimeoutExpired:
        return f"[Error: {name} timed out after {timeout}s]"
    except Exception as e:
        return f"[Error running {name}: {e}]"


def run_claude(prompt: str, cwd: str, timeout: int = 600) -> str:
    """Run claude in print mode with full auto permissions."""
    claude_bin = find_cli("claude")
    if not claude_bin:
        return "[Error: claude CLI not found on PATH]"

    return run_cli(
        name="Claude",
        args=[claude_bin, "-p", "--dangerously-skip-permissions", prompt],
        cwd=cwd,
        timeout=timeout,
        env_overrides={"CLAUDECODE": None},
    )


def run_codex(prompt: str, cwd: str, timeout: int = 600) -> str:
    """Run codex exec in full-auto mode."""
    codex_bin = find_cli("codex")
    if not codex_bin:
        return "[Error: codex CLI not found on PATH]"

    return run_cli(
        name="Codex",
        args=[codex_bin, "exec", "--full-auto", prompt],
        cwd=cwd,
        timeout=timeout,
    )


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
            timeout=120,
            cwd=cwd,
        )
        output = (result.stdout + result.stderr).strip()
        passed = result.returncode == 0
        return passed, output[:3000]
    except subprocess.TimeoutExpired:
        return False, "Verification timed out after 120s"
    except Exception as e:
        return False, f"Verification error: {e}"


# ── Display helpers ──────────────────────────────────────────────────────────


def print_banner() -> None:
    print(f"""
{BOLD}+==========================================+
|         claude-and-codex  v0.4           |
|   Claude Code + Codex CLI orchestrator   |
+=========================================={RESET}

{DIM}Protocol: work -> verify -> review -> debate -> present
Both agents run in full-auto mode. Results are self-verified.
Only verified, reviewed output is presented to you.

Commands: /quit, /turns <n>, /verify <cmd>{RESET}
""")


def print_agent(name: str, color: str, text: str) -> None:
    border = "=" * (len(name) + 6)
    print(f"\n{BOLD}{color}=== {name} ==={RESET}")
    print(f"{color}{text}{RESET}")
    print(f"{BOLD}{color}{border}{RESET}")


def print_phase(phase: str) -> None:
    print(f"\n{DIM}{CYAN}[{phase}]{RESET}")


# ── Protocol phases ──────────────────────────────────────────────────────────


def phase_claude_work(
    user_context: str,
    cwd: str,
    claude_ok: bool,
    history: list[tuple[str, str]],
) -> str:
    """Phase 1: Claude works on the task."""
    print_phase("Phase 1: Claude working on task")

    prompt = (
        "You are Claude Code, working on a coding task. "
        "Another AI (Codex) will review your work after you're done. "
        "Do the work thoroughly -- write code, make changes, fix issues. "
        "Do NOT ask the user for clarification. Figure it out yourself.\n\n"
        f"Conversation:\n{user_context}"
    )

    response = run_claude(prompt, cwd) if claude_ok else "[Claude unavailable]"
    print_agent("Claude", MAGENTA, response)
    history.append(("claude", response))
    return response


def phase_self_verify(
    cwd: str,
    verify_cmd: str | None,
    claude_ok: bool,
    history: list[tuple[str, str]],
) -> bool:
    """Phase 2: Run verification and attempt fixes if it fails."""
    print_phase("Phase 2: Self-verification")
    passed, verify_output = run_verify(cwd, verify_cmd)

    if passed:
        print(f"  {GREEN}Verification passed.{RESET}")
        return True

    print(f"  {RED}Verification failed. Entering fix loop...{RESET}")

    for attempt in range(1, MAX_VERIFY_RETRIES + 1):
        print_phase(f"Phase 2: Fix attempt {attempt}/{MAX_VERIFY_RETRIES}")

        fix_prompt = (
            "Your previous work produced verification errors. "
            "Fix them. Here are the errors:\n\n"
            f"```\n{verify_output}\n```\n\n"
            "Fix all errors. Do NOT ask the user for help."
        )

        fix_resp = run_claude(fix_prompt, cwd) if claude_ok else "[Claude unavailable]"
        print(f"  {DIM}Claude fixing...{RESET}")
        history.append(("claude", f"[fix attempt {attempt}]: {fix_resp}"))

        passed, verify_output = run_verify(cwd, verify_cmd)
        if passed:
            print(f"  {GREEN}Verification passed after fix.{RESET}")
            return True

        print(f"  {RED}Still failing.{RESET}")

    print(f"  {YELLOW}Could not fix after {MAX_VERIFY_RETRIES} attempts.{RESET}")
    return False


def phase_codex_review(
    cwd: str,
    passed: bool,
    codex_ok: bool,
    history: list[tuple[str, str]],
) -> str:
    """Phase 3: Codex reviews Claude's work."""
    print_phase("Phase 3: Codex reviewing Claude's work")
    context = build_context(history)

    prompt = (
        "You are Codex, reviewing Claude's work on a coding task. "
        f"Claude has already made changes. Verification {'passed' if passed else 'FAILED'}.\n\n"
        "Your job:\n"
        "1. Check if the work correctly addresses the user's request\n"
        "2. Look for bugs, edge cases, or missing requirements\n"
        "3. If everything looks good, say 'LGTM' and summarize what was done\n"
        "4. If there are issues, describe them clearly so Claude can fix them\n"
        "5. Do NOT ask the user anything. Decide yourself.\n\n"
        f"Conversation:\n{context}"
    )

    review = run_codex(prompt, cwd) if codex_ok else "LGTM"
    history.append(("codex", review))
    return review


def phase_debate(
    cwd: str,
    codex_review: str,
    verify_cmd: str | None,
    max_rounds: int,
    claude_ok: bool,
    codex_ok: bool,
    history: list[tuple[str, str]],
) -> None:
    """Phase 4: Debate between Claude and Codex until agreement or round limit."""
    latest_review = codex_review

    for round_num in range(1, max_rounds + 1):
        print_phase(f"Phase 4: Debate round {round_num}/{max_rounds}")

        # Claude addresses Codex's feedback
        context = build_context(history)
        claude_fix_prompt = (
            "Codex reviewed your work and found issues. "
            "Address their feedback. Fix the problems. "
            "Do NOT ask the user. Handle it yourself.\n\n"
            f"Codex's review:\n{latest_review}\n\n"
            f"Full conversation:\n{context}"
        )

        claude_resp = run_claude(claude_fix_prompt, cwd) if claude_ok else "PASS"
        history.append(("claude", claude_resp))

        if claude_resp.strip().upper() == "PASS":
            print(f"  {DIM}Claude passed.{RESET}")
            break

        print(f"  {DIM}Claude addressed feedback. Re-verifying...{RESET}")

        # Re-verify after fixes
        passed, verify_output = run_verify(cwd, verify_cmd)
        if not passed:
            print(f"  {RED}Verification failed after fix. Auto-fixing...{RESET}")
            fix_resp = (
                run_claude(
                    f"Verification failed after your fix:\n```\n{verify_output}\n```\nFix it.",
                    cwd,
                )
                if claude_ok
                else "[unavailable]"
            )
            history.append(("claude", f"[auto-fix]: {fix_resp}"))
            passed, _ = run_verify(cwd, verify_cmd)

        # Codex re-reviews
        context = build_context(history)
        re_review_prompt = (
            "Claude addressed your feedback. "
            f"Verification {'passed' if passed else 'FAILED'}. "
            "Re-review. If satisfied, say 'LGTM'. Otherwise, describe remaining issues. "
            "Do NOT ask the user.\n\n"
            f"Conversation:\n{context}"
        )

        latest_review = run_codex(re_review_prompt, cwd) if codex_ok else "LGTM"
        history.append(("codex", latest_review))

        if is_lgtm(latest_review):
            print_agent("Codex", GREEN, latest_review)
            print(f"\n{BOLD}{CYAN}Both agents agree. Work complete.{RESET}")
            break

        print_agent("Codex (re-review)", GREEN, latest_review)
    else:
        print(f"\n{YELLOW}Debate ended after {max_rounds} rounds.{RESET}")
        print_agent("Codex (final)", GREEN, latest_review)


# ── Command handling ─────────────────────────────────────────────────────────


def handle_command(
    user_input: str,
    max_debate_rounds: int,
    verify_cmd: str | None,
) -> tuple[bool, int, str | None]:
    """Handle slash commands. Returns (should_continue, max_debate_rounds, verify_cmd).

    Returns should_continue=True if the input was a command (caller should
    skip to the next input), False if it was not a command.
    """
    if user_input == "/quit":
        print(f"{DIM}Goodbye!{RESET}")
        sys.exit(0)

    if user_input.startswith("/turns "):
        try:
            max_debate_rounds = int(user_input.split()[1])
            print(f"{DIM}Debate rounds set to {max_debate_rounds}{RESET}")
        except ValueError:
            print(f"{DIM}Usage: /turns <number>{RESET}")
        return True, max_debate_rounds, verify_cmd

    if user_input.startswith("/verify "):
        verify_cmd = user_input[8:].strip() or None
        if verify_cmd:
            print(f"{DIM}Verify command set to: {verify_cmd}{RESET}")
        else:
            print(f"{DIM}Verify command cleared.{RESET}")
        return True, max_debate_rounds, verify_cmd

    return False, max_debate_rounds, verify_cmd


# ── Main loop ────────────────────────────────────────────────────────────────


def main() -> None:
    # Check we're not inside a claude/codex session
    if os.environ.get("CLAUDECODE"):
        print(f"{YELLOW}Warning: Running inside a Claude Code session.")
        print(f"claude -p may not work. Run this script directly in your terminal.{RESET}")

    # Check CLI tools exist
    claude_ok = find_cli("claude") is not None
    codex_ok = find_cli("codex") is not None
    print_banner()
    print(f"  Claude CLI: {'found' if claude_ok else 'not found'}")
    print(f"  Codex CLI:  {'found' if codex_ok else 'not found'}")

    if not claude_ok and not codex_ok:
        print(f"{RED}Error: Neither claude nor codex CLI found. Install them first.{RESET}")
        sys.exit(1)

    cwd = os.getcwd()
    verify_cmd = detect_verify_command(cwd)
    max_debate_rounds = MAX_DEBATE_ROUNDS
    conversation_history: list[tuple[str, str]] = []

    if verify_cmd:
        print(f"  Verify cmd: {verify_cmd}")
    else:
        print(f"  Verify cmd: (none detected -- use /verify to set)")
    print()

    while True:
        try:
            user_input = input(f"\n{BOLD}{WHITE}You > {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}Goodbye!{RESET}")
            break

        if not user_input:
            continue

        # Slash commands
        is_cmd, max_debate_rounds, verify_cmd = handle_command(
            user_input, max_debate_rounds, verify_cmd,
        )
        if is_cmd:
            continue

        # ── Run the protocol ──
        conversation_history.append(("user", user_input))
        context = build_context(conversation_history)

        # Phase 1: Claude works on the task
        phase_claude_work(context, cwd, claude_ok, conversation_history)

        # Phase 2: Self-verify (with fix loop)
        passed = phase_self_verify(cwd, verify_cmd, claude_ok, conversation_history)

        # Phase 3: Codex reviews
        codex_review = phase_codex_review(cwd, passed, codex_ok, conversation_history)

        # Phase 4: Debate if Codex found issues
        if is_lgtm(codex_review):
            print_agent("Codex", GREEN, codex_review)
            print(f"\n{BOLD}{CYAN}Both agents agree. Work complete.{RESET}")
        else:
            print_agent("Codex (review)", GREEN, codex_review)
            phase_debate(
                cwd, codex_review, verify_cmd, max_debate_rounds,
                claude_ok, codex_ok, conversation_history,
            )

        # Summary
        print(f"\n{DIM}{'=' * 50}{RESET}")
        print(f"{BOLD}Task complete. Review the changes above.{RESET}")


if __name__ == "__main__":
    main()
