#!/usr/bin/env python3
"""Conway's Game of Life — Main Entry Point

Collaborative build:
  - Engine: Claude-A
  - Renderer & Patterns: Claude-B

Usage:
    python -m game.main [pattern] [generations] [delay]

Examples:
    python -m game.main glider 100 0.1
    python -m game.main gosper_gun 200 0.05
    python -m game.main random 150 0.08
"""

from __future__ import annotations

import os
import sys
import time

from game.engine import Grid, step


def main():
    # Import Claude-B's modules
    try:
        from game import patterns, renderer
    except ImportError as e:
        print(f"Waiting for Claude-B's modules... ({e})")
        print("Claude-B should create game/renderer.py and game/patterns.py")
        sys.exit(1)

    # Parse arguments
    pattern_name = sys.argv[1] if len(sys.argv) > 1 else "glider"
    generations = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    delay = float(sys.argv[3]) if len(sys.argv) > 3 else 0.12

    # Terminal size for rendering
    try:
        cols, rows = os.get_terminal_size()
    except OSError:
        cols, rows = 80, 24
    width = cols - 2
    height = rows - 4  # leave room for status line

    # Get the initial pattern
    pattern_func = getattr(patterns, pattern_name, None)
    if pattern_func is None:
        available = [
            name for name in dir(patterns)
            if not name.startswith("_") and callable(getattr(patterns, name))
        ]
        print(f"Unknown pattern: {pattern_name}")
        print(f"Available: {', '.join(available)}")
        sys.exit(1)

    # Center the pattern
    cx, cy = width // 2, height // 2
    grid: Grid = pattern_func(cx, cy)

    print(f"\033[2J\033[H")  # clear screen
    print(f"Conway's Game of Life | Pattern: {pattern_name} | Gen: 0/{generations}")
    print(f"Built by Claude-A (engine) & Claude-B (renderer + patterns)")
    print(f"Press Ctrl+C to quit\n")
    time.sleep(1.5)

    # Run the simulation
    try:
        for gen in range(generations):
            # Render current state
            frame = renderer.render(grid, width, height)

            # Display
            sys.stdout.write(f"\033[H")  # cursor to top
            status = f" Gen {gen}/{generations} | Alive: {len(grid)} | Pattern: {pattern_name} "
            sys.stdout.write(f"\033[1;36m{'=' * width}\033[0m\n")
            sys.stdout.write(frame)
            sys.stdout.write(f"\033[1;36m{'=' * width}\033[0m\n")
            sys.stdout.write(f"\033[1;33m{status:^{width}}\033[0m\n")
            sys.stdout.flush()

            # Step
            grid = step(grid)

            # Check for extinction
            if not grid:
                print(f"\n\033[1;31mExtinction at generation {gen + 1}!\033[0m")
                break

            time.sleep(delay)

    except KeyboardInterrupt:
        pass

    print(f"\n\033[1;32mSimulation complete.\033[0m")


if __name__ == "__main__":
    main()
