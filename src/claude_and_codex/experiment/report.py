"""Report generation: Markdown tables, JSON export, matplotlib charts."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .metrics import ExperimentRunResult


# ── JSON ────────────────────────────────────────────────────────────────────


def save_results_json(results: list[ExperimentRunResult], path: Path) -> None:
    """Save results as structured JSON."""
    data = {
        "generated_at": datetime.now().isoformat(),
        "runs": [r.to_dict() for r in results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ── Markdown ────────────────────────────────────────────────────────────────


def generate_markdown_report(results: list[ExperimentRunResult]) -> str:
    """Generate a comparison report in Markdown."""
    lines: list[str] = []
    lines.append("# Experiment Report: CC vs CX vs DCC")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Overview table
    lines.append("## Overview")
    lines.append("")
    lines.append("| Benchmark | Mode | Time | Rounds | Dispatches | Verify | Status |")
    lines.append("|-----------|------|------|--------|------------|--------|--------|")

    for r in results:
        dispatch_str = ", ".join(f"{k}:{v}" for k, v in r.dispatches_per_agent.items())
        verify = ""
        if r.final_verification:
            verify = "PASS" if r.final_verification.passed else "FAIL"
        lines.append(
            f"| {r.benchmark_id} | {r.mode} | {r.total_wall_clock_seconds:.1f}s | "
            f"{r.rounds_used}/{r.max_rounds} | {dispatch_str} | {verify} | {r.final_status} |"
        )

    lines.append("")

    # Per-benchmark comparison
    benchmarks = sorted(set(r.benchmark_id for r in results))
    for bid in benchmarks:
        runs = [r for r in results if r.benchmark_id == bid]
        if not runs:
            continue

        lines.append(f"## Benchmark: {runs[0].benchmark_name}")
        lines.append(f"Category: {runs[0].benchmark_category}")
        lines.append("")

        for r in runs:
            lines.append(f"### Mode: {r.mode.upper()}")
            lines.append(f"- **Time**: {r.total_wall_clock_seconds:.1f}s")
            lines.append(f"- **Rounds**: {r.rounds_used}/{r.max_rounds}")
            lines.append(f"- **Dispatches**: {r.total_dispatches}")
            for agent, count in r.dispatches_per_agent.items():
                lines.append(f"  - {agent}: {count}")
            if r.final_verification:
                lines.append(f"- **Verification**: {'PASS' if r.final_verification.passed else 'FAIL'}")
            lines.append(f"- **Status**: {r.final_status}")
            if r.done_summary:
                lines.append(f"- **Summary**: {r.done_summary}")
            if r.director_plan:
                lines.append(f"- **Director Plan** ({r.director_plan_seconds:.1f}s):")
                lines.append(f"  ```")
                lines.append(f"  {r.director_plan[:500]}")
                lines.append(f"  ```")
            if r.error:
                lines.append(f"- **Error**: {r.error}")
            lines.append("")

    # Aggregate stats by mode
    lines.append("## Aggregate Statistics by Mode")
    lines.append("")
    modes = sorted(set(r.mode for r in results))
    lines.append("| Mode | Avg Time | Avg Rounds | Total Dispatches | Pass Rate |")
    lines.append("|------|----------|------------|------------------|-----------|")

    for mode in modes:
        runs = [r for r in results if r.mode == mode]
        avg_time = sum(r.total_wall_clock_seconds for r in runs) / len(runs)
        avg_rounds = sum(r.rounds_used for r in runs) / len(runs)
        total_dispatches = sum(r.total_dispatches for r in runs)
        verified = [r for r in runs if r.final_verification]
        pass_rate = (
            f"{sum(1 for r in verified if r.final_verification.passed)}/{len(verified)}"
            if verified else "N/A"
        )
        lines.append(
            f"| {mode} | {avg_time:.1f}s | {avg_rounds:.1f} | {total_dispatches} | {pass_rate} |"
        )

    lines.append("")

    # Round-by-round detail
    lines.append("## Round-by-Round Detail")
    lines.append("")
    for r in results:
        lines.append(f"### {r.mode.upper()} x {r.benchmark_id}")
        for rd in r.rounds:
            lines.append(f"- **Round {rd.round_number}** ({rd.wall_clock_seconds:.1f}s total, "
                         f"leader: {rd.leader_seconds:.1f}s)")
            for d in rd.dispatches:
                err_tag = " [ERROR]" if d.was_error else ""
                lines.append(f"  - {d.agent}: {d.wall_clock_seconds:.1f}s, "
                             f"{d.output_length} chars{err_tag}")
            if rd.verification:
                vstat = "PASS" if rd.verification.passed else "FAIL"
                lines.append(f"  - verify: {vstat} ({rd.verification.wall_clock_seconds:.1f}s)")
        lines.append("")

    return "\n".join(lines)


# ── Charts (optional matplotlib) ────────────────────────────────────────────


def generate_charts(
    results: list[ExperimentRunResult], output_dir: Path
) -> list[Path]:
    """Generate matplotlib charts. Returns paths to created files.

    Gracefully returns empty list if matplotlib is not installed.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    benchmarks = sorted(set(r.benchmark_id for r in results))
    modes = sorted(set(r.mode for r in results))

    if not benchmarks or not modes:
        return []

    # Chart 1: Wall clock time comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    x_positions = range(len(benchmarks))
    bar_width = 0.25
    colors = {"cc": "#4A90D9", "cx": "#50C878", "dcc": "#FF6B6B"}

    for i, mode in enumerate(modes):
        times = []
        for bid in benchmarks:
            runs = [r for r in results if r.mode == mode and r.benchmark_id == bid]
            times.append(runs[0].total_wall_clock_seconds if runs else 0)
        offset = (i - len(modes) / 2 + 0.5) * bar_width
        bars = ax.bar([x + offset for x in x_positions], times, bar_width,
                      label=mode.upper(), color=colors.get(mode, "#888888"))
        for bar, t in zip(bars, times):
            if t > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                        f"{t:.0f}s", ha="center", va="bottom", fontsize=8)

    ax.set_xlabel("Benchmark")
    ax.set_ylabel("Wall Clock Time (seconds)")
    ax.set_title("Execution Time: CC vs CX vs DCC")
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels(benchmarks, rotation=30, ha="right")
    ax.legend()
    plt.tight_layout()
    p = output_dir / "time_comparison.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    paths.append(p)

    # Chart 2: Rounds used
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, mode in enumerate(modes):
        rounds_data = []
        for bid in benchmarks:
            runs = [r for r in results if r.mode == mode and r.benchmark_id == bid]
            rounds_data.append(runs[0].rounds_used if runs else 0)
        offset = (i - len(modes) / 2 + 0.5) * bar_width
        ax.bar([x + offset for x in x_positions], rounds_data, bar_width,
               label=mode.upper(), color=colors.get(mode, "#888888"))

    ax.set_xlabel("Benchmark")
    ax.set_ylabel("Rounds Used")
    ax.set_title("Rounds Used: CC vs CX vs DCC")
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels(benchmarks, rotation=30, ha="right")
    ax.legend()
    plt.tight_layout()
    p = output_dir / "rounds_comparison.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    paths.append(p)

    # Chart 3: Dispatches per agent (stacked bar)
    fig, ax = plt.subplots(figsize=(10, 6))
    all_agents = sorted(set(
        agent for r in results for agent in r.dispatches_per_agent
    ))
    agent_colors = {
        "claude": "#9B59B6", "claude_a": "#8E44AD", "claude_b": "#6C3483",
        "codex": "#27AE60",
    }
    bottom_vals = {mode: [0.0] * len(benchmarks) for mode in modes}

    for agent in all_agents:
        for i, mode in enumerate(modes):
            counts = []
            for bid in benchmarks:
                runs = [r for r in results if r.mode == mode and r.benchmark_id == bid]
                counts.append(runs[0].dispatches_per_agent.get(agent, 0) if runs else 0)
            offset = (i - len(modes) / 2 + 0.5) * bar_width
            ax.bar([x + offset for x in x_positions], counts, bar_width,
                   bottom=bottom_vals[mode], label=f"{mode.upper()}: {agent}",
                   color=agent_colors.get(agent, "#888888"), alpha=0.7 + i * 0.1)
            bottom_vals[mode] = [b + c for b, c in zip(bottom_vals[mode], counts)]

    ax.set_xlabel("Benchmark")
    ax.set_ylabel("Dispatch Count")
    ax.set_title("Agent Dispatch Patterns")
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels(benchmarks, rotation=30, ha="right")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    p = output_dir / "dispatch_patterns.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    paths.append(p)

    # Chart 4: Pass/Fail heatmap
    fig, ax = plt.subplots(figsize=(8, max(3, len(benchmarks) * 0.8 + 1)))
    heatmap_data = []
    for bid in benchmarks:
        row = []
        for mode in modes:
            runs = [r for r in results if r.mode == mode and r.benchmark_id == bid]
            if runs and runs[0].final_verification:
                row.append(1.0 if runs[0].final_verification.passed else 0.0)
            elif runs and runs[0].final_status == "done":
                row.append(0.5)  # done but no verification
            else:
                row.append(-0.5)  # error or max_rounds
        heatmap_data.append(row)

    from matplotlib.colors import ListedColormap
    cmap = ListedColormap(["#E74C3C", "#F39C12", "#F1C40F", "#2ECC71"])
    im = ax.imshow(heatmap_data, cmap=cmap, aspect="auto", vmin=-0.5, vmax=1.0)

    ax.set_xticks(range(len(modes)))
    ax.set_xticklabels([m.upper() for m in modes])
    ax.set_yticks(range(len(benchmarks)))
    ax.set_yticklabels(benchmarks)
    ax.set_title("Pass/Fail Heatmap")

    for i, row in enumerate(heatmap_data):
        for j, val in enumerate(row):
            label = {1.0: "PASS", 0.0: "FAIL", 0.5: "DONE", -0.5: "ERR"}.get(val, "?")
            ax.text(j, i, label, ha="center", va="center", fontsize=10, fontweight="bold")

    plt.tight_layout()
    p = output_dir / "pass_fail_heatmap.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    paths.append(p)

    return paths
