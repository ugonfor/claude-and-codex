"""Tool call and result display widget."""

from __future__ import annotations

import json

from textual.widget import Widget
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.console import Group

from ..models import Role, ToolCall


class ToolCallWidget(Widget):
    """Renders a tool call and its result."""

    DEFAULT_CSS = """
    ToolCallWidget {
        height: auto;
        margin: 0 2 1 2;
        padding: 0;
    }
    """

    def __init__(self, role: Role, tool_call: ToolCall) -> None:
        super().__init__()
        self.role = role
        self.tool_call = tool_call

    def render(self) -> Panel:
        tc = self.tool_call
        caller = "Claude" if self.role == Role.CLAUDE else "Codex"
        header = Text(f"{caller} -> {tc.name}", style="bold cyan")

        parts = [header, Text("")]

        args_str = json.dumps(tc.arguments, indent=2)
        parts.append(Syntax(args_str, "json", theme="monokai", line_numbers=False))

        if tc.result:
            parts.append(Text("\nResult:", style="bold green"))
            result_preview = tc.result[:500]
            if len(tc.result) > 500:
                result_preview += "... (truncated)"
            parts.append(Text(result_preview, style="dim"))

        if tc.error:
            parts.append(Text(f"\nError: {tc.error}", style="bold red"))

        return Panel(
            Group(*parts),
            title="[dim]Tool Call[/]",
            border_style="dim cyan",
        )
