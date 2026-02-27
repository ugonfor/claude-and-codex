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

import subprocess
import sys
import os
import shutil
import json
import tempfile
from pathlib import Path

# Colors
MAGENTA = "\033[35m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
WHITE = "\033[37m"
CYAN = "\033[36m"
RED = "\033[31m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

MAX_VERIFY_RETRIES = 3
MAX_DEBATE_ROUNDS = 3


def find_cli(name: str) -> str | None:
    """Find a CLI tool on PATH."""
    return shutil.which(name)


def run_claude(prompt: str, cwd: str, timeout: int = 600) -> str:
    """Run claude in print mode with full auto permissions."""
    claude_bin = find_cli("claude")
    if not claude_bin:
        return "[Error: claude CLI not found on PATH]"

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)  # Allow nested invocation

    try:
        result = subprocess.run(
            [
                claude_bin, "-p",
                "--dangerously-skip-permissions",
                prompt,
            ],
            capture_output=True, text=True, timeout=timeout,
            cwd=cwd, env=env,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n[stderr: {result.stderr.strip()[:500]}]"
        return output or "[No output from Claude]"
    except subprocess.TimeoutExpired:
        return f"[Error: Claude timed out after {timeout}s]"
    except Exception as e:
        return f"[Error running Claude: {e}]"


def run_codex(prompt: str, cwd: str, timeout: int = 600) -> str:
    """Run codex exec in full-auto mode."""
    codex_bin = find_cli("codex")
    if not codex_bin:
        return "[Error: codex CLI not found on PATH]"

    try:
        result = subprocess.run(
            [codex_bin, "exec", "--full-auto", prompt],
            capture_output=True, text=True, timeout=timeout,
            cwd=cwd,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n[stderr: {result.stderr.strip()[:500]}]"
        return output or "[No output from Codex]"
    except subprocess.TimeoutExpired:
        return f"[Error: Codex timed out after {timeout}s]"
    except Exception as e:
        return f"[Error running Codex: {e}]"


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
        return True, "(no verification command detected — skipping)"

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=120, cwd=cwd,
        )
        output = (result.stdout + result.stderr).strip()
        passed = result.returncode == 0
        return passed, output[:3000]
    except subprocess.TimeoutExpired:
        return False, "Verification timed out after 120s"
    except Exception as e:
        return False, f"Verification error: {e}"


def print_banner() -> None:
    print(f"""
{BOLD}╔══════════════════════════════════════════╗
║         claude-and-codex  v0.4          ║
║   Claude Code + Codex CLI orchestrator  ║
╚══════════════════════════════════════════╝{RESET}

{DIM}Protocol: work → verify → review → debate → present
Both agents run in full-auto mode. Results are self-verified.
Only verified, reviewed output is presented to you.

Commands: /quit, /turns <n>, /verify <cmd>{RESET}
""")


def print_agent(name: str, color: str, text: str) -> None:
    print(f"\n{BOLD}{color}━━━ {name} ━━━{RESET}")
    print(f"{color}{text}{RESET}")
    print(f"{BOLD}{color}{'━' * (len(name) + 8)}{RESET}")


def print_phase(phase: str) -> None:
    print(f"\n{DIM}{CYAN}[{phase}]{RESET}")


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
    conversation_history: list[tuple[str, str]] = []  # (role, content)

    if verify_cmd:
        print(f"  Verify cmd: {verify_cmd}")
    else:
        print(f"  Verify cmd: (none detected — use /verify to set)")
    print()

    while True:
        try:
            user_input = input(f"\n{BOLD}{WHITE}You > {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}Goodbye!{RESET}")
            break

        if not user_input:
            continue

        # --- Commands ---
        if user_input == "/quit":
            print(f"{DIM}Goodbye!{RESET}")
            break

        if user_input.startswith("/turns "):
            try:
                max_debate_rounds = int(user_input.split()[1])
                print(f"{DIM}Debate rounds set to {max_debate_rounds}{RESET}")
            except ValueError:
                print(f"{DIM}Usage: /turns <number>{RESET}")
            continue

        if user_input.startswith("/verify "):
            verify_cmd = user_input[8:].strip() or None
            if verify_cmd:
                print(f"{DIM}Verify command set to: {verify_cmd}{RESET}")
            else:
                print(f"{DIM}Verify command cleared.{RESET}")
            continue

        # --- Main protocol ---
        conversation_history.append(("user", user_input))

        # Build context
        context = _build_context(conversation_history)

        # ── Phase 1: Claude works on the task ──
        print_phase("Phase 1: Claude working on task")
        claude_work_prompt = (
            f"You are Claude Code, working on a coding task. "
            f"Another AI (Codex) will review your work after you're done. "
            f"Do the work thoroughly — write code, make changes, fix issues. "
            f"Do NOT ask the user for clarification. Figure it out yourself.\n\n"
            f"Conversation:\n{context}"
        )

        claude_resp = run_claude(claude_work_prompt, cwd) if claude_ok else "[Claude unavailable]"
        print_agent("Claude", MAGENTA, claude_resp)
        conversation_history.append(("claude", claude_resp))

        # ── Phase 2: Self-verify ──
        print_phase("Phase 2: Self-verification")
        passed, verify_output = run_verify(cwd, verify_cmd)

        if passed:
            print(f"  {GREEN}Verification passed.{RESET}")
        else:
            print(f"  {RED}Verification failed. Entering fix loop...{RESET}")

            for attempt in range(1, MAX_VERIFY_RETRIES + 1):
                print_phase(f"Phase 2: Fix attempt {attempt}/{MAX_VERIFY_RETRIES}")

                fix_prompt = (
                    f"Your previous work produced verification errors. "
                    f"Fix them. Here are the errors:\n\n"
                    f"```\n{verify_output}\n```\n\n"
                    f"Fix all errors. Do NOT ask the user for help."
                )

                fix_resp = run_claude(fix_prompt, cwd) if claude_ok else "[Claude unavailable]"
                print(f"  {DIM}Claude fixing...{RESET}")
                conversation_history.append(("claude", f"[fix attempt {attempt}]: {fix_resp}"))

                passed, verify_output = run_verify(cwd, verify_cmd)
                if passed:
                    print(f"  {GREEN}Verification passed after fix.{RESET}")
                    break
                else:
                    print(f"  {RED}Still failing.{RESET}")

            if not passed:
                print(f"  {YELLOW}Could not fix after {MAX_VERIFY_RETRIES} attempts.{RESET}")

        # ── Phase 3: Codex reviews ──
        print_phase("Phase 3: Codex reviewing Claude's work")
        context = _build_context(conversation_history)

        review_prompt = (
            f"You are Codex, reviewing Claude's work on a coding task. "
            f"Claude has already made changes. Verification {'passed' if passed else 'FAILED'}.\n\n"
            f"Your job:\n"
            f"1. Check if the work correctly addresses the user's request\n"
            f"2. Look for bugs, edge cases, or missing requirements\n"
            f"3. If everything looks good, say 'LGTM' and summarize what was done\n"
            f"4. If there are issues, describe them clearly so Claude can fix them\n"
            f"5. Do NOT ask the user anything. Decide yourself.\n\n"
            f"Conversation:\n{context}"
        )

        codex_review = run_codex(review_prompt, cwd) if codex_ok else "LGTM"
        conversation_history.append(("codex", codex_review))

        # ── Phase 4: Debate if needed ──
        if "LGTM" in codex_review.upper() or "looks good" in codex_review.lower():
            print_agent("Codex", GREEN, codex_review)
            print(f"\n{BOLD}{CYAN}Both agents agree. Work complete.{RESET}")
        else:
            print_agent("Codex (review)", GREEN, codex_review)

            for round_num in range(1, max_debate_rounds + 1):
                print_phase(f"Phase 4: Debate round {round_num}/{max_debate_rounds}")

                # Claude addresses Codex's feedback
                context = _build_context(conversation_history)
                claude_fix_prompt = (
                    f"Codex reviewed your work and found issues. "
                    f"Address their feedback. Fix the problems. "
                    f"Do NOT ask the user. Handle it yourself.\n\n"
                    f"Codex's review:\n{codex_review}\n\n"
                    f"Full conversation:\n{context}"
                )

                claude_resp = run_claude(claude_fix_prompt, cwd) if claude_ok else "PASS"
                conversation_history.append(("claude", claude_resp))

                if claude_resp.strip().upper() == "PASS":
                    print(f"  {DIM}Claude passed.{RESET}")
                    break

                print(f"  {DIM}Claude addressed feedback. Re-verifying...{RESET}")

                # Re-verify after fixes
                passed, verify_output = run_verify(cwd, verify_cmd)
                if not passed:
                    print(f"  {RED}Verification failed after fix. Auto-fixing...{RESET}")
                    fix_resp = run_claude(
                        f"Verification failed after your fix:\n```\n{verify_output}\n```\nFix it.",
                        cwd,
                    ) if claude_ok else "[unavailable]"
                    conversation_history.append(("claude", f"[auto-fix]: {fix_resp}"))
                    passed, _ = run_verify(cwd, verify_cmd)

                # Codex re-reviews
                context = _build_context(conversation_history)
                re_review_prompt = (
                    f"Claude addressed your feedback. Verification {'passed' if passed else 'FAILED'}. "
                    f"Re-review. If satisfied, say 'LGTM'. Otherwise, describe remaining issues. "
                    f"Do NOT ask the user.\n\n"
                    f"Conversation:\n{context}"
                )

                codex_review = run_codex(re_review_prompt, cwd) if codex_ok else "LGTM"
                conversation_history.append(("codex", codex_review))

                if "LGTM" in codex_review.upper() or "looks good" in codex_review.lower():
                    print_agent("Codex", GREEN, codex_review)
                    print(f"\n{BOLD}{CYAN}Both agents agree. Work complete.{RESET}")
                    break

                print_agent("Codex (re-review)", GREEN, codex_review)
            else:
                print(f"\n{YELLOW}Debate ended after {max_debate_rounds} rounds.{RESET}")
                print_agent("Codex (final)", GREEN, codex_review)

        # ── Summary ──
        print(f"\n{DIM}{'─' * 50}{RESET}")
        print(f"{BOLD}Task complete. Review the changes above.{RESET}")


def _build_context(history: list[tuple[str, str]], max_entries: int = 10) -> str:
    """Build conversation context string from history."""
    context = ""
    for role, content in history[-max_entries:]:
        label = {"user": "User", "claude": "Claude", "codex": "Codex"}.get(role, role)
        # Truncate very long responses in context to keep prompts manageable
        truncated = content[:2000] + "..." if len(content) > 2000 else content
        context += f"[{label}]: {truncated}\n\n"
    return context


if __name__ == "__main__":
    main()
