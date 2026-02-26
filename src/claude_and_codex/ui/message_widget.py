"""Individual message rendering widget with color coding."""

from __future__ import annotations

from textual.widget import Widget
from textual.reactive import reactive
from rich.panel import Panel
from rich.markdown import Markdown as RichMarkdown
from rich.text import Text

from ..models import Message, Role

ROLE_COLORS = {
    Role.USER: "bright_white",
    Role.CLAUDE: "bright_magenta",
    Role.CODEX: "bright_green",
    Role.SYSTEM: "bright_yellow",
    Role.TOOL: "dim",
}

ROLE_LABELS = {
    Role.USER: "You",
    Role.CLAUDE: "Claude",
    Role.CODEX: "Codex",
    Role.SYSTEM: "System",
    Role.TOOL: "Tool",
}


class MessageWidget(Widget):
    """Renders a single conversation message with color-coded borders."""

    DEFAULT_CSS = """
    MessageWidget {
        height: auto;
        margin: 0 0 1 0;
        padding: 0 1;
    }
    """

    content = reactive("")

    def __init__(self, message: Message) -> None:
        super().__init__()
        self.message = message
        self.content = message.content

    def render(self) -> Panel:
        color = ROLE_COLORS.get(self.message.role, "white")
        label = ROLE_LABELS.get(self.message.role, "Unknown")

        if self.content:
            body = RichMarkdown(self.content)
        else:
            body = Text("...", style="dim italic")

        status = "" if self.message.is_complete else " (streaming...)"

        return Panel(
            body,
            title=f"[bold {color}]{label}{status}[/]",
            title_align="left",
            border_style=color,
            padding=(0, 1),
        )

    def update_content(self, message: Message) -> None:
        self.message = message
        self.content = message.content
        self.refresh()
