"""Agent status display bar with token/latency metrics."""

from __future__ import annotations

from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text

from ..models import Role, AgentStatus
from ..metrics import MetricsTracker


STATUS_ICONS = {
    AgentStatus.IDLE: "o",
    AgentStatus.THINKING: "...",
    AgentStatus.STREAMING: ">>>",
    AgentStatus.TOOL_CALLING: "[T]",
    AgentStatus.ERROR: "!",
}


def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


class StatusBar(Static):
    """Shows current status of both agents plus cumulative metrics."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    """

    claude_status: reactive[AgentStatus] = reactive(AgentStatus.IDLE)
    codex_status: reactive[AgentStatus] = reactive(AgentStatus.IDLE)

    def __init__(self, metrics: MetricsTracker | None = None) -> None:
        super().__init__()
        self._metrics = metrics

    def set_metrics(self, metrics: MetricsTracker) -> None:
        self._metrics = metrics

    def render(self) -> Text:
        claude_icon = STATUS_ICONS[self.claude_status]
        codex_icon = STATUS_ICONS[self.codex_status]

        text = Text()
        text.append(
            f" Claude: {claude_icon} {self.claude_status.value} ",
            style="bold magenta",
        )

        if self._metrics:
            cm = self._metrics.get(Role.CLAUDE)
            if cm.total_turns > 0:
                text.append(
                    f"[{_fmt_tokens(cm.total_input_tokens + cm.total_output_tokens)} tok] ",
                    style="magenta",
                )

        text.append("| ")
        text.append(
            f" Codex: {codex_icon} {self.codex_status.value} ",
            style="bold green",
        )

        if self._metrics:
            xm = self._metrics.get(Role.CODEX)
            if xm.total_turns > 0:
                text.append(
                    f"[{_fmt_tokens(xm.total_input_tokens + xm.total_output_tokens)} tok] ",
                    style="green",
                )

        text.append("| Ctrl+C: quit ", style="dim")
        return text

    def update_status(self, role: Role, status: AgentStatus) -> None:
        if role == Role.CLAUDE:
            self.claude_status = status
        elif role == Role.CODEX:
            self.codex_status = status
