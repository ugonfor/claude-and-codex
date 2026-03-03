"""Tests for experiment mode implementations."""

from unittest.mock import patch

from claude_and_codex.experiment.modes import (
    ExperimentMode,
    ModeConfig,
    get_mode_config,
    parse_experiment_commands,
    CC_SYSTEM,
    CX_SYSTEM,
)


class TestModeConfig:
    def test_cc_mode(self) -> None:
        config = get_mode_config(ExperimentMode.CC)
        assert config.mode == ExperimentMode.CC
        assert config.system_prompt == CC_SYSTEM
        assert config.has_director_layer is False

    def test_cx_mode(self) -> None:
        config = get_mode_config(ExperimentMode.CX)
        assert config.mode == ExperimentMode.CX
        assert config.system_prompt == CX_SYSTEM
        assert config.has_director_layer is False

    def test_dcc_mode(self) -> None:
        config = get_mode_config(ExperimentMode.DCC)
        assert config.mode == ExperimentMode.DCC
        assert config.has_director_layer is True

    def test_cc_prompt_has_agent_a_b(self) -> None:
        assert "DISPATCH_CLAUDE_A" in CC_SYSTEM
        assert "DISPATCH_CLAUDE_B" in CC_SYSTEM
        assert "DISPATCH_CODEX" not in CC_SYSTEM

    def test_cx_prompt_has_claude_codex(self) -> None:
        assert "DISPATCH_CLAUDE" in CX_SYSTEM
        assert "DISPATCH_CODEX" in CX_SYSTEM
        assert "DISPATCH_CLAUDE_A" not in CX_SYSTEM


class TestParseExperimentCommands:
    def test_cc_dispatch_a(self) -> None:
        cmds = parse_experiment_commands(
            "DISPATCH_CLAUDE_A: write the code", ExperimentMode.CC
        )
        assert cmds == [("DISPATCH_CLAUDE_A", "write the code")]

    def test_cc_dispatch_b(self) -> None:
        cmds = parse_experiment_commands(
            "DISPATCH_CLAUDE_B: review the code", ExperimentMode.CC
        )
        assert cmds == [("DISPATCH_CLAUDE_B", "review the code")]

    def test_cc_ignores_codex(self) -> None:
        cmds = parse_experiment_commands(
            "DISPATCH_CODEX: something", ExperimentMode.CC
        )
        assert cmds == []

    def test_cx_dispatch_claude(self) -> None:
        cmds = parse_experiment_commands(
            "DISPATCH_CLAUDE: analyze the file", ExperimentMode.CX
        )
        assert cmds == [("DISPATCH_CLAUDE", "analyze the file")]

    def test_cx_dispatch_codex(self) -> None:
        cmds = parse_experiment_commands(
            "DISPATCH_CODEX: generate tests", ExperimentMode.CX
        )
        assert cmds == [("DISPATCH_CODEX", "generate tests")]

    def test_verify(self) -> None:
        cmds = parse_experiment_commands("VERIFY", ExperimentMode.CC)
        assert cmds == [("VERIFY", "")]

    def test_done_with_summary(self) -> None:
        cmds = parse_experiment_commands(
            "DONE: All tasks complete", ExperimentMode.CX
        )
        assert cmds == [("DONE", "All tasks complete")]

    def test_bare_done(self) -> None:
        cmds = parse_experiment_commands("DONE", ExperimentMode.CX)
        assert cmds == [("DONE", "Task complete.")]

    def test_multiple_cc_commands(self) -> None:
        text = "DISPATCH_CLAUDE_A: write code\nDISPATCH_CLAUDE_B: write tests\nVERIFY"
        cmds = parse_experiment_commands(text, ExperimentMode.CC)
        assert len(cmds) == 3
        assert cmds[0][0] == "DISPATCH_CLAUDE_A"
        assert cmds[1][0] == "DISPATCH_CLAUDE_B"
        assert cmds[2][0] == "VERIFY"

    def test_multiple_cx_commands(self) -> None:
        text = "DISPATCH_CLAUDE: analyze\nDISPATCH_CODEX: generate\nVERIFY\nDONE: finished"
        cmds = parse_experiment_commands(text, ExperimentMode.CX)
        assert len(cmds) == 4
        assert cmds[0][0] == "DISPATCH_CLAUDE"
        assert cmds[3][0] == "DONE"

    def test_ignores_non_command_lines(self) -> None:
        text = "Let me think about this.\nDISPATCH_CLAUDE: do it\nGood plan."
        cmds = parse_experiment_commands(text, ExperimentMode.CX)
        assert len(cmds) == 1
        assert cmds[0] == ("DISPATCH_CLAUDE", "do it")

    def test_dcc_same_as_cx(self) -> None:
        text = "DISPATCH_CLAUDE: task\nDISPATCH_CODEX: task2"
        cx_cmds = parse_experiment_commands(text, ExperimentMode.CX)
        dcc_cmds = parse_experiment_commands(text, ExperimentMode.DCC)
        assert cx_cmds == dcc_cmds


