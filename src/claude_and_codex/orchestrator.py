"""Orchestrator for managing agent turns and preventing infinite loops."""

from __future__ import annotations

import asyncio
from typing import Callable, Awaitable

from .models import Message, Role, ToolCall, AgentStatus
from .conversation import Conversation
from .agents.base import BaseAgent
from .config import Config


class Orchestrator:
    """Manages agent turn-taking with anti-ping-pong mechanisms.

    Strategy:
    1. On user message: both agents respond (Claude first, then Codex).
    2. After an agent responds: check if the other wants to respond.
    3. Track consecutive non-user turns. Stop at max.
    4. If an agent responds with "PASS", skip it.
    5. Cooldown between agent turns for UI readability.
    """

    def __init__(
        self,
        conversation: Conversation,
        claude: BaseAgent,
        codex: BaseAgent,
        config: Config,
        on_status_change: Callable[[Role, AgentStatus], Awaitable[None]] | None = None,
        on_stream_chunk: Callable[[Role, str, Message], Awaitable[None]] | None = None,
        on_message_complete: Callable[[Message], Awaitable[None]] | None = None,
        on_tool_call: Callable[[Role, ToolCall], Awaitable[None]] | None = None,
        on_new_message: Callable[[Message], Awaitable[None]] | None = None,
    ) -> None:
        self.conversation = conversation
        self.claude = claude
        self.codex = codex
        self.config = config
        self._consecutive_agent_turns = 0

        # UI callbacks
        self.on_status_change = on_status_change
        self.on_stream_chunk = on_stream_chunk
        self.on_message_complete = on_message_complete
        self.on_tool_call = on_tool_call
        self.on_new_message = on_new_message

    async def handle_user_message(self, content: str) -> None:
        """Called when the user sends a message."""
        msg = Message(role=Role.USER, content=content)
        await self.conversation.add_message(msg)
        self._consecutive_agent_turns = 0

        # Both agents respond to user messages
        await self._run_agent(self.claude)
        await asyncio.sleep(self.config.agent_cooldown_seconds)
        await self._run_agent(self.codex)

        # Follow-up loop for free-form collaboration
        await self._follow_up_loop()

    async def _run_agent(self, agent: BaseAgent) -> bool:
        """Run a single agent turn. Returns True if agent produced output."""
        if self._consecutive_agent_turns >= self.config.max_consecutive_agent_turns:
            return False

        recent = self.conversation.messages[-5:]
        if not agent.should_respond(recent):
            return False

        if self.on_status_change:
            await self.on_status_change(agent.role, AgentStatus.THINKING)

        # Create streaming placeholder message
        streaming_msg = Message(
            role=agent.role,
            content="",
            is_complete=False,
        )
        await self.conversation.add_message(streaming_msg)
        if self.on_new_message:
            await self.on_new_message(streaming_msg)

        # Stream response
        full_text = ""
        async for chunk in agent.generate_response():
            full_text += chunk
            streaming_msg.content = full_text
            if self.on_stream_chunk:
                await self.on_stream_chunk(agent.role, chunk, streaming_msg)

        # Check for PASS
        if full_text.strip().upper() == "PASS":
            streaming_msg.content = "[Passed]"
            streaming_msg.is_complete = True
            if self.on_message_complete:
                await self.on_message_complete(streaming_msg)
            if self.on_status_change:
                await self.on_status_change(agent.role, AgentStatus.IDLE)
            return False

        streaming_msg.content = full_text
        streaming_msg.is_complete = True

        # Handle tool calls
        tool_calls = await agent.get_pending_tool_calls()
        if tool_calls:
            streaming_msg.tool_calls = tool_calls
            await self._handle_tool_calls(agent, streaming_msg, tool_calls)

        if self.on_message_complete:
            await self.on_message_complete(streaming_msg)
        if self.on_status_change:
            await self.on_status_change(agent.role, AgentStatus.IDLE)

        self._consecutive_agent_turns += 1
        return True

    async def _handle_tool_calls(
        self,
        agent: BaseAgent,
        msg: Message,
        tool_calls: list[ToolCall],
    ) -> None:
        """Execute tool calls and feed results back."""
        if self.on_status_change:
            await self.on_status_change(agent.role, AgentStatus.TOOL_CALLING)

        for tc in tool_calls:
            result = await agent.tool_registry.execute(tc.name, tc.arguments)
            tc.result = result

            # Fire UI callback AFTER execution so result is available (P3 fix)
            if self.on_tool_call:
                await self.on_tool_call(agent.role, tc)

            # Add tool result to conversation
            tool_msg = Message(
                role=Role.TOOL,
                content=f"Tool {tc.name}: {result[:500]}",
                tool_calls=[tc],
            )
            await self.conversation.add_message(tool_msg)

        # After tool execution, let the same agent continue.
        # Do NOT increment _consecutive_agent_turns here — _run_agent
        # already increments when it produces output (P1 fix).
        await self._run_agent(agent)

    async def _follow_up_loop(self) -> None:
        """Check if either agent wants to continue the conversation."""
        while self._consecutive_agent_turns < self.config.max_consecutive_agent_turns:
            recent = self.conversation.messages[-5:]

            claude_wants = self.claude.should_respond(recent)
            codex_wants = self.codex.should_respond(recent)

            if not claude_wants and not codex_wants:
                break

            if claude_wants:
                responded = await self._run_agent(self.claude)
                if responded:
                    await asyncio.sleep(self.config.agent_cooldown_seconds)
                    continue

            if codex_wants:
                responded = await self._run_agent(self.codex)
                if responded:
                    await asyncio.sleep(self.config.agent_cooldown_seconds)
                    continue

            break
