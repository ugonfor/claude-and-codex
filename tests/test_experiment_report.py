"""Tests for experiment report generation."""

from datetime import datetime
from pathlib import Path

from claude_and_codex.experiment.metrics import (
    ExperimentRunResult, RoundMetrics, DispatchMetrics, VerificationResult,
)
from claude_and_codex.experiment.report import (
    generate_markdown_report, generate_charts, save_results_json,
)


def _make_result(mode: str, benchmark_id: str, passed: bool = True) -> ExperimentRunResult:
    """Helper to create a test result."""
    return ExperimentRunResult(
        run_id=f"{mode}_{benchmark_id}_test",
        benchmark_id=benchmark_id,
        benchmark_name=f"Benchmark {benchmark_id}",
        benchmark_category="codegen",
        mode=mode,
        started_at=datetime(2026, 3, 3, 14, 0, 0),
        finished_at=datetime(2026, 3, 3, 14, 1, 0),
        total_wall_clock_seconds=60.0,
        rounds_used=3,
        max_rounds=8,
        rounds=[
            RoundMetrics(
                round_number=1,
                leader_seconds=5.0,
                dispatches=[
                    DispatchMetrics(agent="claude", command="write code",
                                    wall_clock_seconds=20.0, output_length=500),
                ],
                verification=VerificationResult(passed=passed, output="ok", wall_clock_seconds=2.0),
            ),
        ],
        final_verification=VerificationResult(passed=passed, output="ok", wall_clock_seconds=2.0),
        final_status="done",
        done_summary="All complete",
        team_leader_calls=3,
        total_dispatches=3,
        dispatches_per_agent={"claude": 2, "codex": 1},
    )


class TestMarkdownReport:
    def test_generates_overview_table(self) -> None:
        results = [_make_result("cc", "b1"), _make_result("cx", "b1")]
        md = generate_markdown_report(results)
        assert "| Benchmark | Mode |" in md
        assert "| b1 |" in md

    def test_per_benchmark_sections(self) -> None:
        results = [_make_result("cc", "b1"), _make_result("cx", "b2")]
        md = generate_markdown_report(results)
        assert "## Benchmark: Benchmark b1" in md
        assert "## Benchmark: Benchmark b2" in md

    def test_aggregate_stats(self) -> None:
        results = [
            _make_result("cc", "b1"),
            _make_result("cc", "b2"),
            _make_result("cx", "b1"),
        ]
        md = generate_markdown_report(results)
        assert "## Aggregate Statistics by Mode" in md
        assert "| cc |" in md
        assert "| cx |" in md

    def test_round_by_round_detail(self) -> None:
        results = [_make_result("cx", "b1")]
        md = generate_markdown_report(results)
        assert "## Round-by-Round Detail" in md
        assert "Round 1" in md

    def test_empty_results(self) -> None:
        md = generate_markdown_report([])
        assert "# Experiment Report" in md


class TestJsonReport:
    def test_save_and_load(self, tmp_path: Path) -> None:
        results = [_make_result("cc", "b1")]
        path = tmp_path / "results.json"
        save_results_json(results, path)

        import json
        data = json.loads(path.read_text())
        assert "runs" in data
        assert len(data["runs"]) == 1
        assert data["runs"][0]["mode"] == "cc"

    def test_round_trip_fields(self, tmp_path: Path) -> None:
        result = _make_result("cx", "b2")
        path = tmp_path / "results.json"
        save_results_json([result], path)

        import json
        data = json.loads(path.read_text())
        run = data["runs"][0]
        assert run["benchmark_id"] == "b2"
        assert run["total_wall_clock_seconds"] == 60.0
        assert run["rounds_used"] == 3
        assert run["dispatches_per_agent"]["claude"] == 2


class TestCharts:
    def test_generates_chart_files(self, tmp_path: Path) -> None:
        results = [
            _make_result("cc", "b1"),
            _make_result("cx", "b1"),
            _make_result("dcc", "b1"),
        ]
        paths = generate_charts(results, tmp_path / "charts")
        # May be empty if matplotlib not installed
        if paths:
            assert len(paths) == 4
            for p in paths:
                assert p.exists()
                assert p.suffix == ".png"

    def test_empty_results(self, tmp_path: Path) -> None:
        paths = generate_charts([], tmp_path / "charts")
        assert paths == []
