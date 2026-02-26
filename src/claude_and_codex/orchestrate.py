"""Orchestrator that runs actual claude and codex CLI tools as subprocesses.

Usage: .venv/bin/python -m claude_and_codex.orchestrate
  (must be run outside of claude/codex sessions)
"""

from __future__ import annotations

import subprocess
import sys
import os
import shutil
from pathlib import Path

# Colors
MAGENTA = "\033[35m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
WHITE = "\033[37m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def find_cli(name: str) -> str | None:
    """Find a CLI tool on PATH."""
    return shutil.which(name)


def run_claude(prompt: str, cwd: str) -> str:
    """Run claude -p (print mode) and return output."""
    claude_bin = find_cli("claude")
    if not claude_bin:
        return "[Error: claude CLI not found on PATH]"

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)  # Allow nested invocation

    try:
        result = subprocess.run(
            [claude_bin, "-p", prompt],
            capture_output=True, text=True, timeout=300,
            cwd=cwd, env=env,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n[stderr: {result.stderr.strip()[:200]}]"
        return output or "[No output from Claude]"
    except subprocess.TimeoutExpired:
        return "[Error: Claude timed out after 300s]"
    except Exception as e:
        return f"[Error running Claude: {e}]"


def run_codex(prompt: str, cwd: str) -> str:
    """Run codex exec and return output."""
    codex_bin = find_cli("codex")
    if not codex_bin:
        return "[Error: codex CLI not found on PATH]"

    try:
        result = subprocess.run(
            [codex_bin, "exec", "--full-auto", prompt],
            capture_output=True, text=True, timeout=300,
            cwd=cwd,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n[stderr: {result.stderr.strip()[:200]}]"
        return output or "[No output from Codex]"
    except subprocess.TimeoutExpired:
        return "[Error: Codex timed out after 300s]"
    except Exception as e:
        return f"[Error running Codex: {e}]"


def print_banner() -> None:
    print(f"""
{BOLD}╔══════════════════════════════════════════╗
║         claude-and-codex  v0.3          ║
║   Claude Code + Codex CLI orchestrator  ║
╚══════════════════════════════════════════╝{RESET}

{DIM}Both agents will respond to your messages and debate each other.
Type your message and press Enter. Type /quit to exit.
Commands: /quit, /claude <msg>, /codex <msg>, /turns <n>{RESET}
""")


def print_agent(name: str, color: str, text: str) -> None:
    print(f"\n{BOLD}{color}━━━ {name} ━━━{RESET}")
    print(f"{color}{text}{RESET}")
    print(f"{BOLD}{color}{'━' * (len(name) + 8)}{RESET}")


def main() -> None:
    # Check we're not inside a claude/codex session
    if os.environ.get("CLAUDECODE"):
        print(f"{YELLOW}Warning: Running inside a Claude Code session.")
        print(f"claude -p may not work. Run this script directly in your terminal.{RESET}")

    # Check CLI tools exist
    claude_ok = find_cli("claude") is not None
    codex_ok = find_cli("codex") is not None
    print_banner()
    print(f"  Claude CLI: {'✓' if claude_ok else '✗ not found'}")
    print(f"  Codex CLI:  {'✓' if codex_ok else '✗ not found'}")
    print()

    if not claude_ok and not codex_ok:
        print("Error: Neither claude nor codex CLI found. Install them first.")
        sys.exit(1)

    cwd = os.getcwd()
    max_debate_turns = 1  # How many times agents go back-and-forth
    conversation_history: list[tuple[str, str]] = []  # (role, content)

    while True:
        try:
            user_input = input(f"\n{BOLD}{WHITE}You > {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}Goodbye!{RESET}")
            break

        if not user_input:
            continue

        # Commands
        if user_input == "/quit":
            print(f"{DIM}Goodbye!{RESET}")
            break
        if user_input.startswith("/turns "):
            try:
                max_debate_turns = int(user_input.split()[1])
                print(f"{DIM}Debate turns set to {max_debate_turns}{RESET}")
            except ValueError:
                print(f"{DIM}Usage: /turns <number>{RESET}")
            continue
        if user_input.startswith("/claude "):
            msg = user_input[8:]
            print(f"{DIM}Sending to Claude only...{RESET}")
            resp = run_claude(msg, cwd)
            print_agent("Claude", MAGENTA, resp)
            continue
        if user_input.startswith("/codex "):
            msg = user_input[7:]
            print(f"{DIM}Sending to Codex only...{RESET}")
            resp = run_codex(msg, cwd)
            print_agent("Codex", GREEN, resp)
            continue

        conversation_history.append(("user", user_input))

        # Build context from history
        context = ""
        for role, content in conversation_history[-10:]:  # Last 10 messages
            if role == "user":
                context += f"[User]: {content}\n\n"
            elif role == "claude":
                context += f"[Claude]: {content}\n\n"
            elif role == "codex":
                context += f"[Codex]: {content}\n\n"

        # --- Round 1: Both agents respond to user ---
        claude_prompt = (
            f"You are collaborating with another AI called Codex (GPT). "
            f"A user asked something. Respond helpfully and concisely.\n\n"
            f"Conversation so far:\n{context}"
            f"Now respond as Claude."
        )

        print(f"\n{DIM}Claude is thinking...{RESET}")
        claude_resp = run_claude(claude_prompt, cwd) if claude_ok else "[Claude unavailable]"
        print_agent("Claude", MAGENTA, claude_resp)
        conversation_history.append(("claude", claude_resp))

        # Update context with Claude's response
        context += f"[Claude]: {claude_resp}\n\n"

        codex_prompt = (
            f"You are collaborating with another AI called Claude (Anthropic). "
            f"A user asked something and Claude already responded. "
            f"Add your perspective — agree, disagree, or build on Claude's answer. "
            f"If Claude covered it well, just say PASS.\n\n"
            f"Conversation so far:\n{context}"
            f"Now respond as Codex."
        )

        print(f"\n{DIM}Codex is thinking...{RESET}")
        codex_resp = run_codex(codex_prompt, cwd) if codex_ok else "[Codex unavailable]"
        print_agent("Codex", GREEN, codex_resp)
        conversation_history.append(("codex", codex_resp))

        # --- Debate rounds ---
        for turn in range(max_debate_turns):
            context += f"[Codex]: {codex_resp}\n\n"

            # Check if Codex passed
            if codex_resp.strip().upper() == "PASS":
                print(f"{DIM}Codex passed. No further debate.{RESET}")
                break

            # Claude responds to Codex
            debate_claude = (
                f"You are Claude, debating with Codex. "
                f"Codex just responded. If you agree or have nothing to add, say PASS. "
                f"Otherwise, respond constructively.\n\n"
                f"Conversation so far:\n{context}"
                f"Now respond as Claude."
            )

            print(f"\n{DIM}Claude is responding to Codex...{RESET}")
            claude_resp = run_claude(debate_claude, cwd) if claude_ok else "PASS"

            if claude_resp.strip().upper() == "PASS":
                print(f"{DIM}Claude passed. Debate concluded.{RESET}")
                conversation_history.append(("claude", "PASS"))
                break

            print_agent("Claude", MAGENTA, claude_resp)
            conversation_history.append(("claude", claude_resp))
            context += f"[Claude]: {claude_resp}\n\n"

            # Codex responds to Claude
            debate_codex = (
                f"You are Codex, debating with Claude. "
                f"Claude just responded. If you agree or have nothing to add, say PASS. "
                f"Otherwise, respond constructively.\n\n"
                f"Conversation so far:\n{context}"
                f"Now respond as Codex."
            )

            print(f"\n{DIM}Codex is responding to Claude...{RESET}")
            codex_resp = run_codex(debate_codex, cwd) if codex_ok else "PASS"

            if codex_resp.strip().upper() == "PASS":
                print(f"{DIM}Codex passed. Debate concluded.{RESET}")
                conversation_history.append(("codex", "PASS"))
                break

            print_agent("Codex", GREEN, codex_resp)
            conversation_history.append(("codex", codex_resp))


if __name__ == "__main__":
    main()
