"""Core data models for claude-and-codex."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from datetime import datetime
from uuid import uuid4


class Role(str, Enum):
    USER = "user"
    CLAUDE = "claude"
    CODEX = "codex"
    SYSTEM = "system"
    TOOL = "tool"


class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    STREAMING = "streaming"
    TOOL_CALLING = "tool_calling"
    ERROR = "error"


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]
    result: str | None = None
    error: str | None = None


@dataclass
class Message:
    role: Role
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: list[ToolCall] = field(default_factory=list)
    is_complete: bool = True
    message_id: str = field(default_factory=lambda: str(uuid4()))
    # Which agent owns this tool message (for scoping tool results per provider)
    tool_owner: Role | None = None
