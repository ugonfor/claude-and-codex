"""Tests for the tool system: registry, file_read, file_write, shell_exec."""

from __future__ import annotations

import sys

import pytest
from pathlib import Path

from claude_and_codex.tools.registry import ToolDefinition, ToolRegistry
from claude_and_codex.tools.file_read import read_file, configure as configure_read
from claude_and_codex.tools.file_write import write_file, configure as configure_write
from claude_and_codex.tools.shell_exec import execute_shell, configure as configure_shell


# --- ToolRegistry ---


async def _dummy_tool(**kwargs) -> str:
    return "ok"


class TestToolRegistry:
    def test_register_and_get(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}},
            execute=_dummy_tool,
        )
        registry.register(tool)
        assert registry.get("test_tool") is tool
        assert registry.get("nonexistent") is None

    def test_all_anthropic_format(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="my_tool",
            description="desc",
            parameters={"type": "object", "properties": {"x": {"type": "string"}}},
            execute=_dummy_tool,
        )
        registry.register(tool)
        result = registry.all_anthropic()
        assert len(result) == 1
        assert result[0]["name"] == "my_tool"
        assert "input_schema" in result[0]

    def test_all_openai_format(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="my_tool",
            description="desc",
            parameters={"type": "object", "properties": {}},
            execute=_dummy_tool,
        )
        registry.register(tool)
        result = registry.all_openai()
        assert len(result) == 1
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "my_tool"

    @pytest.mark.asyncio
    async def test_execute_known_tool(self) -> None:
        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="echo", description="", parameters={},
            execute=_dummy_tool,
        ))
        result = await registry.execute("echo", {})
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self) -> None:
        registry = ToolRegistry()
        result = await registry.execute("missing", {})
        assert "Unknown tool" in result


# --- file_read ---


class TestFileRead:
    @pytest.mark.asyncio
    async def test_read_existing_file(self, tmp_path: Path) -> None:
        f = tmp_path / "hello.txt"
        f.write_text("line1\nline2\nline3\n", encoding="utf-8")
        configure_read(tmp_path)
        result = await read_file("hello.txt")
        assert "1: line1" in result
        assert "2: line2" in result
        assert "3: line3" in result

    @pytest.mark.asyncio
    async def test_read_with_offset_and_limit(self, tmp_path: Path) -> None:
        f = tmp_path / "data.txt"
        f.write_text("\n".join(f"line{i}" for i in range(10)), encoding="utf-8")
        configure_read(tmp_path)
        result = await read_file("data.txt", offset=2, limit=3)
        assert "3: line2" in result
        assert "5: line4" in result
        assert "line0" not in result

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, tmp_path: Path) -> None:
        configure_read(tmp_path)
        result = await read_file("nope.txt")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_read_directory_not_file(self, tmp_path: Path) -> None:
        d = tmp_path / "subdir"
        d.mkdir()
        configure_read(tmp_path)
        result = await read_file("subdir")
        assert "Not a file" in result


# --- file_write ---


class TestFileWrite:
    @pytest.mark.asyncio
    async def test_write_creates_file(self, tmp_path: Path) -> None:
        configure_write(tmp_path)
        result = await write_file("output.txt", "hello world")
        assert "Successfully wrote" in result
        assert (tmp_path / "output.txt").read_text() == "hello world"

    @pytest.mark.asyncio
    async def test_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        configure_write(tmp_path)
        result = await write_file("deep/nested/file.txt", "content")
        assert "Successfully wrote" in result
        assert (tmp_path / "deep" / "nested" / "file.txt").exists()

    @pytest.mark.asyncio
    async def test_write_overwrites_existing(self, tmp_path: Path) -> None:
        f = tmp_path / "existing.txt"
        f.write_text("old", encoding="utf-8")
        configure_write(tmp_path)
        await write_file("existing.txt", "new")
        assert f.read_text() == "new"


# --- shell_exec ---


class TestShellExec:
    @pytest.mark.asyncio
    async def test_simple_command(self, tmp_path: Path) -> None:
        configure_shell(tmp_path)
        result = await execute_shell("echo hello")
        assert "hello" in result
        assert "exit code: 0" in result

    @pytest.mark.asyncio
    async def test_command_failure(self, tmp_path: Path) -> None:
        configure_shell(tmp_path)
        result = await execute_shell("exit 1")
        assert "exit code: 1" in result

    @pytest.mark.asyncio
    async def test_timeout(self, tmp_path: Path) -> None:
        configure_shell(tmp_path)
        # Use a cross-platform long-running command
        cmd = "ping -n 20 127.0.0.1" if sys.platform == "win32" else "sleep 10"
        result = await execute_shell(cmd, timeout=1)
        assert "timed out" in result
