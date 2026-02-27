"""Token and latency metrics tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from .models import Role


@dataclass
class TurnMetrics:
    """Metrics for a single agent turn."""
    role: Role
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0


@dataclass
class AgentMetrics:
    """Cumulative metrics for one agent."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_turns: int = 0
    total_latency_ms: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        if self.total_turns == 0:
            return 0.0
        return self.total_latency_ms / self.total_turns

    def record(self, turn: TurnMetrics) -> None:
        self.total_input_tokens += turn.input_tokens
        self.total_output_tokens += turn.output_tokens
        self.total_latency_ms += turn.latency_ms
        self.total_turns += 1


class MetricsTracker:
    """Tracks per-agent metrics across the session."""

    def __init__(self) -> None:
        self._agents: dict[Role, AgentMetrics] = {
            Role.CLAUDE: AgentMetrics(),
            Role.CODEX: AgentMetrics(),
        }
        self.turns: list[TurnMetrics] = []

    def record_turn(self, turn: TurnMetrics) -> None:
        self._agents[turn.role].record(turn)
        self.turns.append(turn)

    def get(self, role: Role) -> AgentMetrics:
        return self._agents[role]

    def summary(self) -> str:
        lines: list[str] = ["Session Metrics", ""]
        for role in (Role.CLAUDE, Role.CODEX):
            m = self._agents[role]
            name = "Claude" if role == Role.CLAUDE else "Codex"
            lines.append(f"{name}:")
            lines.append(f"  Turns: {m.total_turns}")
            lines.append(
                f"  Tokens: {m.total_input_tokens} in / {m.total_output_tokens} out"
            )
            lines.append(f"  Avg latency: {m.avg_latency_ms:.0f}ms")
            lines.append("")
        total_tokens = sum(
            m.total_input_tokens + m.total_output_tokens
            for m in self._agents.values()
        )
        lines.append(f"Total tokens: {total_tokens}")
        return "\n".join(lines)

    def reset(self) -> None:
        for m in self._agents.values():
            m.total_input_tokens = 0
            m.total_output_tokens = 0
            m.total_turns = 0
            m.total_latency_ms = 0.0
        self.turns.clear()
