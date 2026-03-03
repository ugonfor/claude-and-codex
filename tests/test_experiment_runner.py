"""Tests for experiment runner and sandbox."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from claude_and_codex.experiment.benchmarks import Benchmark
from claude_and_codex.experiment.metrics import ExperimentRunResult
from claude_and_codex.experiment.modes import ExperimentMode
from claude_and_codex.experiment.runner import ExperimentPlan, ExperimentRunner
from claude_and_codex.experiment.sandbox import (
    Sandbox, create_sandbox, cleanup_sandbox, preserve_sandbox,
)


class TestSandbox:
    def test_create_sandbox(self, tmp_path: Path) -> None:
        b = Benchmark(id="test", name="Test", category="codegen", description="task")
        sandbox = create_sandbox(b, "cx", tmp_path)
        assert sandbox.root.exists()
        assert sandbox.benchmark_id == "test"
        assert sandbox.mode == "cx"
        assert "cx_test_" in sandbox.run_id

    def test_setup_files_written(self, tmp_path: Path) -> None:
        b = Benchmark(
            id="test", name="Test", category="bugfix", description="fix",
            setup_files={"main.py": "print('hi')", "tests/test_main.py": "assert True"},
        )
        sandbox = create_sandbox(b, "cc", tmp_path)
        assert (sandbox.root / "main.py").read_text() == "print('hi')"
        assert (sandbox.root / "tests" / "test_main.py").read_text() == "assert True"

    def test_cleanup_sandbox(self, tmp_path: Path) -> None:
        b = Benchmark(id="test", name="Test", category="codegen", description="task")
        sandbox = create_sandbox(b, "cx", tmp_path)
        assert sandbox.root.exists()
        cleanup_sandbox(sandbox)
        assert not sandbox.root.exists()

    def test_preserve_sandbox(self, tmp_path: Path) -> None:
        b = Benchmark(
            id="test", name="Test", category="codegen", description="task",
            setup_files={"hello.txt": "world"},
        )
        sandbox = create_sandbox(b, "cx", tmp_path / "sandboxes")
        output_dir = tmp_path / "preserved"
        dest = preserve_sandbox(sandbox, output_dir)
        assert dest.exists()
        assert (dest / "hello.txt").read_text() == "world"

    def test_create_sandbox_tempdir(self) -> None:
        b = Benchmark(id="test", name="Test", category="codegen", description="task")
        sandbox = create_sandbox(b, "cx")
        assert sandbox.root.exists()
        cleanup_sandbox(sandbox)


class TestExperimentPlan:
    def test_defaults(self) -> None:
        plan = ExperimentPlan()
        assert len(plan.modes) == 3  # all three modes
        assert plan.repeats == 1
        assert plan.max_rounds == 8

    def test_custom_config(self) -> None:
        plan = ExperimentPlan(
            modes=[ExperimentMode.CC],
            repeats=3,
            max_rounds=4,
        )
        assert len(plan.modes) == 1
        assert plan.repeats == 3
        assert plan.max_rounds == 4


class TestExperimentRunner:
    @patch("claude_and_codex.experiment.runner.run_experiment_task")
    def test_runs_all_combinations(self, mock_run, tmp_path: Path) -> None:
        mock_run.return_value = ExperimentRunResult(
            run_id="test", benchmark_id="b1", benchmark_name="B1",
            benchmark_category="codegen", mode="cx",
            final_status="done",
        )
        benchmarks = [
            Benchmark(id="b1", name="B1", category="codegen", description="t1"),
            Benchmark(id="b2", name="B2", category="bugfix", description="t2"),
        ]
        plan = ExperimentPlan(
            modes=[ExperimentMode.CC, ExperimentMode.CX],
            benchmarks=benchmarks,
            repeats=1,
            results_dir=tmp_path,
        )
        runner = ExperimentRunner(plan)
        results = runner.run_all()

        assert len(results) == 4  # 2 benchmarks x 2 modes x 1 repeat
        assert mock_run.call_count == 4

    @patch("claude_and_codex.experiment.runner.run_experiment_task")
    def test_save_results_json(self, mock_run, tmp_path: Path) -> None:
        mock_run.return_value = ExperimentRunResult(
            run_id="test", benchmark_id="b1", benchmark_name="B1",
            benchmark_category="codegen", mode="cx",
            final_status="done",
        )
        plan = ExperimentPlan(
            modes=[ExperimentMode.CX],
            benchmarks=[Benchmark(id="b1", name="B1", category="codegen", description="t1")],
            results_dir=tmp_path,
        )
        runner = ExperimentRunner(plan)
        runner.run_all()
        path = runner.save_results(tmp_path)

        assert path.exists()
        data = json.loads(path.read_text())
        assert "runs" in data
        assert len(data["runs"]) == 1

    @patch("claude_and_codex.experiment.runner.run_experiment_task")
    def test_error_in_run_captured(self, mock_run, tmp_path: Path) -> None:
        mock_run.side_effect = RuntimeError("boom")
        plan = ExperimentPlan(
            modes=[ExperimentMode.CX],
            benchmarks=[Benchmark(id="b1", name="B1", category="codegen", description="t1")],
            results_dir=tmp_path,
        )
        runner = ExperimentRunner(plan)
        results = runner.run_all()
        assert len(results) == 1
        assert results[0].final_status == "error"
        assert "boom" in results[0].error
