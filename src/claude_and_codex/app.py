"""Main Textual application for claude-and-codex."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual import work

from .config import Config
from .models import Role, AgentStatus, Message, ToolCall
from .conversation import Conversation
from .orchestrator import Orchestrator
from .agents.claude_agent import ClaudeAgent
from .agents.codex_agent import CodexAgent
from .tools.registry import ToolRegistry
from .tools.file_read import file_read_tool
from .tools.file_write import file_write_tool
from .tools.shell_exec import shell_exec_tool, configure as configure_shell
from .ui.chat_panel import ChatPanel
from .ui.input_bar import InputBar, UserSubmitted
from .ui.status_bar import StatusBar


class ClaudeAndCodexApp(App):
    """A TUI for collaborative AI coding with Claude and Codex."""

    TITLE = "claude-and-codex"
    CSS_PATH = "ui/app.tcss"
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config = Config.from_env()

        # Validate configuration
        self._init_errors = self.config.validate()

        # Core components
        self.conversation = Conversation()
        self.tool_registry = ToolRegistry()
        self.tool_registry.register(file_read_tool)
        self.tool_registry.register(file_write_tool)
        self.tool_registry.register(shell_exec_tool)

        # Configure shell tool with working directory
        configure_shell(
            self.config.working_directory,
            self.config.max_tool_output_chars,
        )

        # Create agents (even if keys are missing — error shown in UI)
        self.claude = ClaudeAgent(
            conversation=self.conversation,
            tool_registry=self.tool_registry,
            api_key=self.config.anthropic_api_key,
            model=self.config.claude_model,
        )
        self.codex = CodexAgent(
            conversation=self.conversation,
            tool_registry=self.tool_registry,
            api_key=self.config.openai_api_key,
            model=self.config.codex_model,
        )

        self.orchestrator = Orchestrator(
            conversation=self.conversation,
            claude=self.claude,
            codex=self.codex,
            config=self.config,
            on_status_change=self._on_status_change,
            on_stream_chunk=self._on_stream_chunk,
            on_message_complete=self._on_message_complete,
            on_tool_call=self._on_tool_call,
            on_new_message=self._on_new_message,
        )

    def compose(self) -> ComposeResult:
        yield Header()
        yield ChatPanel()
        yield InputBar()
        yield StatusBar()
        yield Footer()

    async def on_mount(self) -> None:
        """Show welcome message or init errors."""
        chat = self.query_one(ChatPanel)
        if self._init_errors:
            for err in self._init_errors:
                chat.add_message(Message(role=Role.SYSTEM, content=f"Error: {err}"))
            chat.add_message(Message(
                role=Role.SYSTEM,
                content=(
                    "Set ANTHROPIC_API_KEY and OPENAI_API_KEY environment variables,\n"
                    "or login with `claude` CLI and `codex login` for OAuth."
                ),
            ))
        else:
            chat.add_message(Message(
                role=Role.SYSTEM,
                content=(
                    f"Welcome to claude-and-codex! Both agents are ready.\n"
                    f"Auth: {self.config.auth_summary()}\n"
                    f"Working directory: {self.config.working_directory}\n"
                    f"Type a message to start collaborating."
                ),
            ))
        self.query_one(InputBar).focus()

    async def on_user_submitted(self, event: UserSubmitted) -> None:
        """Handle user message submission."""
        chat = self.query_one(ChatPanel)
        msg = Message(role=Role.USER, content=event.content)
        chat.add_message(msg)
        self._handle_message(event.content)

    @work(exclusive=True, thread=False)
    async def _handle_message(self, content: str) -> None:
        """Worker that runs the orchestrator."""
        await self.orchestrator.handle_user_message(content)

    # --- Orchestrator callbacks ---

    async def _on_status_change(self, role: Role, status: AgentStatus) -> None:
        self.query_one(StatusBar).update_status(role, status)

    async def _on_stream_chunk(
        self, role: Role, chunk: str, message: Message
    ) -> None:
        self.query_one(ChatPanel).update_message(message)

    async def _on_message_complete(self, message: Message) -> None:
        self.query_one(ChatPanel).update_message(message)

    async def _on_tool_call(self, role: Role, tool_call: ToolCall) -> None:
        self.query_one(ChatPanel).add_tool_call(role, tool_call)

    async def _on_new_message(self, message: Message) -> None:
        self.query_one(ChatPanel).add_message(message)
