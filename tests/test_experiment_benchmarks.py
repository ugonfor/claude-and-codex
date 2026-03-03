"""Tests for experiment benchmark loading."""

from pathlib import Path

from claude_and_codex.experiment.benchmarks import Benchmark, load_benchmark, load_benchmarks


class TestBenchmark:
    def test_load_valid_json(self, tmp_path: Path) -> None:
        data = '{"id":"test","name":"Test","category":"codegen","description":"Do stuff"}'
        p = tmp_path / "test.json"
        p.write_text(data, encoding="utf-8")
        b = load_benchmark(p)
        assert b.id == "test"
        assert b.name == "Test"
        assert b.category == "codegen"
        assert b.description == "Do stuff"
        assert b.setup_files == {}
        assert b.timeout_seconds == 600

    def test_load_with_setup_files(self, tmp_path: Path) -> None:
        import json
        data = {
            "id": "bf", "name": "Bug Fix", "category": "bugfix",
            "description": "Fix the bug",
            "setup_files": {"main.py": "print('hi')"},
            "verify_cmd": "python -m pytest -q",
            "expected_outcomes": ["tests pass"],
            "timeout_seconds": 120,
        }
        p = tmp_path / "bf.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        b = load_benchmark(p)
        assert b.setup_files == {"main.py": "print('hi')"}
        assert b.verify_cmd == "python -m pytest -q"
        assert b.timeout_seconds == 120

    def test_load_benchmarks_from_dir(self, tmp_path: Path) -> None:
        for i in range(3):
            p = tmp_path / f"bench_{i}.json"
            p.write_text(
                f'{{"id":"b{i}","name":"B{i}","category":"codegen","description":"task {i}"}}',
                encoding="utf-8",
            )
        benchmarks = load_benchmarks(tmp_path)
        assert len(benchmarks) == 3
        ids = [b.id for b in benchmarks]
        assert "b0" in ids
        assert "b1" in ids
        assert "b2" in ids

    def test_load_benchmarks_empty_dir(self, tmp_path: Path) -> None:
        benchmarks = load_benchmarks(tmp_path)
        assert benchmarks == []

    def test_load_benchmarks_missing_dir(self) -> None:
        benchmarks = load_benchmarks(Path("/nonexistent/path"))
        assert benchmarks == []

    def test_load_real_benchmarks(self) -> None:
        """Verify the bundled benchmark JSON files are valid."""
        benchmarks = load_benchmarks()
        assert len(benchmarks) >= 4
        ids = {b.id for b in benchmarks}
        assert "codegen_calculator" in ids
        assert "bugfix_off_by_one" in ids
        assert "refactor_extract_fn" in ids
        assert "testwrite_utils" in ids

    def test_benchmark_categories(self) -> None:
        benchmarks = load_benchmarks()
        categories = {b.category for b in benchmarks}
        assert "codegen" in categories
        assert "bugfix" in categories
        assert "refactor" in categories
        assert "testwrite" in categories
