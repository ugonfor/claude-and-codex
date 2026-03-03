"""Three experiment modes: CC (Claude-Claude), CX (Claude-Codex), DCC (Director-Claude-Codex)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from rich.console import Console

from ..orchestrate import (
    run_claude, run_codex, run_verify, truncate, is_error,
)
from .metrics import (
    ExperimentRunResult, RoundMetrics, DispatchMetrics, VerificationResult,
)
from .benchmarks import Benchmark

console = Console()


# ── Mode definitions ────────────────────────────────────────────────────────


class ExperimentMode(str, Enum):
    CC = "cc"       # Claude-Claude
    CX = "cx"       # Claude-Codex (control group)
    DCC = "dcc"     # Director(Claude) + Claude-Codex


CC_SYSTEM = """\
You are the TEAM LEADER (coordinator only) in a Director-Team Leader-Teammate system.

CRITICAL: You are a COORDINATOR. You do NOT write code, edit files, or use tools yourself.
Your ONLY job is to emit DISPATCH commands and let teammates do the work.
You MUST dispatch at least one command before using DONE.

The DIRECTOR (user) gives you tasks. You have two TEAMMATES:
- Claude Agent A (via DISPATCH_CLAUDE_A) -- strong at analysis, architecture, careful code
- Claude Agent B (via DISPATCH_CLAUDE_B) -- brings a second perspective, catches blind spots

Both teammates are Claude Code instances. Use them for different aspects:
- Agent A writes code, Agent B reviews (or vice versa)
- Agent A builds, Agent B tests
- Split different subproblems between them

COMMANDS (put these on their own line, exactly as shown):

  DISPATCH_CLAUDE_A: <instruction for Agent A>
  DISPATCH_CLAUDE_B: <instruction for Agent B>
  VERIFY
  DONE: <summary for the Director>

Rules:
- You MUST dispatch to at least one teammate before DONE
- You can dispatch to one or both teammates in a single response
- After dispatching, you'll see their output and can decide next steps
- ALWAYS verify after code changes before reporting DONE
- If a teammate's work has issues, dispatch a fix (to same or other teammate)
- ABSOLUTELY DO NOT do any coding work yourself -- only dispatch
- Do not read, write, or edit any files yourself -- teammates handle all file operations
- Be concise in your reasoning. Focus on coordination, not narration.
- NEVER ask the Director for clarification. Figure it out yourself.
"""

CX_SYSTEM = """\
You are the TEAM LEADER (coordinator only) in a Director-Team Leader-Teammate system.

CRITICAL: You are a COORDINATOR. You do NOT write code, edit files, or use tools yourself.
Your ONLY job is to emit DISPATCH commands and let teammates do the work.
You MUST dispatch at least one command before using DONE.

The DIRECTOR (user) gives you tasks. You have two TEAMMATES:
- Claude Code (via DISPATCH_CLAUDE) -- strong at analysis, architecture, careful code
- Codex (via DISPATCH_CODEX) -- strong at fast iteration, generation, different perspective

COMMANDS (put these on their own line, exactly as shown):

  DISPATCH_CLAUDE: <instruction for Claude Code>
  DISPATCH_CODEX: <instruction for Codex>
  VERIFY
  DONE: <summary for the Director>

Rules:
- You MUST dispatch to at least one teammate before DONE
- You can dispatch to one or both teammates in a single response
- After dispatching, you'll see their output and can decide next steps
- ALWAYS verify after code changes before reporting DONE
- If a teammate's work has issues, dispatch a fix (to same or other teammate)
- ABSOLUTELY DO NOT do any coding work yourself -- only dispatch
- Do not read, write, or edit any files yourself -- teammates handle all file operations
- Be concise in your reasoning. Focus on coordination, not narration.
- NEVER ask the Director for clarification. Figure it out yourself.
"""

DCC_DIRECTOR_SYSTEM = """\
You are the DIRECTOR in a Director-Team Leader-Teammate system.

Given a task, produce a structured execution plan. Do NOT execute the task yourself.
Only output a plan. Do NOT write code, edit files, or use tools.

