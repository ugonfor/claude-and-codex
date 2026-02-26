"""Shared conversation state and event bus."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from .models import Message, Role, ToolCall


class Conversation:
    """Thread-safe shared conversation state with dual API format conversion."""

    def __init__(self) -> None:
        self._messages: list[Message] = []
        self._lock = asyncio.Lock()
        self._listeners: list[asyncio.Queue[tuple[Message, bool]]] = []

    @property
    def messages(self) -> list[Message]:
        return list(self._messages)

    async def add_message(self, message: Message) -> None:
        async with self._lock:
            self._messages.append(message)
        for queue in self._listeners:
            await queue.put((message, False))

    async def update_message(self, message: Message) -> None:
        """For streaming updates to an in-progress message."""
        for queue in self._listeners:
            await queue.put((message, True))

    def subscribe(self) -> asyncio.Queue[tuple[Message, bool]]:
        queue: asyncio.Queue[tuple[Message, bool]] = asyncio.Queue()
        self._listeners.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        if queue in self._listeners:
            self._listeners.remove(queue)

    def to_anthropic_messages(self) -> list[dict[str, Any]]:
        """Convert conversation to Anthropic API message format.

        Claude's own messages become 'assistant'.
        Codex messages become 'user' with a [Codex] prefix.
        Tool results: native format for Claude's own calls, plain text summary
        for Codex's calls (avoids invalid tool_result without matching tool_use).
        """
        result: list[dict[str, Any]] = []
        for msg in self._messages:
            if not msg.is_complete:
                continue

            if msg.role == Role.USER:
                result.append({"role": "user", "content": msg.content})

            elif msg.role == Role.CLAUDE:
                content_blocks: list[dict[str, Any]] = []
                if msg.content:
                    content_blocks.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                result.append({"role": "assistant", "content": content_blocks})

            elif msg.role == Role.CODEX:
                # Other agent's messages as user with clear delimiter
                result.append({
                    "role": "user",
                    "content": f"<agent name=\"codex\">\n{msg.content}\n</agent>",
                })

            elif msg.role == Role.TOOL:
                if msg.tool_owner == Role.CLAUDE:
                    # Native tool_result for Claude's own tool calls
                    for tc in msg.tool_calls:
                        result.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": tc.id,
                                "content": tc.result or tc.error or "",
                            }],
                        })
                else:
                    # Codex's tool results → plain text summary for Claude
                    for tc in msg.tool_calls:
                        summary = tc.result or tc.error or ""
                        result.append({
                            "role": "user",
                            "content": (
                                f"<agent name=\"codex\">\n"
                                f"[Tool {tc.name} result]: {summary[:500]}\n"
                                f"</agent>"
                            ),
                        })

            elif msg.role == Role.SYSTEM:
                result.append({"role": "user", "content": f"[System]: {msg.content}"})

        return result

    def to_openai_messages(self) -> list[dict[str, Any]]:
        """Convert conversation to OpenAI API message format.

        Codex's own messages become 'assistant'.
        Claude messages become 'user' with name='claude'.
        Tool results: native format for Codex's own calls, plain text summary
        for Claude's calls (avoids orphaned tool role messages).
        """
        result: list[dict[str, Any]] = []
        for msg in self._messages:
            if not msg.is_complete:
                continue

            if msg.role == Role.USER:
                result.append({"role": "user", "content": msg.content})

            elif msg.role == Role.CODEX:
                base: dict[str, Any] = {"role": "assistant", "content": msg.content}
                if msg.tool_calls:
                    base["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in msg.tool_calls
                    ]
                result.append(base)

            elif msg.role == Role.CLAUDE:
                # Other agent's messages as user with name metadata
                result.append({
                    "role": "user",
                    "name": "claude",
                    "content": f"<agent name=\"claude\">\n{msg.content}\n</agent>",
                })

            elif msg.role == Role.TOOL:
                if msg.tool_owner == Role.CODEX:
                    # Native tool result for Codex's own tool calls
                    for tc in msg.tool_calls:
                        result.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": tc.result or tc.error or "",
                        })
                else:
                    # Claude's tool results → plain text summary for Codex
                    for tc in msg.tool_calls:
                        summary = tc.result or tc.error or ""
                        result.append({
                            "role": "user",
                            "name": "claude",
                            "content": (
                                f"<agent name=\"claude\">\n"
                                f"[Tool {tc.name} result]: {summary[:500]}\n"
                                f"</agent>"
                            ),
                        })

            elif msg.role == Role.SYSTEM:
                result.append({"role": "user", "content": f"[System]: {msg.content}"})

        return result
