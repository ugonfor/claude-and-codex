"""Benchmark task definitions and loading."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


BENCHMARKS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "benchmarks"


@dataclass
class Benchmark:
    """A single benchmark task definition."""
    id: str
    name: str
    category: str                           # codegen, bugfix, refactor, testwrite
    description: str                        # full task given to the Team Leader
    setup_files: dict[str, str] = field(default_factory=dict)  # filename -> content
    verify_cmd: str = ""
    expected_outcomes: list[str] = field(default_factory=list)
    timeout_seconds: int = 600


def load_benchmark(path: Path) -> Benchmark:
    """Load a single benchmark from a JSON file."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return Benchmark(
        id=data["id"],
        name=data["name"],
        category=data["category"],
        description=data["description"],
        setup_files=data.get("setup_files", {}),
        verify_cmd=data.get("verify_cmd", ""),
        expected_outcomes=data.get("expected_outcomes", []),
        timeout_seconds=data.get("timeout_seconds", 600),
    )


def load_benchmarks(directory: Path | None = None) -> list[Benchmark]:
    """Load all benchmarks from the benchmarks/ directory."""
    d = directory or BENCHMARKS_DIR
    if not d.is_dir():
        return []
    benchmarks = []
    for p in sorted(d.glob("*.json")):
        benchmarks.append(load_benchmark(p))
    return benchmarks
