"""Terminal renderer for Conway's Game of Life."""

from __future__ import annotations

from typing import List


def render(grid: List[List[bool]], generation: int) -> None:
    """Clear the terminal and render the grid with a generation counter."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    # ANSI escape: clear screen + move cursor home
    print("\x1b[2J\x1b[H", end="")
    print(f"Generation: {generation} | Size: {width}x{height}")

    alive = "\x1b[32mO\x1b[0m"
    dead = "."

    for row in grid:
        line = "".join(alive if cell else dead for cell in row)
        print(line)