Think carefully about:
1. What subtasks are needed
2. Which agent type is best for each (Claude for analysis/architecture, Codex for generation)
3. What order they should run in
4. How to verify success

Output format (text only, no tool use):
PLAN:
1. <subtask description> [agent: claude|codex]
2. <subtask description> [agent: claude|codex]
...
SUCCESS_CRITERIA: <what "done" looks like>
VERIFY_STRATEGY: <how to verify the work>
"""


@dataclass
class ModeConfig:
    mode: ExperimentMode
    system_prompt: str
    has_director_layer: bool = False


def get_mode_config(mode: ExperimentMode) -> ModeConfig:
    """Get configuration for a given experiment mode."""
    if mode == ExperimentMode.CC:
        return ModeConfig(mode=mode, system_prompt=CC_SYSTEM)
    elif mode == ExperimentMode.CX:
        return ModeConfig(mode=mode, system_prompt=CX_SYSTEM)
    elif mode == ExperimentMode.DCC:
        return ModeConfig(mode=mode, system_prompt=CX_SYSTEM, has_director_layer=True)
    raise ValueError(f"Unknown mode: {mode}")


# ── Command parsing ─────────────────────────────────────────────────────────


def parse_experiment_commands(
    response: str, mode: ExperimentMode
) -> list[tuple[str, str]]:
    """Parse structured commands, supporting mode-specific variants.

    CC mode: DISPATCH_CLAUDE_A, DISPATCH_CLAUDE_B, VERIFY, DONE
    CX/DCC: DISPATCH_CLAUDE, DISPATCH_CODEX, VERIFY, DONE
    """
    commands: list[tuple[str, str]] = []
    for line in response.split("\n"):
        stripped = line.strip()

        if mode == ExperimentMode.CC:
            if stripped.startswith("DISPATCH_CLAUDE_A:"):
                commands.append(("DISPATCH_CLAUDE_A", stripped[18:].strip()))
            elif stripped.startswith("DISPATCH_CLAUDE_B:"):
                commands.append(("DISPATCH_CLAUDE_B", stripped[18:].strip()))
        else:
            if stripped.startswith("DISPATCH_CLAUDE:"):
                commands.append(("DISPATCH_CLAUDE", stripped[16:].strip()))
            elif stripped.startswith("DISPATCH_CODEX:"):
                commands.append(("DISPATCH_CODEX", stripped[15:].strip()))

        if stripped == "VERIFY":
            commands.append(("VERIFY", ""))
        elif stripped.startswith("DONE:"):
            commands.append(("DONE", stripped[5:].strip()))
        elif stripped == "DONE":
            commands.append(("DONE", "Task complete."))

    return commands


# ── Dispatch helpers ────────────────────────────────────────────────────────


def _dispatch(
    cmd: str, arg: str, cwd: str, codex_ok: bool,
) -> tuple[str, str, str]:
    """Execute a dispatch command. Returns (agent_label, output, agent_key)."""
    if cmd == "DISPATCH_CLAUDE_A":
        return "Claude A", run_claude(arg, cwd, stream=False), "claude_a"
    elif cmd == "DISPATCH_CLAUDE_B":
        return "Claude B", run_claude(arg, cwd, stream=False), "claude_b"
    elif cmd == "DISPATCH_CLAUDE":
        return "Claude", run_claude(arg, cwd, stream=False), "claude"
    elif cmd == "DISPATCH_CODEX":
        if not codex_ok:
            return "Codex", "[System: Codex not available]", "codex"
        return "Codex", run_codex(arg, cwd, stream=False), "codex"
    return "unknown", "", "unknown"


# ── Core experiment task runner ─────────────────────────────────────────────


def run_experiment_task(
    benchmark: Benchmark,
    mode: ExperimentMode,
    sandbox_dir: str,
    max_rounds: int = 8,
    codex_ok: bool = True,
) -> ExperimentRunResult:
    """Run one benchmark task in one mode. Returns structured results.

    All CLI calls use stream=False (batch experiment, no terminal output).
    """
    config = get_mode_config(mode)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{mode.value}_{benchmark.id}_{ts}"

    result = ExperimentRunResult(
        run_id=run_id,
        benchmark_id=benchmark.id,
        benchmark_name=benchmark.name,
        benchmark_category=benchmark.category,
        mode=mode.value,
        max_rounds=max_rounds,
        sandbox_path=sandbox_dir,
    )
    result.started_at = datetime.now()

    verify_cmd = benchmark.verify_cmd or None
    team_log: list[str] = []
    team_log.append(f"[Director's request]: {benchmark.description}")

    # DCC mode: Director planning phase
    if config.has_director_layer:
        console.print(f"  [dim]{mode.value}[/dim] Director planning...")
        t0 = time.time()
        director_prompt = (
            f"{DCC_DIRECTOR_SYSTEM}\n\n"
            f"Working directory: {sandbox_dir}\n\n"
            f"Task:\n{benchmark.description}"
        )
        director_plan = run_claude(director_prompt, sandbox_dir, stream=False)
        result.director_plan_seconds = time.time() - t0
        result.director_plan = director_plan
        team_log.insert(0, f"[Director's plan]: {director_plan}")
        console.print(f"  [dim]{mode.value}[/dim] Director plan ready ({result.director_plan_seconds:.1f}s)")

    # Team Leader loop
    for round_num in range(1, max_rounds + 1):
        result.rounds_used = round_num
        round_metrics = RoundMetrics(round_number=round_num)
        console.print(f"  [dim]{mode.value}[/dim] Round {round_num}/{max_rounds}")

        # Team Leader thinking
        leader_prompt = (
            f"{config.system_prompt}\n\n"
            f"Working directory: {sandbox_dir}\n"
            f"Verify command: {verify_cmd or '(auto-detect)'}\n\n"
            f"Conversation log:\n" + "\n\n".join(team_log)
        )
        t0 = time.time()
        leader_response = run_claude(leader_prompt, sandbox_dir, stream=False)
        round_metrics.leader_seconds = time.time() - t0
        result.team_leader_calls += 1

        if is_error(leader_response):
            result.error = leader_response
            result.final_status = "error"
            break

        team_log.append(f"[Team Leader]: {leader_response}")

        # Parse and execute commands
        commands = parse_experiment_commands(leader_response, mode)

        if not commands:
            team_log.append("[System]: No commands detected. Continue or use DONE.")
            result.rounds.append(round_metrics)
            continue

        done = False
        for cmd, arg in commands:
            if cmd.startswith("DISPATCH_"):
                t0 = time.time()
                label, output, agent_key = _dispatch(cmd, arg, sandbox_dir, codex_ok)
                dispatch_time = time.time() - t0

                dm = DispatchMetrics(
                    agent=agent_key,
                    command=arg,
                    wall_clock_seconds=dispatch_time,
                    output_length=len(output),
                    was_error=is_error(output),
                )
                round_metrics.dispatches.append(dm)
                result.total_dispatches += 1
                result.dispatches_per_agent[agent_key] = (
                    result.dispatches_per_agent.get(agent_key, 0) + 1
                )

                team_log.append(f"[{label} output]: {truncate(output)}")
                console.print(f"  [dim]{mode.value}[/dim]   {label}: {len(output)} chars ({dispatch_time:.1f}s)")

            elif cmd == "VERIFY":
                t0 = time.time()
                passed, verify_output = run_verify(sandbox_dir, verify_cmd)
                verify_time = time.time() - t0

                vr = VerificationResult(
                    passed=passed,
                    output=verify_output,
                    wall_clock_seconds=verify_time,
                )
                round_metrics.verification = vr
                result.final_verification = vr

                status = "PASSED" if passed else "FAILED"
                team_log.append(f"[Verification]: {status}\n{verify_output}")
                console.print(f"  [dim]{mode.value}[/dim]   Verify: {status} ({verify_time:.1f}s)")

            elif cmd == "DONE":
                result.done_summary = arg
                result.final_status = "done"
                done = True
                break

        result.rounds.append(round_metrics)
        result.rounds_used = round_num

        if done:
            break
    else:
        result.final_status = "max_rounds"

    result.finished_at = datetime.now()
    result.total_wall_clock_seconds = (
        result.finished_at - result.started_at
    ).total_seconds()

    return result
