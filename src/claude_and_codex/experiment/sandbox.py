"""Isolated sandbox environments for experiment runs."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .benchmarks import Benchmark


@dataclass
class Sandbox:
    """An isolated directory for one experiment run."""
    run_id: str
    root: Path
    benchmark_id: str
    mode: str


def create_sandbox(
    benchmark: Benchmark,
    mode: str,
    base_dir: Path | None = None,
) -> Sandbox:
    """Create an isolated directory and write benchmark setup files into it."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{mode}_{benchmark.id}_{ts}"
    if base_dir:
        root = base_dir / run_id
        root.mkdir(parents=True, exist_ok=True)
    else:
        root = Path(tempfile.mkdtemp(prefix=f"exp_{run_id}_"))

    for filename, content in benchmark.setup_files.items():
        filepath = root / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")

    return Sandbox(run_id=run_id, root=root, benchmark_id=benchmark.id, mode=mode)


def cleanup_sandbox(sandbox: Sandbox) -> None:
    """Remove the sandbox directory."""
    if sandbox.root.exists():
        shutil.rmtree(sandbox.root, ignore_errors=True)


def preserve_sandbox(sandbox: Sandbox, output_dir: Path) -> Path:
    """Copy sandbox contents to a permanent location."""
    dest = output_dir / sandbox.run_id
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(sandbox.root, dest)
    return dest
