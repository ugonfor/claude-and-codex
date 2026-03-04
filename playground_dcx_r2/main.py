"""Conway's Game of Life - simple terminal demo.

Run:
  python main.py --pattern glider

Codex-Worker contribution to collaborative demo.
"""

from __future__ import annotations

import argparse
import os
import random
import time
from typing import Iterable, Tuple

from life_engine import LifeGrid
import patterns


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def render(grid: LifeGrid, rows: int, cols: int, offset_r: int, offset_c: int) -> str:
    lines = []
    alive = grid.alive
    for r in range(offset_r, offset_r + rows):
        line = ""
        for c in range(offset_c, offset_c + cols):
            line += "O" if (r, c) in alive else " "
        lines.append(line)
    return "\n".join(lines)


def seed_random(grid: LifeGrid, rows: int, cols: int, density: float, seed: int | None) -> None:
    rng = random.Random(seed)
    for r in range(rows):
        for c in range(cols):
            if rng.random() < density:
                grid.add(r, c)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Conway's Game of Life (terminal demo)")
    parser.add_argument("--pattern", default="glider", help="Pattern name")
    parser.add_argument("--rows", type=int, default=30)
    parser.add_argument("--cols", type=int, default=60)
    parser.add_argument("--offset-r", type=int, default=0)
    parser.add_argument("--offset-c", type=int, default=0)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--delay", type=float, default=0.1)
    parser.add_argument("--random", action="store_true", help="Seed random grid")
    parser.add_argument("--density", type=float, default=0.25, help="Density for random seed")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--list", action="store_true", help="List available patterns")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.list:
        for name in patterns.list_patterns():
            print(name)
        return 0

    grid = LifeGrid()

    if args.random:
        seed_random(grid, args.rows, args.cols, args.density, args.seed)
    else:
        try:
            pattern = patterns.get_pattern(args.pattern)
        except KeyError as exc:
            print(exc)
            print("Available patterns:")
            for name in patterns.list_patterns():
                print(f"  {name}")
            return 2
        # Center pattern in viewport
        min_r = min(r for r, _ in pattern)
        min_c = min(c for _, c in pattern)
        max_r = max(r for r, _ in pattern)
        max_c = max(c for _, c in pattern)
        pat_h = max_r - min_r + 1
        pat_w = max_c - min_c + 1
        start_r = args.offset_r + max(0, (args.rows - pat_h) // 2)
        start_c = args.offset_c + max(0, (args.cols - pat_w) // 2)
        grid.place_pattern(pattern, start_r - min_r, start_c - min_c)

    for step in range(args.steps):
        clear_screen()
        print(f"Conway's Game of Life | step {step} | pop {grid.population()}")
        print(render(grid, args.rows, args.cols, args.offset_r, args.offset_c))
        time.sleep(args.delay)
        grid = grid.step()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())