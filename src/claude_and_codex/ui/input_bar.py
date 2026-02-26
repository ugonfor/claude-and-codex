"""User input widget."""

from __future__ import annotations

from textual.widgets import Input
from textual.message import Message as TextualMessage


class UserSubmitted(TextualMessage):
    """Emitted when user submits a message."""

    def __init__(self, content: str) -> None:
        super().__init__()
        self.content = content


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

    async def action_submit(self) -> None:
        content = self.value.strip()
        if content:
            self.post_message(UserSubmitted(content))
            self.value = ""
