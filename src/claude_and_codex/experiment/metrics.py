"""Metrics data structures for experiment runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DispatchMetrics:
    """Metrics for a single agent dispatch within a round."""
    agent: str                  # "claude_a", "claude_b", "claude", "codex"
    command: str                # the instruction given
    wall_clock_seconds: float = 0.0
    output_length: int = 0      # chars of output
    was_error: bool = False


@dataclass
class VerificationResult:
    """Result of a VERIFY command."""
    passed: bool
    output: str = ""
    wall_clock_seconds: float = 0.0


@dataclass
class RoundMetrics:
    """Metrics for one Team Leader reasoning round."""
    round_number: int
    leader_seconds: float = 0.0          # time for Team Leader thinking
    dispatches: list[DispatchMetrics] = field(default_factory=list)
    verification: VerificationResult | None = None

    @property
    def wall_clock_seconds(self) -> float:
        total = self.leader_seconds
        total += sum(d.wall_clock_seconds for d in self.dispatches)
        if self.verification:
            total += self.verification.wall_clock_seconds
        return total


@dataclass
class ExperimentRunResult:
    """Complete result of one experiment run (one benchmark x one mode)."""
    run_id: str
    benchmark_id: str
    benchmark_name: str
    benchmark_category: str
    mode: str                                    # "cc", "cx", "dcc"
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime = field(default_factory=datetime.now)
    total_wall_clock_seconds: float = 0.0
    rounds_used: int = 0
    max_rounds: int = 8
    rounds: list[RoundMetrics] = field(default_factory=list)
    final_verification: VerificationResult | None = None
    final_status: str = "pending"                # "done", "max_rounds", "error"
    done_summary: str = ""
    team_leader_calls: int = 0
    total_dispatches: int = 0
    dispatches_per_agent: dict[str, int] = field(default_factory=dict)
    director_plan: str | None = None             # DCC mode only
    director_plan_seconds: float = 0.0           # DCC mode only
    sandbox_path: str = ""
    error: str | None = None

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "run_id": self.run_id,
            "benchmark_id": self.benchmark_id,
            "benchmark_name": self.benchmark_name,
            "benchmark_category": self.benchmark_category,
            "mode": self.mode,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "total_wall_clock_seconds": self.total_wall_clock_seconds,
            "rounds_used": self.rounds_used,
            "max_rounds": self.max_rounds,
            "rounds": [
                {
                    "round_number": r.round_number,
                    "leader_seconds": r.leader_seconds,
                    "wall_clock_seconds": r.wall_clock_seconds,
                    "dispatches": [
                        {
                            "agent": d.agent,
                            "command": d.command,
                            "wall_clock_seconds": d.wall_clock_seconds,
                            "output_length": d.output_length,
                            "was_error": d.was_error,
                        }
                        for d in r.dispatches
                    ],
                    "verification": {
                        "passed": r.verification.passed,
                        "output": r.verification.output,
                        "wall_clock_seconds": r.verification.wall_clock_seconds,
                    } if r.verification else None,
                }
                for r in self.rounds
            ],
            "final_verification": {
                "passed": self.final_verification.passed,
                "output": self.final_verification.output,
                "wall_clock_seconds": self.final_verification.wall_clock_seconds,
            } if self.final_verification else None,
            "final_status": self.final_status,
            "done_summary": self.done_summary,
            "team_leader_calls": self.team_leader_calls,
            "total_dispatches": self.total_dispatches,
            "dispatches_per_agent": self.dispatches_per_agent,
            "director_plan": self.director_plan,
            "director_plan_seconds": self.director_plan_seconds,
            "sandbox_path": self.sandbox_path,
            "error": self.error,
        }
