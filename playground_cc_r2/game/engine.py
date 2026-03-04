"""Conway's Game of Life — Core Engine (by Claude-A)

Rules:
1. Any live cell with 2 or 3 neighbors survives.
2. Any dead cell with exactly 3 neighbors becomes alive.
3. All other live cells die. All other dead cells stay dead.
"""

from __future__ import annotations

Grid = set[tuple[int, int]]


def count_neighbors(x: int, y: int, grid: Grid) -> int:
    """Count the number of live neighbors for cell (x, y)."""
    count = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            if (x + dx, y + dy) in grid:
                count += 1
    return count


def step(grid: Grid) -> Grid:
    """Compute one generation step of the Game of Life.

    Returns a new grid (set of live cell coordinates).
    """
    if not grid:
        return set()

    # Collect all cells that could potentially be alive next generation:
    # all live cells + all their neighbors
    candidates: set[tuple[int, int]] = set()
    for x, y in grid:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                candidates.add((x + dx, y + dy))

    next_grid: Grid = set()
    for cell in candidates:
        n = count_neighbors(cell[0], cell[1], grid)
        if cell in grid:
            # Rule 1: survival
            if n in (2, 3):
                next_grid.add(cell)
        else:
            # Rule 2: birth
            if n == 3:
                next_grid.add(cell)

    return next_grid


def run(grid: Grid, steps: int) -> list[Grid]:
    """Run the simulation for N steps, returning all states."""
    history = [grid]
    current = grid
    for _ in range(steps):
        current = step(current)
        history.append(current)
    return history


def bounding_box(grid: Grid) -> tuple[int, int, int, int]:
    """Return (min_x, min_y, max_x, max_y) bounding box of live cells."""
    if not grid:
        return (0, 0, 0, 0)
    xs = [c[0] for c in grid]
    ys = [c[1] for c in grid]
    return (min(xs), min(ys), max(xs), max(ys))
