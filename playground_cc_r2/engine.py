"""Conway's Game of Life — core engine."""

from __future__ import annotations

import random
from typing import Set, Tuple

Cell = Tuple[int, int]
Grid = Set[Cell]


# ── Classic patterns ─────────────────────────────────────────────────────────

PATTERNS: dict[str, list[Cell]] = {
    "glider": [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
    "blinker": [(0, 0), (0, 1), (0, 2)],
    "toad": [(0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)],
    "beacon": [(0, 0), (0, 1), (1, 0), (2, 3), (3, 2), (3, 3)],
    "r_pentomino": [(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)],
    "diehard": [(0, 6), (1, 0), (1, 1), (2, 1), (2, 5), (2, 6), (2, 7)],
    "acorn": [(0, 1), (1, 3), (2, 0), (2, 1), (2, 4), (2, 5), (2, 6)],
    "lwss": [  # lightweight spaceship
        (0, 1), (0, 4), (1, 0), (2, 0), (2, 4), (3, 0), (3, 1), (3, 2), (3, 3),
    ],
}


def make_pattern(name: str, offset: tuple[int, int] = (0, 0)) -> Grid:
    """Return a named pattern shifted by offset."""
    if name not in PATTERNS:
        raise ValueError(f"Unknown pattern: {name}. Choose from: {list(PATTERNS.keys())}")
    dr, dc = offset
    return {(r + dr, c + dc) for r, c in PATTERNS[name]}


# ── Grid operations ──────────────────────────────────────────────────────────

def random_grid(rows: int, cols: int, density: float = 0.3) -> Grid:
    """Generate a random grid with given density of live cells."""
    return {
        (r, c)
        for r in range(rows)
        for c in range(cols)
        if random.random() < density
    }


def neighbors(cell: Cell) -> list[Cell]:
    """Return the 8 neighbors of a cell."""
    r, c = cell
    return [
        (r - 1, c - 1), (r - 1, c), (r - 1, c + 1),
        (r,     c - 1),              (r,     c + 1),
        (r + 1, c - 1), (r + 1, c), (r + 1, c + 1),
    ]


def step(grid: Grid) -> Grid:
    """Compute one generation using standard B3/S23 rules.

    - A live cell with 2 or 3 neighbors survives.
    - A dead cell with exactly 3 neighbors becomes alive.
    - All other cells die or stay dead.
    """
    # Count neighbors for every cell that *could* change
    neighbor_counts: dict[Cell, int] = {}
    for cell in grid:
        for nb in neighbors(cell):
            neighbor_counts[nb] = neighbor_counts.get(nb, 0) + 1

    new_grid: Grid = set()
    for cell, count in neighbor_counts.items():
        if count == 3 or (count == 2 and cell in grid):
            new_grid.add(cell)
    return new_grid


def bounded_step(grid: Grid, rows: int, cols: int) -> Grid:
    """Like step(), but clamp to a bounding box [0, rows) x [0, cols)."""
    return {
        (r, c) for r, c in step(grid)
        if 0 <= r < rows and 0 <= c < cols
    }


def grid_to_2d(grid: Grid, rows: int, cols: int) -> list[list[bool]]:
    """Convert sparse grid to dense 2D array."""
    return [
        [((r, c) in grid) for c in range(cols)]
        for r in range(rows)
    ]


def population(grid: Grid) -> int:
    """Return number of live cells."""
    return len(grid)


def bounding_box(grid: Grid) -> tuple[int, int, int, int] | None:
    """Return (min_row, min_col, max_row, max_col) or None if empty."""
    if not grid:
        return None
    rows = [r for r, c in grid]
    cols = [c for r, c in grid]
    return min(rows), min(cols), max(rows), max(cols)


def run(grid: Grid, generations: int, rows: int | None = None, cols: int | None = None) -> list[Grid]:
    """Run the simulation for N generations, returning all states including initial."""
    history = [grid]
    for _ in range(generations):
        if rows is not None and cols is not None:
            grid = bounded_step(grid, rows, cols)
        else:
            grid = step(grid)
        history.append(grid)
    return history
