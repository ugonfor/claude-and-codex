"""Analyze a Game of Life simulation -- population dynamics and pattern detection."""

from __future__ import annotations

from life import Grid, glider, blinker, glider_gun, random_soup


def analyze_run(grid: Grid, steps: int = 200) -> dict:
    """Run a simulation and collect statistics."""
    populations = []
    seen_states: dict[frozenset, int] = {}

    for gen in range(steps):
        state = frozenset(grid.cells)
        populations.append(len(grid.cells))

        if state in seen_states:
            cycle_start = seen_states[state]
            cycle_len = gen - cycle_start
            return {
                "generations": gen,
                "final_population": len(grid.cells),
                "peak_population": max(populations),
                "min_population": min(populations),
                "populations": populations,
                "outcome": "cycle",
                "cycle_start": cycle_start,
                "cycle_length": cycle_len,
            }

        if len(grid.cells) == 0:
            return {
                "generations": gen,
                "final_population": 0,
                "peak_population": max(populations),
                "min_population": 0,
                "populations": populations,
                "outcome": "extinction",
            }

        seen_states[state] = gen
        grid = grid.step()

    populations.append(len(grid.cells))
    return {
        "generations": steps,
        "final_population": len(grid.cells),
        "peak_population": max(populations),
        "min_population": min(populations),
        "populations": populations,
        "outcome": "timeout",
    }


def sparkline(values: list[int], width: int = 60) -> str:
    """Render a list of ints as a text sparkline."""
    if not values:
        return ""
    mn, mx = min(values), max(values)
    chars = " _.-~*=#"
    if mx == mn:
        return chars[0] * min(len(values), width)

    # Downsample if needed
    if len(values) > width:
        step = len(values) / width
        sampled = [values[int(i * step)] for i in range(width)]
    else:
        sampled = values

    return "".join(
        chars[min(int((v - mn) / (mx - mn) * (len(chars) - 1)), len(chars) - 1)]
        for v in sampled
    )


def print_report(stats: dict) -> None:
    """Pretty-print simulation analysis."""
    print("=" * 60)
    print("  Game of Life -- Simulation Analysis")
    print("  Built by Claude & Codex")
    print("=" * 60)
    print(f"  Outcome:      {stats['outcome']}")
    print(f"  Generations:  {stats['generations']}")
    print(f"  Peak pop:     {stats['peak_population']}")
    print(f"  Min pop:      {stats['min_population']}")
    print(f"  Final pop:    {stats['final_population']}")

    if stats["outcome"] == "cycle":
        print(f"  Cycle start:  gen {stats['cycle_start']}")
        print(f"  Cycle length: {stats['cycle_length']}")

    print()
    print("  Population over time:")
    print(f"  [{sparkline(stats['populations'])}]")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    pattern = sys.argv[1] if len(sys.argv) > 1 else "glider"

    if pattern == "blinker":
        g = Grid(10, 10)
        blinker(g, 4, 4)
    elif pattern == "glider":
        g = Grid(30, 30)
        glider(g, 1, 1)
    elif pattern == "gun":
        g = Grid(60, 30)
        glider_gun(g, 1, 1)
    elif pattern == "random":
        g = Grid(40, 20)
        random_soup(g, 0.25)
    else:
        print(f"Unknown: {pattern}")
        sys.exit(1)

    stats = analyze_run(g)
    print_report(stats)
