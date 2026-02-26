"""Codex agent implementation.

Supports two backends:
1. ChatGPT OAuth → Responses API at chatgpt.com/backend-api/codex (streaming)
2. Standard API key → OpenAI Chat Completions API (streaming)
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import AsyncIterator

from openai import AsyncOpenAI

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
        model: str = "gpt-5.3-codex",
        account_id: str = "",
        use_chatgpt_oauth: bool = False,
    ) -> None:
        super().__init__(Role.CODEX, conversation, tool_registry)
        self.api_key = api_key
        self.model = model
        self.account_id = account_id
        self.use_chatgpt_oauth = use_chatgpt_oauth
        self._pending_tool_calls: list[ToolCall] = []

        if not use_chatgpt_oauth:
            self.client = AsyncOpenAI(api_key=api_key)

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
        if self.use_chatgpt_oauth:
            async for chunk in self._generate_chatgpt_oauth():
                yield chunk
        else:
            async for chunk in self._generate_openai_standard():
                yield chunk

    async def _generate_chatgpt_oauth(self) -> AsyncIterator[str]:
        """Use ChatGPT backend Responses API (streaming SSE)."""
        self.status = AgentStatus.STREAMING
        self._pending_tool_calls = []

        # Build input in Responses API format
        messages = self.conversation.to_openai_messages()
        input_items = []
        for msg in messages:
            if msg.get("role") == "system":
                continue
            role = msg["role"] if msg["role"] in ("user", "assistant") else "user"
            input_items.append({
                "type": "message",
                "role": role,
                "content": msg.get("content", ""),
            })

        tools = self.tool_registry.all_openai()
        body: dict = {
            "model": self.model,
            "instructions": self.build_system_prompt(),
            "input": input_items,
            "store": False,
            "stream": True,
        }
        if tools:
            body["tools"] = tools

        try:
            req = urllib.request.Request(
                "https://chatgpt.com/backend-api/codex/responses",
                data=json.dumps(body).encode(),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "ChatGPT-Account-ID": self.account_id,
                },
            )
            resp = urllib.request.urlopen(req, timeout=120)

            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data: "):
                    continue
                payload = line[6:]
                if payload == "[DONE]":
                    break
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    continue

                etype = event.get("type", "")
                if etype == "response.output_text.delta":
                    delta = event.get("delta", "")
                    if delta:
                        yield delta
                elif etype == "response.completed":
                    response = event.get("response", {})
                    for item in response.get("output", []):
                        if item.get("type") == "function_call":
                            try:
                                args = json.loads(item.get("arguments", "{}"))
                            except json.JSONDecodeError:
                                args = {}
                            self._pending_tool_calls.append(
                                ToolCall(
                                    id=item.get("call_id", item.get("id", "")),
                                    name=item.get("name", ""),
                                    arguments=args,
                                )
                            )

        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
            self.status = AgentStatus.ERROR
            if isinstance(e, urllib.error.HTTPError):
                body_text = e.read().decode("utf-8", errors="replace")[:300]
                yield f"\n[Error {e.code}: {body_text}]"
            else:
                yield f"\n[Error: {e}]"
            return

        self.status = AgentStatus.IDLE

    async def _generate_openai_standard(self) -> AsyncIterator[str]:
        """Use standard OpenAI Chat Completions API (streaming)."""
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

            tool_call_accumulators: dict[int, dict] = {}

            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta is None:
                    continue
                if delta.content:
                    yield delta.content
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in tool_call_accumulators:
                            tool_call_accumulators[idx] = {
                                "id": "", "name": "", "arguments": "",
                            }
                        acc = tool_call_accumulators[idx]
                        if tc_delta.id:
                            acc["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                acc["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                acc["arguments"] += tc_delta.function.arguments

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
