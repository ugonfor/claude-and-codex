"""Claude agent implementation using Anthropic API."""

from __future__ import annotations

import anthropic
from typing import AsyncIterator

from ..models import Message, Role, ToolCall, AgentStatus
from ..conversation import Conversation
from ..tools.registry import ToolRegistry
from .base import BaseAgent


class ClaudeAgent(BaseAgent):
    def __init__(
        self,
        conversation: Conversation,
        tool_registry: ToolRegistry,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
    ) -> None:
        super().__init__(Role.CLAUDE, conversation, tool_registry)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self._pending_tool_calls: list[ToolCall] = []

    def build_system_prompt(self) -> str:
        return (
            "You are Claude, an AI coding assistant working collaboratively with "
            "another AI assistant called Codex (powered by GPT). You and Codex "
            "share a conversation with a human user. You can read/write files and "
            "execute shell commands.\n\n"
            "Guidelines:\n"
            "- If Codex has already answered adequately, say 'PASS' to skip.\n"
            "- Avoid repeating what Codex just said.\n"
            "- Collaborate: build on each other's work.\n"
            "- Be concise when the other agent is also active.\n"
            "- Use tools when you need to inspect or modify code.\n"
            "- When you disagree with Codex, explain why constructively."
        )

    async def generate_response(self) -> AsyncIterator[str]:
        self.status = AgentStatus.STREAMING
        self._pending_tool_calls = []

        messages = self.conversation.to_anthropic_messages()
        tools = self.tool_registry.all_anthropic()

        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=self.build_system_prompt(),
                messages=messages,
                tools=tools if tools else anthropic.NOT_GIVEN,
            ) as stream:
                async for event in stream:
                    if hasattr(event, "type") and event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield event.delta.text

                final_message = await stream.get_final_message()
                for block in final_message.content:
                    if block.type == "tool_use":
                        self._pending_tool_calls.append(
                            ToolCall(
                                id=block.id,
                                name=block.name,
                                arguments=block.input,
                            )
                        )
        except Exception as e:
            self.status = AgentStatus.ERROR
            yield f"\n[Error: {e}]"
            return

        self.status = AgentStatus.IDLE

    async def get_pending_tool_calls(self) -> list[ToolCall]:
        return self._pending_tool_calls

    def should_respond(self, last_messages: list[Message]) -> bool:
        if not last_messages:
            return False
        last = last_messages[-1]
        if last.role == Role.USER:
            return True
        if last.role == Role.CODEX:
            content_lower = last.content.lower()
            if "claude" in content_lower or "?" in last.content:
                return True
            if content_lower.strip() == "pass":
                return False
        if last.role == Role.TOOL:
            # Respond to tool results from our own tool calls
            return True
        return False
