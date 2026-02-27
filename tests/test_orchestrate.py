"""Tests for orchestrate.py -- free-form collaboration engine."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from claude_and_codex.orchestrate import (
    is_done_or_pass,
    is_error,
    truncate,
    build_context,
    detect_verify_command,
    run_cli,
    run_verify,
    find_cli,
    resolve_image_path,
    elapsed_str,
    handle_command,
    run_claude,
    run_codex,
    PROMPT_MAX_CHARS,
    CODEX_ARG_LIMIT,
)


# ── is_done_or_pass ─────────────────────────────────────────────────────────


class TestIsDoneOrPass:
    def test_done(self) -> None:
        assert is_done_or_pass("DONE") is True

    def test_pass(self) -> None:
        assert is_done_or_pass("PASS") is True

    def test_done_with_period(self) -> None:
        assert is_done_or_pass("DONE.") is True

    def test_done_last_line(self) -> None:
        assert is_done_or_pass("I fixed the bug.\nDONE") is True

    def test_pass_with_explanation(self) -> None:
        assert is_done_or_pass("PASS — waiting for a task") is True

    def test_pass_with_dash(self) -> None:
        assert is_done_or_pass("PASS - Codex already responded") is True

    def test_not_done(self) -> None:
        assert is_done_or_pass("Here are some changes I made") is False

    def test_empty(self) -> None:
        assert is_done_or_pass("") is True


# ── is_error ────────────────────────────────────────────────────────────────


class TestIsError:
    def test_none(self) -> None:
        assert is_error(None) is True

    def test_empty(self) -> None:
        assert is_error("") is True

    def test_error_prefix(self) -> None:
        assert is_error("[Error: something broke]") is True

    def test_no_output(self) -> None:
        assert is_error("[No output from Codex]") is True

    def test_normal(self) -> None:
        assert is_error("Here is my work") is False


# ── truncate ─────────────────────────────────────────────────────────────────


class TestTruncate:
    def test_short_unchanged(self) -> None:
        assert truncate("hello", 100) == "hello"

    def test_long_truncated(self) -> None:
        result = truncate("a" * 100, 50)
        assert result.startswith("a" * 50)
        assert "100 chars total" in result

    def test_default_max(self) -> None:
        assert truncate("x" * 2000) == "x" * 2000
        assert "2001 chars total" in truncate("x" * 2001)


# ── build_context ────────────────────────────────────────────────────────────


class TestBuildContext:
    def test_empty(self) -> None:
        assert build_context([]) == ""

    def test_labels(self) -> None:
        result = build_context([("user", "hi"), ("claude", "yo"), ("codex", "ok")])
        assert "[User]:" in result
        assert "[Claude]:" in result
        assert "[Codex]:" in result

    def test_system_label(self) -> None:
        result = build_context([("system", "verification passed")])
        assert "[System]:" in result

    def test_max_entries(self) -> None:
        history = [("user", f"msg{i}") for i in range(20)]
        result = build_context(history, max_entries=3)
        assert "msg17" in result
        assert "msg0" not in result


# ── detect_verify_command ────────────────────────────────────────────────────


class TestDetectVerify:
    def test_python(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[project]")
        (tmp_path / "tests").mkdir()
        assert detect_verify_command(str(tmp_path)) == "python -m pytest -q 2>&1"

    def test_node(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(json.dumps({"scripts": {"test": "jest"}}))
        assert detect_verify_command(str(tmp_path)) == "npm test 2>&1"

    def test_rust(self, tmp_path: Path) -> None:
        (tmp_path / "Cargo.toml").write_text("[package]")
        assert detect_verify_command(str(tmp_path)) == "cargo test 2>&1"

    def test_go(self, tmp_path: Path) -> None:
        (tmp_path / "go.mod").write_text("module example")
        assert detect_verify_command(str(tmp_path)) == "go test ./... 2>&1"

    def test_unknown(self, tmp_path: Path) -> None:
        assert detect_verify_command(str(tmp_path)) is None


# ── run_cli ──────────────────────────────────────────────────────────────────


class TestRunCli:
    def test_simple(self, tmp_path: Path) -> None:
        result = run_cli("Test", ["python", "-c", "print('hello')"], str(tmp_path), timeout=10)
        assert "hello" in result

    def test_stderr(self, tmp_path: Path) -> None:
        result = run_cli(
            "Test",
            ["python", "-c", "import sys; sys.stderr.write('oops'); sys.exit(1)"],
            str(tmp_path), timeout=10,
        )
        assert "oops" in result

    def test_timeout(self, tmp_path: Path) -> None:
        cmd = ["ping", "-n", "20", "127.0.0.1"] if sys.platform == "win32" else ["sleep", "10"]
        result = run_cli("Test", cmd, str(tmp_path), timeout=1)
        assert "timed out" in result

    def test_stdin(self, tmp_path: Path) -> None:
        result = run_cli(
            "Test",
            ["python", "-c", "import sys; print(sys.stdin.read().strip())"],
            str(tmp_path), timeout=10, stdin_text="piped",
        )
        assert "piped" in result

    def test_no_output(self, tmp_path: Path) -> None:
        result = run_cli("Test", ["python", "-c", "pass"], str(tmp_path), timeout=10)
        assert "No output" in result


# ── run_verify ───────────────────────────────────────────────────────────────


class TestRunVerify:
    def test_no_command(self, tmp_path: Path) -> None:
        passed, _ = run_verify(str(tmp_path))
        assert passed is True

    def test_passing(self, tmp_path: Path) -> None:
        passed, output = run_verify(str(tmp_path), "echo OK")
        assert passed is True
        assert "OK" in output

    def test_failing(self, tmp_path: Path) -> None:
        passed, _ = run_verify(str(tmp_path), "exit 1")
        assert passed is False


# ── resolve_image_path ───────────────────────────────────────────────────────


class TestResolveImagePath:
    def test_valid(self, tmp_path: Path) -> None:
        img = tmp_path / "photo.png"
        img.write_text("")
        assert resolve_image_path(str(img), str(tmp_path)) == str(img)

    def test_relative(self, tmp_path: Path) -> None:
        (tmp_path / "pic.jpg").write_text("")
        result = resolve_image_path("pic.jpg", str(tmp_path))
        assert result is not None

    def test_nonexistent(self, tmp_path: Path) -> None:
        assert resolve_image_path("nope.png", str(tmp_path)) is None


# ── elapsed_str ──────────────────────────────────────────────────────────────


class TestElapsedStr:
    def test_seconds(self) -> None:
        result = elapsed_str(time.time() - 5.5)
        assert "s" in result

    def test_minutes(self) -> None:
        result = elapsed_str(time.time() - 125)
        assert "2m" in result


# ── handle_command ───────────────────────────────────────────────────────────


class TestHandleCommand:
    def _call(self, user_input, **kwargs):
        defaults = dict(
            max_turns=12, verify_cmd=None, images=[], cwd="/tmp",
            history=[], claude_ok=True, codex_ok=True,
        )
        defaults.update(kwargs)
        return handle_command(user_input, **defaults)

    def test_help(self) -> None:
        is_cmd, _, _, _ = self._call("/help")
        assert is_cmd is True

    def test_status(self) -> None:
        is_cmd, _, _, _ = self._call("/status")
        assert is_cmd is True

    def test_clear(self) -> None:
        history = [("user", "hi")]
        self._call("/clear", history=history)
        assert len(history) == 0

    def test_turns(self) -> None:
        _, turns, _, _ = self._call("/turns 5")
        assert turns == 5

    def test_verify(self) -> None:
        _, _, cmd, _ = self._call("/verify make test")
        assert cmd == "make test"

    def test_cd(self, tmp_path: Path) -> None:
        _, _, _, new_cwd = self._call(f"/cd {tmp_path}")
        assert new_cwd == str(tmp_path)

    def test_unknown_slash(self) -> None:
        is_cmd, _, _, _ = self._call("/foobar")
        assert is_cmd is True

    def test_non_command(self) -> None:
        is_cmd, _, _, _ = self._call("regular message")
        assert is_cmd is False


# ── run_claude / run_codex ──────────────────────────────────────────────────


class TestRunClaude:
    @patch("claude_and_codex.orchestrate.find_cli", return_value=None)
    def test_not_found(self, _) -> None:
        assert "not found" in run_claude("hello", "/tmp")

    @patch("claude_and_codex.orchestrate.run_cli", return_value="done")
    @patch("claude_and_codex.orchestrate.find_cli", return_value="/usr/bin/claude")
    def test_pipes_stdin(self, _, mock_run) -> None:
        run_claude("my prompt", "/tmp")
        assert mock_run.call_args[1]["stdin_text"] == "my prompt"

    @patch("claude_and_codex.orchestrate.run_cli", return_value="done")
    @patch("claude_and_codex.orchestrate.find_cli", return_value="/usr/bin/claude")
    def test_with_images(self, _, mock_run) -> None:
        run_claude("task", "/tmp", images=["a.png"])
        assert "a.png" in mock_run.call_args[1]["stdin_text"]


class TestRunCodex:
    @patch("claude_and_codex.orchestrate.find_cli", return_value=None)
    def test_not_found(self, _) -> None:
        assert "not found" in run_codex("hello", "/tmp")

    @patch("claude_and_codex.orchestrate.run_cli", return_value="done")
    @patch("claude_and_codex.orchestrate.find_cli", return_value="/usr/bin/codex")
    def test_short_prompt(self, _, mock_run) -> None:
        run_codex("short", "/tmp")
        # run_cli called with positional args: name, args_list, cwd
        call_args = mock_run.call_args
        args_list = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("args", [])
        assert "short" in args_list
