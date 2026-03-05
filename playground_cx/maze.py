"""Maze generation using recursive backtracking (DFS).

Produces a 2D grid where:
  - 0 = open path
  - 1 = wall

The maze has exactly one entrance (top-left) and one exit (bottom-right).
"""

from __future__ import annotations

import random
from typing import List, Tuple

Grid = List[List[int]]
Cell = Tuple[int, int]

WALL = 1
PATH = 0


def generate_maze(rows: int = 21, cols: int = 21, seed: int | None = None) -> Grid:
    """Generate a maze using recursive backtracking.

    Args:
        rows: Must be odd (will be forced odd if even).
        cols: Must be odd (will be forced odd if even).
        seed: Random seed for reproducibility.

    Returns:
        2D grid with walls (1) and paths (0).
    """
    if seed is not None:
        random.seed(seed)

    # Force odd dimensions so walls align to grid
    rows = rows if rows % 2 == 1 else rows + 1
    cols = cols if cols % 2 == 1 else cols + 1

    # Start with all walls
    grid: Grid = [[WALL] * cols for _ in range(rows)]

    def _carve(r: int, c: int) -> None:
        grid[r][c] = PATH
        directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        random.shuffle(directions)
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 < nr < rows and 0 < nc < cols and grid[nr][nc] == WALL:
                # Carve the wall between current and neighbor
                grid[r + dr // 2][c + dc // 2] = PATH
                _carve(nr, nc)

    # Start carving from (1, 1)
    _carve(1, 1)

    # Ensure entrance and exit
    grid[0][1] = PATH  # entrance at top
    grid[rows - 1][cols - 2] = PATH  # exit at bottom

    return grid


def render_maze(grid: Grid) -> str:
    """Render maze as a string using block characters."""
    symbols = {WALL: "##", PATH: "  "}
    lines = []
    for row in grid:
        lines.append("".join(symbols[cell] for cell in row))
    return "\n".join(lines)


def get_entrance(grid: Grid) -> Cell:
    """Return the entrance cell coordinates."""
    return (0, 1)


def get_exit(grid: Grid) -> Cell:
    """Return the exit cell coordinates."""
    return (len(grid) - 1, len(grid[0]) - 2)


if __name__ == "__main__":
    maze = generate_maze(21, 41, seed=42)
    print(render_maze(maze))
    print(f"\nEntrance: {get_entrance(maze)}")
    print(f"Exit: {get_exit(maze)}")
