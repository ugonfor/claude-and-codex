"""Run Conway's Game of Life in a terminal."""

from __future__ import annotations

import argparse
import random
import sys
import time

from game import GameOfLife, GLIDER, BLINKER, BLOCK, LWSS
from renderer import Renderer


HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"

PATTERNS = {
    "glider": GLIDER,
    "blinker": BLINKER,
    "block": BLOCK,
    "lwss": LWSS,
}


def pattern_size(pattern: list[tuple[int, int]]) -> tuple[int, int]:
    max_r = max(r for r, _ in pattern)
    max_c = max(c for _, c in pattern)
    return max_r + 1, max_c + 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Conway's Game of Life (terminal)")
    parser.add_argument("--width", type=int, default=60)
    parser.add_argument("--height", type=int, default=20)
    parser.add_argument("--density", type=float, default=0.3)
    parser.add_argument("--delay", type=float, default=0.1)
    parser.add_argument("--steps", type=int, default=0, help="0 = run forever")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--pattern", choices=sorted(PATTERNS.keys()), default=None)
    parser.add_argument("--alive", type=str, default="O")
    parser.add_argument("--dead", type=str, default=".")
    parser.add_argument("--border", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.width <= 0 or args.height <= 0:
        raise SystemExit("width/height must be positive")

    if args.seed is not None:
        random.seed(args.seed)

    game = GameOfLife(args.width, args.height)

    if args.pattern is not None:
        game.clear()
        pattern = PATTERNS[args.pattern]
        p_h, p_w = pattern_size(pattern)
        offset_r = max(0, (args.height - p_h) // 2)
        offset_c = max(0, (args.width - p_w) // 2)
        game.add_pattern(pattern, offset_r, offset_c)
    else:
        game.randomize(args.density)

    renderer = Renderer(game, alive_char=args.alive, dead_char=args.dead, border=args.border)

    print(HIDE_CURSOR, end="")
    try:
        iterations = None if args.steps == 0 else args.steps
        i = 0
        while iterations is None or i < iterations:
            renderer.clear_screen()
            print(renderer.render_frame(), end="")
            sys.stdout.flush()
            game.step()
            i += 1
            if iterations is None or i < iterations:
                time.sleep(max(0.0, args.delay))
    except KeyboardInterrupt:
        pass
    finally:
        print(SHOW_CURSOR, end="")
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
