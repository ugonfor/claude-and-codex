"""Main Textual application for claude-and-codex."""

from __future__ import annotations

import asyncio
from pathlib import Path
from dataclasses import dataclass

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
from .tools.file_read import file_read_tool, configure as configure_file_read
from .tools.file_write import file_write_tool, configure as configure_file_write
from .tools.shell_exec import shell_exec_tool, configure as configure_shell
from .ui.chat_panel import ChatPanel
from .ui.input_bar import InputBar, UserSubmitted, CommandSubmitted, SlashCommand
from .ui.status_bar import StatusBar


@dataclass
class PendingConfirmation:
    tool_name: str
    future: asyncio.Future[bool]


class CommandHandler:
    """Handles slash commands from the input bar."""

    HELP_TEXT = (
        "Available commands:\n"
        "- /model <name>: set Claude and Codex model names\n"
        "- /clear: clear chat and conversation history\n"
        "- /cd <path>: set working directory for tools\n"
        "- /help: show this help"
    )

    def __init__(self, app: ClaudeAndCodexApp) -> None:
        self.app = app

    async def handle(self, command: SlashCommand) -> str:
        name = command.name

        if name == "help" or name == "":
            return self.HELP_TEXT

        if name == "clear":
            self.app.conversation = Conversation()
            self.app.claude.conversation = self.app.conversation
            self.app.codex.conversation = self.app.conversation
            self.app.orchestrator.conversation = self.app.conversation
            self.app.query_one(ChatPanel).clear_messages()
            return "Cleared chat panel and in-memory conversation."

        if name == "model":
            model = command.argument.strip()
            if not model:
                return "Usage: /model <name>"
            self.app.config.claude_model = model
            self.app.config.codex_model = model
            self.app.claude.model = model
            self.app.codex.model = model
            return f"Updated model for both agents to: {model}"

        if name == "cd":
            raw_path = command.argument.strip()
            if not raw_path:
                return "Usage: /cd <path>"

            candidate = Path(raw_path)
            if not candidate.is_absolute():
                candidate = (self.app.config.working_directory / candidate).resolve()

            if not candidate.exists():
                return f"Path does not exist: {candidate}"
            if not candidate.is_dir():
                return f"Not a directory: {candidate}"

            self.app.config.working_directory = candidate
            configure_file_read(candidate)
            configure_file_write(candidate)
            configure_shell(candidate, self.app.config.max_tool_output_chars)
            return f"Working directory changed to: {candidate}"

        return f"Unknown command: /{name}\n\n{self.HELP_TEXT}"


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
        self.command_handler = CommandHandler(self)
        self._pending_confirmation: PendingConfirmation | None = None

        # Validate configuration
        self._init_errors = self.config.validate()

        # Core components
        self.conversation = Conversation()
        self.tool_registry = ToolRegistry()
        self.tool_registry.register(file_read_tool)
        self.tool_registry.register(file_write_tool)
        self.tool_registry.register(shell_exec_tool)

        # Configure all tools with working directory (P2 fix)
        configure_file_read(self.config.working_directory)
        configure_file_write(self.config.working_directory)
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
            on_tool_confirmation=self._on_tool_confirmation,
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
        if await self._maybe_resolve_confirmation(event.content):
            return

        chat = self.query_one(ChatPanel)
        msg = Message(role=Role.USER, content=event.content)
        chat.add_message(msg)
        self._handle_message(event.content)

    async def on_command_submitted(self, event: CommandSubmitted) -> None:
        if await self._maybe_resolve_confirmation(event.command.raw):
            return

        result = await self.command_handler.handle(event.command)
        self.query_one(ChatPanel).add_message(Message(role=Role.SYSTEM, content=result))

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

    async def _on_tool_confirmation(self, role: Role, tool_call: ToolCall) -> bool:
        caller = "Claude" if role == Role.CLAUDE else "Codex"
        args_preview = str(tool_call.arguments)
        prompt = (
            f"Confirm tool execution from {caller}: `{tool_call.name}`\n"
            f"Arguments: {args_preview}\n"
            "Reply `yes` to approve or `no` to deny."
        )
        self.query_one(ChatPanel).add_message(
            Message(role=Role.SYSTEM, content=prompt)
        )

        future: asyncio.Future[bool] = asyncio.get_running_loop().create_future()
        self._pending_confirmation = PendingConfirmation(
            tool_name=tool_call.name,
            future=future,
        )
        self.query_one(InputBar).placeholder = "Confirm tool call: yes / no"
        approved = await future
        self.query_one(InputBar).placeholder = "Type a message... (Ctrl+C to quit)"
        return approved

    async def _maybe_resolve_confirmation(self, content: str) -> bool:
        pending = self._pending_confirmation
        if pending is None:
            return False

        value = content.strip().lower()
        if value in {"yes", "y"}:
            pending.future.set_result(True)
            self.query_one(ChatPanel).add_message(
                Message(
                    role=Role.SYSTEM,
                    content=f"Approved `{pending.tool_name}`.",
                )
            )
            self._pending_confirmation = None
            return True

        if value in {"no", "n"}:
            pending.future.set_result(False)
            self.query_one(ChatPanel).add_message(
                Message(
                    role=Role.SYSTEM,
                    content=f"Denied `{pending.tool_name}`.",
                )
            )
            self._pending_confirmation = None
            return True

        self.query_one(ChatPanel).add_message(
            Message(
                role=Role.SYSTEM,
                content="Pending tool confirmation. Reply `yes` or `no`.",
            )
        )
        return True
