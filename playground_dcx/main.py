"""Conway's Game of Life - CLI Entry Point.

Run: python main.py [pattern] [--width W] [--height H] [--speed S]
"""

import argparse
import sys
import time

from game import GameOfLife
from patterns import get_pattern, list_patterns
from renderer import render


def parse_args():
    parser = argparse.ArgumentParser(description="Conway's Game of Life")
    parser.add_argument(
        "pattern",
        nargs="?",
        default="glider",
        help=f"Pattern to load. Available: {', '.join(list_patterns())}",
    )
    parser.add_argument("--width", "-W", type=int, default=40, help="Grid width (default: 40)")
    parser.add_argument("--height", "-H", type=int, default=25, help="Grid height (default: 25)")
    parser.add_argument("--speed", "-s", type=float, default=0.15, help="Seconds per generation (default: 0.15)")
    parser.add_argument("--list", "-l", action="store_true", help="List all available patterns and exit")
    parser.add_argument("--generations", "-g", type=int, default=0, help="Max generations (0 = infinite)")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.list:
        print("Available patterns:")
        for name in list_patterns():
            print(f"  - {name}")
        return

    # Create game
    game = GameOfLife(args.width, args.height)

    # Load pattern centered on grid
    try:
        pattern = get_pattern(args.pattern)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Calculate centering offset
    if pattern:
        max_x = max(x for x, y in pattern)
        max_y = max(y for x, y in pattern)
        offset_x = (args.width - max_x) // 2
        offset_y = (args.height - max_y) // 2
    else:
        offset_x = offset_y = 0

    game.load_pattern(pattern, offset_x=offset_x, offset_y=offset_y)

    print(f"Loading '{args.pattern}' pattern on {args.width}x{args.height} grid...")
    print(f"Speed: {args.speed}s/gen | Press Ctrl+C to stop")
    time.sleep(1)

    # Run simulation
    try:
        gen = 0
        while True:
            render(game.get_grid(), game.generation)
            if args.generations > 0 and gen >= args.generations:
                print(f"\nReached {args.generations} generations. Done!")
                break
            time.sleep(args.speed)
            game.step()
            gen += 1
    except KeyboardInterrupt:
        print(f"\n\nStopped at generation {game.generation}.")
        print(f"Final alive cells: {game.count_alive()}")


if __name__ == "__main__":
    main()
