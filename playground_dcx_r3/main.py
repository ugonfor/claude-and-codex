"""ASCII Game of Life demo runner."""

from __future__ import annotations

import argparse
import random
import sys

from life_display import animate, print_frame
from life_engine import GameOfLife


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Conway's Game of Life (ASCII)")
    parser.add_argument("--width", type=int, default=40, help="Grid width")
    parser.add_argument("--height", type=int, default=20, help="Grid height")
    parser.add_argument("--pattern", type=str, default="glider", help="Named pattern")
    parser.add_argument("--list-patterns", action="store_true", help="List built-in patterns and exit")
    parser.add_argument("--random", action="store_true", help="Use random initial population")
    parser.add_argument("--density", type=float, default=0.2, help="Density for random fill (0..1)")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for random fill")
    parser.add_argument("--steps", type=int, default=200, help="Number of steps (0 = infinite)")
    parser.add_argument("--delay", type=float, default=0.1, help="Seconds between frames")
    parser.add_argument("--alive", type=str, default="#", help="Character for alive cell")
    parser.add_argument("--dead", type=str, default=".", help="Character for dead cell")
    parser.add_argument("--border", action="store_true", help="Draw border around grid")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear screen between frames")
    parser.add_argument("--no-ansi", action="store_true", help="Disable ANSI clear, use system clear")
    parser.add_argument("--snapshot", action="store_true", help="Print a single frame and exit")
    parser.add_argument("--no-stats", action="store_true", help="Hide generation and population")
    return parser


def create_game(args: argparse.Namespace) -> GameOfLife:
    if args.random:
        if not (0.0 <= args.density <= 1.0):
            raise ValueError("--density must be between 0 and 1")
        game = GameOfLife(width=args.width, height=args.height)
        rng = random.Random(args.seed)
        for r in range(args.height):
            for c in range(args.width):
                if rng.random() < args.density:
                    game.set_cell(r, c, True)
        return game

    return GameOfLife.from_pattern(args.pattern, width=args.width, height=args.height)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_patterns:
        for name in GameOfLife.available_patterns():
            print(name)
        return 0

    try:
        game = create_game(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.snapshot:
        print_frame(
            game,
            alive=args.alive,
            dead=args.dead,
            border=args.border,
            show_stats=not args.no_stats,
        )
        return 0

    steps = None if args.steps == 0 else args.steps
    animate(
        game,
        steps=steps,
        delay=args.delay,
        alive=args.alive,
        dead=args.dead,
        border=args.border,
        show_stats=not args.no_stats,
        clear=not args.no_clear,
        use_ansi=not args.no_ansi,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
