"""Run a Conway's Game of Life simulation in the terminal."""

from __future__ import annotations

import argparse
import random
import time

from life import Grid, blinker, glider, glider_gun, random_soup
from renderer import display


PATTERNS = {
    "glider": glider,
    "blinker": blinker,
    "gun": glider_gun,
    "random": random_soup,
}


def build_grid(width: int, height: int, pattern: str, density: float) -> Grid:
    grid = Grid(width, height)
    if pattern == "random":
        random_soup(grid, density=density)
    else:
        PATTERNS[pattern](grid)
    return grid


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Conway's Game of Life (ASCII)")
    parser.add_argument("--width", type=int, default=40)
    parser.add_argument("--height", type=int, default=20)
    parser.add_argument(
        "--pattern",
        choices=sorted(PATTERNS.keys()),
        default="glider",
        help="Starting pattern.",
    )
    parser.add_argument("--density", type=float, default=0.3)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--delay", type=float, default=0.08)
    parser.add_argument("--alive", default="#")
    parser.add_argument("--dead", default=".")
    parser.add_argument("--no-clear", action="store_true")
    parser.add_argument("--seed", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    grid = build_grid(args.width, args.height, args.pattern, args.density)

    step = 0
    while True:
        display(grid, alive=args.alive, dead=args.dead, clear=not args.no_clear)
        grid = grid.step()
        step += 1
        if args.steps >= 0 and step >= args.steps:
            break
        time.sleep(args.delay)


if __name__ == "__main__":
    main()
