"""Experiment runner: orchestrates benchmark x mode combinations."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .benchmarks import Benchmark, load_benchmarks
from .metrics import ExperimentRunResult
from .modes import ExperimentMode, run_experiment_task
from .sandbox import create_sandbox, cleanup_sandbox, preserve_sandbox
from ..orchestrate import find_cli

console = Console()


@dataclass
class ExperimentPlan:
    """Configuration for an experiment run."""
    modes: list[ExperimentMode] = field(default_factory=lambda: list(ExperimentMode))
    benchmarks: list[Benchmark] = field(default_factory=list)
    repeats: int = 1
    max_rounds: int = 8
    results_dir: Path = Path("results")
    preserve_sandboxes: bool = False


class ExperimentRunner:
    """Runs all mode x benchmark x repeat combinations."""

    def __init__(self, plan: ExperimentPlan):
        self.plan = plan
        self.results: list[ExperimentRunResult] = []

    def run_all(self) -> list[ExperimentRunResult]:
        """Run all combinations sequentially."""
        codex_ok = find_cli("codex") is not None
        total = len(self.plan.benchmarks) * len(self.plan.modes) * self.plan.repeats
        i = 0

        for benchmark in self.plan.benchmarks:
            for mode in self.plan.modes:
                for repeat in range(self.plan.repeats):
                    i += 1
                    console.print(f"\n[bold]Run {i}/{total}[/bold]: "
                                  f"[cyan]{mode.value}[/cyan] x "
                                  f"[yellow]{benchmark.id}[/yellow]"
                                  f"{f' (repeat {repeat+1})' if self.plan.repeats > 1 else ''}")
                    result = self.run_single(mode, benchmark, codex_ok)
                    self.results.append(result)

        return self.results

    def run_single(
        self, mode: ExperimentMode, benchmark: Benchmark, codex_ok: bool = True,
    ) -> ExperimentRunResult:
        """Run one specific combination."""
        # Create isolated sandbox
        sandbox_base = self.plan.results_dir / "sandboxes" if self.plan.preserve_sandboxes else None
        sandbox = create_sandbox(benchmark, mode.value, sandbox_base)

        try:
            result = run_experiment_task(
                benchmark=benchmark,
                mode=mode,
                sandbox_dir=str(sandbox.root),
                max_rounds=self.plan.max_rounds,
                codex_ok=codex_ok,
            )
            result.sandbox_path = str(sandbox.root)

            # Preserve sandbox if requested
            if self.plan.preserve_sandboxes:
                dest = self.plan.results_dir / "sandboxes"
                dest.mkdir(parents=True, exist_ok=True)
                preserve_sandbox(sandbox, dest)

            return result
        except Exception as e:
            return ExperimentRunResult(
                run_id=sandbox.run_id,
                benchmark_id=benchmark.id,
                benchmark_name=benchmark.name,
                benchmark_category=benchmark.category,
                mode=mode.value,
                final_status="error",
                error=str(e),
                sandbox_path=str(sandbox.root),
            )
        finally:
            if not self.plan.preserve_sandboxes:
                cleanup_sandbox(sandbox)

    def save_results(self, output_dir: Path | None = None) -> Path:
        """Save all results as JSON."""
        d = output_dir or self.plan.results_dir
        d.mkdir(parents=True, exist_ok=True)
        path = d / "results.json"
        data = {
            "experiment_id": f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "config": {
                "modes": [m.value for m in self.plan.modes],
                "benchmarks": [b.id for b in self.plan.benchmarks],
                "repeats": self.plan.repeats,
                "max_rounds": self.plan.max_rounds,
            },
            "runs": [r.to_dict() for r in self.results],
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path


# ── CLI entry point ─────────────────────────────────────────────────────────


def run_experiment_cli(argv: list[str]) -> None:
    """Parse CLI args and run the experiment."""
    # Parse simple args
    modes_str = _get_arg(argv, "--modes", "cc,cx,dcc")
    benchmarks_str = _get_arg(argv, "--benchmarks", "")
    repeats = int(_get_arg(argv, "--repeats", "1"))
    max_rounds = int(_get_arg(argv, "--max-rounds", "8"))
    output = _get_arg(argv, "--output", "results")
    preserve = "--preserve-sandboxes" in argv

    # Resolve modes
    mode_map = {m.value: m for m in ExperimentMode}
    modes = []
    for name in modes_str.split(","):
        name = name.strip().lower()
        if name in mode_map:
            modes.append(mode_map[name])
        else:
            console.print(f"[red]Unknown mode: {name}[/red]")
            sys.exit(1)

    # Load benchmarks
    all_benchmarks = load_benchmarks()
    if benchmarks_str:
        wanted = {b.strip() for b in benchmarks_str.split(",")}
        benchmarks = [b for b in all_benchmarks if b.id in wanted]
        missing = wanted - {b.id for b in benchmarks}
        if missing:
            console.print(f"[red]Unknown benchmarks: {', '.join(missing)}[/red]")
            sys.exit(1)
    else:
        benchmarks = all_benchmarks

    if not benchmarks:
        console.print("[red]No benchmarks found. Check benchmarks/ directory.[/red]")
        sys.exit(1)

    # Check CLIs
    claude_ok = find_cli("claude") is not None
    codex_ok = find_cli("codex") is not None
    if not claude_ok:
        console.print("[red]Claude CLI not found. Cannot run experiments.[/red]")
        sys.exit(1)

    # Show plan
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(output) / ts

    console.print(Panel(
        f"Modes: {', '.join(m.value for m in modes)}\n"
        f"Benchmarks: {', '.join(b.id for b in benchmarks)}\n"
        f"Repeats: {repeats}\n"
        f"Max rounds: {max_rounds}\n"
        f"Codex CLI: {'available' if codex_ok else 'NOT available'}\n"
        f"Output: {results_dir}",
        title="[bold]Experiment Plan[/bold]",
        border_style="cyan",
    ))

    plan = ExperimentPlan(
        modes=modes,
        benchmarks=benchmarks,
        repeats=repeats,
        max_rounds=max_rounds,
        results_dir=results_dir,
        preserve_sandboxes=preserve,
    )

    runner = ExperimentRunner(plan)
    results = runner.run_all()

    # Save results
    results_dir.mkdir(parents=True, exist_ok=True)
    json_path = runner.save_results(results_dir)
    console.print(f"\n[green]Results saved: {json_path}[/green]")

    # Generate report
    from .report import generate_markdown_report, generate_charts, save_results_json

    md = generate_markdown_report(results)
    md_path = results_dir / "report.md"
    md_path.write_text(md, encoding="utf-8")
    console.print(f"[green]Report: {md_path}[/green]")

    chart_paths = generate_charts(results, results_dir / "charts")
    if chart_paths:
        console.print(f"[green]Charts: {len(chart_paths)} generated in {results_dir / 'charts'}[/green]")

    # Summary table
    _print_summary(results)


def _print_summary(results: list[ExperimentRunResult]) -> None:
    """Print a summary table to the console."""
    table = Table(title="Experiment Results")
    table.add_column("Benchmark", style="yellow")
    table.add_column("Mode", style="cyan")
    table.add_column("Time", justify="right")
    table.add_column("Rounds", justify="right")
    table.add_column("Dispatches", justify="right")
    table.add_column("Verify", justify="center")
    table.add_column("Status")

    for r in results:
        dispatch_str = ", ".join(f"{k}:{v}" for k, v in r.dispatches_per_agent.items())
        verify = ""
        if r.final_verification:
            verify = "[green]PASS[/green]" if r.final_verification.passed else "[red]FAIL[/red]"
        status_style = {"done": "green", "max_rounds": "yellow", "error": "red"}.get(r.final_status, "white")
        table.add_row(
            r.benchmark_id,
            r.mode,
            f"{r.total_wall_clock_seconds:.1f}s",
            f"{r.rounds_used}/{r.max_rounds}",
            dispatch_str,
            verify,
            f"[{status_style}]{r.final_status}[/{status_style}]",
        )

    console.print()
    console.print(table)


def _get_arg(argv: list[str], flag: str, default: str) -> str:
    """Get a CLI argument value."""
    for i, arg in enumerate(argv):
        if arg == flag and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith(f"{flag}="):
            return arg.split("=", 1)[1]
    return default
