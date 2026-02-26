"""User input widget."""

from __future__ import annotations

from dataclasses import dataclass

from textual.widgets import Input
from textual.message import Message as TextualMessage


class UserSubmitted(TextualMessage):
    """Emitted when user submits a message."""

    def __init__(self, content: str) -> None:
        super().__init__()
        self.content = content


@dataclass(frozen=True)
class SlashCommand:
    """Parsed slash command from the input bar."""

    name: str
    argument: str
    raw: str


class CommandSubmitted(TextualMessage):
    """Emitted when user submits a slash command."""

    def __init__(self, command: SlashCommand) -> None:
        super().__init__()
        self.command = command


class InputBar(Input):
    """Input widget at the bottom of the screen."""

    DEFAULT_CSS = """
    InputBar {
        dock: bottom;
        height: 3;
        margin: 0 1;
        border: solid $accent;
    }
    """

    def __init__(self) -> None:
        super().__init__(placeholder="Type a message... (Ctrl+C to quit)")

    def _parse_slash_command(self, content: str) -> SlashCommand | None:
        if not content.startswith("/"):
            return None

        body = content[1:].strip()
        if not body:
            return SlashCommand(name="", argument="", raw=content)

        parts = body.split(maxsplit=1)
        name = parts[0].lower()
        argument = parts[1].strip() if len(parts) > 1 else ""
        return SlashCommand(name=name, argument=argument, raw=content)

    async def action_submit(self) -> None:
        content = self.value.strip()
        if content:
            command = self._parse_slash_command(content)
            if command is not None:
                self.post_message(CommandSubmitted(command))
            else:
                self.post_message(UserSubmitted(content))
            self.value = ""
