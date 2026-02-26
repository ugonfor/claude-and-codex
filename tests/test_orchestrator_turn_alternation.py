from __future__ import annotations

from typing import AsyncIterator

import pytest

from claude_and_codex.agents.base import BaseAgent
from claude_and_codex.config import Config
from claude_and_codex.conversation import Conversation
from claude_and_codex.models import Message, Role, ToolCall
from claude_and_codex.orchestrator import Orchestrator
from claude_and_codex.tools.registry import ToolRegistry


class FakeAgent(BaseAgent):
    def __init__(self, role: Role, conversation: Conversation, tool_registry: ToolRegistry) -> None:
        super().__init__(role, conversation, tool_registry)

    async def generate_response(self) -> AsyncIterator[str]:
        yield f"{self.role.value}-response"

    async def get_pending_tool_calls(self) -> list[ToolCall]:
        return []

    def should_respond(self, last_messages: list[Message]) -> bool:
        return True

    def build_system_prompt(self) -> str:
        return ""


@pytest.mark.asyncio
async def test_orchestrator_alternates_first_responder_per_user_turn() -> None:
    conversation = Conversation()
    tools = ToolRegistry()
    claude = FakeAgent(Role.CLAUDE, conversation, tools)
    codex = FakeAgent(Role.CODEX, conversation, tools)

    orchestrator = Orchestrator(
        conversation=conversation,
        claude=claude,
        codex=codex,
        config=Config(
            anthropic_api_key="test",
            openai_api_key="test",
            agent_cooldown_seconds=0,
            max_consecutive_agent_turns=2,
        ),
    )

    await orchestrator.handle_user_message("first")
    first_turn_roles = [m.role for m in conversation.messages]
    assert first_turn_roles[:3] == [Role.USER, Role.CLAUDE, Role.CODEX]

    await orchestrator.handle_user_message("second")
    all_roles = [m.role for m in conversation.messages]
    assert all_roles[3:6] == [Role.USER, Role.CODEX, Role.CLAUDE]
