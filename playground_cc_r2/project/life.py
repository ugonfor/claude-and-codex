"""Game of Life Scene — Uses Canvas engine (by Claude-A)

Conway's Game of Life rendered as an animated ASCII scene.
Adapted to match Claude-B's scene interface: scene_fn(canvas, frame)
"""

from __future__ import annotations

from engine import Canvas

# Type alias
Grid = set[tuple[int, int]]


def _step(grid: Grid) -> Grid:
    """One generation of Conway's Game of Life."""
    if not grid:
        return set()

    candidates: set[tuple[int, int]] = set()
    for x, y in grid:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                candidates.add((x + dx, y + dy))

    next_grid: Grid = set()
    for cx, cy in candidates:
        n = sum(
            1 for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            if (dx or dy) and (cx + dx, cy + dy) in grid
        )
        if (cx, cy) in grid:
            if n in (2, 3):
                next_grid.add((cx, cy))
        elif n == 3:
            next_grid.add((cx, cy))

    return next_grid


def _glider(x: int, y: int) -> Grid:
    return {(x+1, y), (x+2, y+1), (x, y+2), (x+1, y+2), (x+2, y+2)}


def _r_pentomino(x: int, y: int) -> Grid:
    return {(x+1, y), (x+2, y), (x, y+1), (x+1, y+1), (x+1, y+2)}


def _acorn(x: int, y: int) -> Grid:
    return {
        (x, y+1), (x+1, y+3), (x+2, y), (x+2, y+1),
        (x+2, y+4), (x+2, y+5), (x+2, y+6)
    }


# Persistent state across frames
_life_state: dict[str, object] = {}


def scene_life(canvas: Canvas, frame: int):
    """Game of Life scene — matches Claude-B's interface: scene_fn(canvas, frame)."""
    canvas.clear()
    cx, cy = canvas.width // 4, canvas.height // 2

    # Initialize or reset on frame 0
    if frame == 0 or "grid" not in _life_state:
        grid: Grid = set()
        grid |= _r_pentomino(cx, cy)
        grid |= _glider(cx - 10, cy - 5)
        grid |= _glider(cx + 10, cy - 3)
        grid |= _glider(cx - 5, cy + 5)
        grid |= _acorn(cx + 15, cy + 2)
        _life_state["grid"] = grid

    grid = _life_state["grid"]

    # Draw live cells
    for x, y in grid:
        if canvas.in_bounds(x, y):
            canvas.set_pixel(x, y, "#")

    # Draw title
    title = f"[ Game of Life | Alive: {len(grid)} | Gen: {frame} ]"
    canvas.draw_text(2, 0, title)

    # Step the simulation
    grid = _step(grid)
    if not grid:
        grid = _r_pentomino(cx, cy)
        grid |= _glider(cx - 10, cy - 5)

    _life_state["grid"] = grid
