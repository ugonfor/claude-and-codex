"""Abstract base agent class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from ..models import Message, Role, ToolCall, AgentStatus
from ..conversation import Conversation
from ..tools.registry import ToolRegistry


class BaseAgent(ABC):
    """Abstract base for both Claude and Codex agents."""

    def __init__(
        self,
        role: Role,
        conversation: Conversation,
        tool_registry: ToolRegistry,
    ) -> None:
        self.role = role
        self.conversation = conversation
        self.tool_registry = tool_registry
        self.status = AgentStatus.IDLE

    @abstractmethod
    async def generate_response(self) -> AsyncIterator[str]:
        """Stream a response. Yields text chunks as they arrive."""
        ...

    @abstractmethod
    async def get_pending_tool_calls(self) -> list[ToolCall]:
        """After generate_response completes, return any tool calls."""
        ...

    @abstractmethod
    def should_respond(self, last_messages: list[Message]) -> bool:
        """Heuristic: should this agent respond given recent context?"""
        ...

    @abstractmethod
    def build_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        ...
