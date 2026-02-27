"""Tests for conversation export (JSONL and Markdown)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from claude_and_codex.models import Message, Role, ToolCall
from claude_and_codex.export import to_jsonl, to_markdown, export_conversation


def _sample_messages() -> list[Message]:
    tc = ToolCall(id="tc-1", name="read_file", arguments={"path": "x.py"}, result="code here")
    return [
        Message(role=Role.USER, content="Hello"),
        Message(role=Role.CLAUDE, content="Hi, let me read that file.", tool_calls=[tc]),
        Message(role=Role.TOOL, content="Tool result", tool_calls=[tc], tool_owner=Role.CLAUDE),
        Message(role=Role.CODEX, content="Looks good to me."),
    ]


class TestToJsonl:
    def test_produces_valid_jsonl(self) -> None:
        msgs = _sample_messages()
        output = to_jsonl(msgs)
        lines = output.strip().split("\n")
        assert len(lines) == 4
        for line in lines:
            obj = json.loads(line)
            assert "role" in obj
            assert "content" in obj
            assert "timestamp" in obj

    def test_includes_tool_calls(self) -> None:
        msgs = _sample_messages()
        output = to_jsonl(msgs)
        lines = output.strip().split("\n")
        claude_msg = json.loads(lines[1])
        assert "tool_calls" in claude_msg
        assert claude_msg["tool_calls"][0]["name"] == "read_file"

    def test_includes_tool_owner(self) -> None:
        msgs = _sample_messages()
        output = to_jsonl(msgs)
        lines = output.strip().split("\n")
        tool_msg = json.loads(lines[2])
        assert tool_msg["tool_owner"] == "claude"

    def test_empty_messages(self) -> None:
        assert to_jsonl([]) == ""


class TestToMarkdown:
    def test_has_header(self) -> None:
        md = to_markdown(_sample_messages())
        assert "# Conversation Export" in md

    def test_contains_all_roles(self) -> None:
        md = to_markdown(_sample_messages())
        assert "### User" in md
        assert "### Claude" in md
        assert "### Codex" in md
        assert "### Tool" in md

    def test_contains_tool_call_details(self) -> None:
        md = to_markdown(_sample_messages())
        assert "`read_file`" in md
        assert "code here" in md

    def test_empty_messages(self) -> None:
        md = to_markdown([])
        assert "# Conversation Export" in md


class TestExportConversation:
    def test_export_both_formats(self, tmp_path: Path) -> None:
        msgs = _sample_messages()
        paths = export_conversation(msgs, tmp_path / "out", fmt="both")
        assert len(paths) == 2
        assert any(p.suffix == ".jsonl" for p in paths)
        assert any(p.suffix == ".md" for p in paths)
        for p in paths:
            assert p.exists()

    def test_export_jsonl_only(self, tmp_path: Path) -> None:
        msgs = _sample_messages()
        paths = export_conversation(msgs, tmp_path / "out", fmt="jsonl")
        assert len(paths) == 1
        assert paths[0].suffix == ".jsonl"

    def test_export_markdown_only(self, tmp_path: Path) -> None:
        msgs = _sample_messages()
        paths = export_conversation(msgs, tmp_path / "out", fmt="markdown")
        assert len(paths) == 1
        assert paths[0].suffix == ".md"

    def test_creates_output_dir(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "does" / "not" / "exist"
        export_conversation(_sample_messages(), out_dir, fmt="jsonl")
        assert out_dir.exists()
