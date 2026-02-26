from __future__ import annotations

import pytest

from claude_and_codex.conversation import Conversation
from claude_and_codex.models import Message, Role, ToolCall


@pytest.mark.asyncio
async def test_to_anthropic_messages_respects_tool_owner_scoping() -> None:
    conversation = Conversation()

    claude_tool_call = ToolCall(
        id="claude-tool-1",
        name="read_file",
        arguments={"path": "README.md"},
        result="README contents",
    )
    codex_tool_call = ToolCall(
        id="codex-tool-1",
        name="execute_shell",
        arguments={"command": "ls"},
        result="file_a.py\nfile_b.py",
    )

    await conversation.add_message(Message(role=Role.USER, content="Inspect repo"))
    await conversation.add_message(
        Message(
            role=Role.CLAUDE,
            content="I will read the README.",
            tool_calls=[claude_tool_call],
        )
    )
    await conversation.add_message(
        Message(
            role=Role.TOOL,
            content="Tool read_file: README contents",
            tool_calls=[claude_tool_call],
            tool_owner=Role.CLAUDE,
        )
    )
    await conversation.add_message(
        Message(
            role=Role.CODEX,
            content="I will list the directory.",
            tool_calls=[codex_tool_call],
        )
    )
    await conversation.add_message(
        Message(
            role=Role.TOOL,
            content="Tool execute_shell: file_a.py",
            tool_calls=[codex_tool_call],
            tool_owner=Role.CODEX,
        )
    )

    messages = conversation.to_anthropic_messages()

    assert messages[0] == {"role": "user", "content": "Inspect repo"}
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"][1]["type"] == "tool_use"
    assert messages[1]["content"][1]["id"] == "claude-tool-1"

    claude_tool_results = [
        m
        for m in messages
        if isinstance(m.get("content"), list)
        and m["content"]
        and m["content"][0].get("type") == "tool_result"
    ]
    assert len(claude_tool_results) == 1
    assert claude_tool_results[0]["content"][0]["type"] == "tool_result"
    assert claude_tool_results[0]["content"][0]["tool_use_id"] == "claude-tool-1"

    codex_tool_summaries = [
        m
        for m in messages
        if isinstance(m.get("content"), str)
        and "[Tool execute_shell result]" in m["content"]
    ]
    assert len(codex_tool_summaries) == 1


@pytest.mark.asyncio
async def test_to_openai_messages_respects_tool_owner_scoping() -> None:
    conversation = Conversation()

    codex_tool_call = ToolCall(
        id="codex-tool-1",
        name="write_file",
        arguments={"path": "out.txt", "content": "hello"},
        result="ok",
    )
    claude_tool_call = ToolCall(
        id="claude-tool-1",
        name="read_file",
        arguments={"path": "README.md"},
        result="README contents",
    )

    await conversation.add_message(Message(role=Role.USER, content="Make changes"))
    await conversation.add_message(
        Message(
            role=Role.CODEX,
            content="Creating a file now.",
            tool_calls=[codex_tool_call],
        )
    )
    await conversation.add_message(
        Message(
            role=Role.TOOL,
            content="Tool write_file: ok",
            tool_calls=[codex_tool_call],
            tool_owner=Role.CODEX,
        )
    )
    await conversation.add_message(
        Message(
            role=Role.CLAUDE,
            content="I will inspect docs.",
            tool_calls=[claude_tool_call],
        )
    )
    await conversation.add_message(
        Message(
            role=Role.TOOL,
            content="Tool read_file: README contents",
            tool_calls=[claude_tool_call],
            tool_owner=Role.CLAUDE,
        )
    )

    messages = conversation.to_openai_messages()

    assert messages[0] == {"role": "user", "content": "Make changes"}
    assert messages[1]["role"] == "assistant"
    assert messages[1]["tool_calls"][0]["id"] == "codex-tool-1"

    tool_results = [m for m in messages if m.get("role") == "tool"]
    assert len(tool_results) == 1
    assert tool_results[0]["tool_call_id"] == "codex-tool-1"

    claude_tool_summaries = [
        m
        for m in messages
        if m.get("role") == "user"
        and m.get("name") == "claude"
        and "[Tool read_file result]" in m.get("content", "")
    ]
    assert len(claude_tool_summaries) == 1
