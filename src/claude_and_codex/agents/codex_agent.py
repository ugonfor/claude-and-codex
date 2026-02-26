"""Codex agent implementation using OpenAI API."""

from __future__ import annotations

import json
from openai import AsyncOpenAI
from typing import AsyncIterator

from ..models import Message, Role, ToolCall, AgentStatus
from ..conversation import Conversation
from ..tools.registry import ToolRegistry
from .base import BaseAgent


class CodexAgent(BaseAgent):
    def __init__(
        self,
        conversation: Conversation,
        tool_registry: ToolRegistry,
        api_key: str,
        model: str = "gpt-4o",
    ) -> None:
        super().__init__(Role.CODEX, conversation, tool_registry)
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self._pending_tool_calls: list[ToolCall] = []

    def build_system_prompt(self) -> str:
        return (
            "You are Codex, an AI coding assistant powered by GPT, working "
            "collaboratively with another AI assistant called Claude (by Anthropic). "
            "You and Claude share a conversation with a human user. You can read/write "
            "files and execute shell commands.\n\n"
            "Guidelines:\n"
            "- If Claude has already answered adequately, respond with just 'PASS'.\n"
            "- Avoid repeating what Claude just said.\n"
            "- Collaborate: build on each other's work.\n"
            "- Be concise when the other agent is also active.\n"
            "- Use tools when you need to inspect or modify code.\n"
            "- When you disagree with Claude, explain why constructively."
        )

    async def generate_response(self) -> AsyncIterator[str]:
        self.status = AgentStatus.STREAMING
        self._pending_tool_calls = []

        messages = self.conversation.to_openai_messages()
        messages.insert(0, {"role": "system", "content": self.build_system_prompt()})
        tools = self.tool_registry.all_openai()

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                stream=True,
            )

            # Accumulate tool call data from streamed chunks
            tool_call_accumulators: dict[int, dict] = {}

            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta is None:
                    continue

                # Stream text content
                if delta.content:
                    yield delta.content

                # Accumulate tool calls from deltas
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in tool_call_accumulators:
                            tool_call_accumulators[idx] = {
                                "id": "",
                                "name": "",
                                "arguments": "",
                            }
                        acc = tool_call_accumulators[idx]
                        if tc_delta.id:
                            acc["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                acc["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                acc["arguments"] += tc_delta.function.arguments

            # Build final tool calls from accumulators
            for _idx, acc in sorted(tool_call_accumulators.items()):
                try:
                    args = json.loads(acc["arguments"]) if acc["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}
                self._pending_tool_calls.append(
                    ToolCall(id=acc["id"], name=acc["name"], arguments=args)
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
        if last.role == Role.CLAUDE:
            content_lower = last.content.lower()
            if "codex" in content_lower or "?" in last.content:
                return True
            if content_lower.strip() == "pass":
                return False
        if last.role == Role.TOOL:
            return True
        return False
