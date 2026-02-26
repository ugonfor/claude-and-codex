"""Main scrollable chat display panel."""

from __future__ import annotations

from textual.containers import VerticalScroll

from ..models import Message, Role, ToolCall
from .message_widget import MessageWidget
from .tool_call_widget import ToolCallWidget


class ChatPanel(VerticalScroll):
    """Scrollable panel showing all conversation messages."""

    DEFAULT_CSS = """
    ChatPanel {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._message_widgets: dict[str, MessageWidget] = {}

    def add_message(self, message: Message) -> None:
        widget = MessageWidget(message)
        self._message_widgets[message.message_id] = widget
        self.mount(widget)
        self.scroll_end(animate=False)

    def update_message(self, message: Message) -> None:
        widget = self._message_widgets.get(message.message_id)
        if widget:
            widget.update_content(message)
            self.scroll_end(animate=False)

    def add_tool_call(self, role: Role, tool_call: ToolCall) -> None:
        widget = ToolCallWidget(role, tool_call)
        self.mount(widget)
        self.scroll_end(animate=False)