class TestRunExperimentTask:
    @patch("claude_and_codex.experiment.modes.run_verify", return_value=(True, "passed"))
    @patch("claude_and_codex.experiment.modes.run_claude")
    def test_cc_dispatches_to_claude_twice(self, mock_claude, _mock_verify) -> None:
        from claude_and_codex.experiment.benchmarks import Benchmark

        mock_claude.side_effect = [
            # Team Leader response
            "DISPATCH_CLAUDE_A: write code\nDISPATCH_CLAUDE_B: review code\nVERIFY\nDONE: all done",
            # Agent A output
            "code written",
            # Agent B output
            "code reviewed",
        ]

        from claude_and_codex.experiment.modes import run_experiment_task

        benchmark = Benchmark(
            id="test", name="Test", category="codegen",
            description="Do stuff", verify_cmd="echo ok",
        )
        result = run_experiment_task(benchmark, ExperimentMode.CC, "/tmp", max_rounds=2)

        assert result.mode == "cc"
        assert result.final_status == "done"
        assert result.dispatches_per_agent.get("claude_a", 0) >= 1
        assert result.dispatches_per_agent.get("claude_b", 0) >= 1

    @patch("claude_and_codex.experiment.modes.run_verify", return_value=(True, "passed"))
    @patch("claude_and_codex.experiment.modes.run_codex", return_value="codex output")
    @patch("claude_and_codex.experiment.modes.run_claude")
    def test_cx_dispatches_both(self, mock_claude, _mock_codex, _mock_verify) -> None:
        from claude_and_codex.experiment.benchmarks import Benchmark

        mock_claude.side_effect = [
            "DISPATCH_CLAUDE: write\nDISPATCH_CODEX: test\nVERIFY\nDONE: complete",
            "claude output",
        ]

        from claude_and_codex.experiment.modes import run_experiment_task

        benchmark = Benchmark(
            id="test", name="Test", category="codegen",
            description="Do stuff", verify_cmd="echo ok",
        )
        result = run_experiment_task(benchmark, ExperimentMode.CX, "/tmp", max_rounds=2)

        assert result.mode == "cx"
        assert result.final_status == "done"
        assert "claude" in result.dispatches_per_agent
        assert "codex" in result.dispatches_per_agent

    @patch("claude_and_codex.experiment.modes.run_verify", return_value=(True, "passed"))
    @patch("claude_and_codex.experiment.modes.run_codex", return_value="codex output")
    @patch("claude_and_codex.experiment.modes.run_claude")
    def test_dcc_has_director_phase(self, mock_claude, _mock_codex, _mock_verify) -> None:
        from claude_and_codex.experiment.benchmarks import Benchmark

        mock_claude.side_effect = [
            "PLAN:\n1. Build calculator [agent: claude]\nSUCCESS_CRITERIA: tests pass",
            "DISPATCH_CLAUDE: write code\nVERIFY\nDONE: complete",
            "code written",
        ]

        from claude_and_codex.experiment.modes import run_experiment_task

        benchmark = Benchmark(
            id="test", name="Test", category="codegen",
            description="Do stuff", verify_cmd="echo ok",
        )
        result = run_experiment_task(benchmark, ExperimentMode.DCC, "/tmp", max_rounds=2)

        assert result.mode == "dcc"
        assert result.director_plan is not None
        assert result.director_plan_seconds >= 0

    @patch("claude_and_codex.experiment.modes.run_claude")
    def test_max_rounds_respected(self, mock_claude) -> None:
        from claude_and_codex.experiment.benchmarks import Benchmark

        mock_claude.return_value = "Let me think... no commands here."

        from claude_and_codex.experiment.modes import run_experiment_task

        benchmark = Benchmark(
            id="test", name="Test", category="codegen",
            description="Do stuff",
        )
        result = run_experiment_task(benchmark, ExperimentMode.CX, "/tmp", max_rounds=2)

        assert result.final_status == "max_rounds"
        assert result.rounds_used == 2

    @patch("claude_and_codex.experiment.modes.run_claude")
    def test_error_handling(self, mock_claude) -> None:
        from claude_and_codex.experiment.benchmarks import Benchmark

        mock_claude.return_value = "[Error: connection failed]"

        from claude_and_codex.experiment.modes import run_experiment_task

        benchmark = Benchmark(
            id="test", name="Test", category="codegen",
            description="Do stuff",
        )
        result = run_experiment_task(benchmark, ExperimentMode.CX, "/tmp", max_rounds=3)

        assert result.final_status == "error"
        assert result.error is not None
