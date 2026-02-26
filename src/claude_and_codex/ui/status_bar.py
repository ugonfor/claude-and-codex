"""Agent status display bar."""

from __future__ import annotations

from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text

from ..models import Role, AgentStatus


STATUS_ICONS = {
    AgentStatus.IDLE: "o",
    AgentStatus.THINKING: "...",
    AgentStatus.STREAMING: ">>>",
    AgentStatus.TOOL_CALLING: "[T]",
    AgentStatus.ERROR: "!",
}


class StatusBar(Static):
    """Shows current status of both agents."""

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

    def render(self) -> Text:
        claude_icon = STATUS_ICONS[self.claude_status]
        codex_icon = STATUS_ICONS[self.codex_status]

        text = Text()
        text.append(
            f" Claude: {claude_icon} {self.claude_status.value} ",
            style="bold magenta",
        )
        text.append(" | ")
        text.append(
            f" Codex: {codex_icon} {self.codex_status.value} ",
            style="bold green",
        )
        text.append(" | Ctrl+C: quit ", style="dim")
        return text

    def update_status(self, role: Role, status: AgentStatus) -> None:
        if role == Role.CLAUDE:
            self.claude_status = status
        elif role == Role.CODEX:
            self.codex_status = status
