"""Conway's Game of Life — Core Engine.

Built by Claude-Worker as part of a collaborative project with Codex-Worker.
"""

from __future__ import annotations
from typing import Set, Tuple

Cell = Tuple[int, int]


class LifeGrid:
    """Sparse representation of a Game of Life grid."""

    def __init__(self, alive: Set[Cell] | None = None):
        self.alive: Set[Cell] = set(alive) if alive else set()

    def add(self, row: int, col: int) -> None:
        self.alive.add((row, col))

    def remove(self, row: int, col: int) -> None:
        self.alive.discard((row, col))

    def is_alive(self, row: int, col: int) -> bool:
        return (row, col) in self.alive

    def toggle(self, row: int, col: int) -> None:
        cell = (row, col)
        if cell in self.alive:
            self.alive.discard(cell)
        else:
            self.alive.add(cell)

    def neighbors(self, row: int, col: int) -> int:
        """Count live neighbors of a cell."""
        count = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                if (row + dr, col + dc) in self.alive:
                    count += 1
        return count

    def step(self) -> "LifeGrid":
        """Advance one generation. Returns a new LifeGrid."""
        # Candidates: all live cells + their neighbors
        candidates: Set[Cell] = set()
        for r, c in self.alive:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    candidates.add((r + dr, c + dc))

        new_alive: Set[Cell] = set()
        for cell in candidates:
            n = self.neighbors(*cell)
            if cell in self.alive:
                # Survival: 2 or 3 neighbors
                if n in (2, 3):
                    new_alive.add(cell)
            else:
                # Birth: exactly 3 neighbors
                if n == 3:
                    new_alive.add(cell)

        return LifeGrid(new_alive)

    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Return (min_row, min_col, max_row, max_col) of live cells."""
        if not self.alive:
            return (0, 0, 0, 0)
        rows = [r for r, _ in self.alive]
        cols = [c for _, c in self.alive]
        return (min(rows), min(cols), max(rows), max(cols))

    def population(self) -> int:
        return len(self.alive)

    def render(self, rows: int = 30, cols: int = 60, offset_r: int = 0, offset_c: int = 0) -> str:
        """Render the grid as a string for terminal display."""
        lines = []
        for r in range(offset_r, offset_r + rows):
            line = ""
            for c in range(offset_c, offset_c + cols):
                line += "#" if (r, c) in self.alive else "."
            lines.append(line)
        return "\n".join(lines)

    def place_pattern(self, pattern: Set[Cell], offset_r: int = 0, offset_c: int = 0) -> None:
        """Place a pattern onto the grid at a given offset."""
        for r, c in pattern:
            self.alive.add((r + offset_r, c + offset_c))

    def __repr__(self) -> str:
        return f"LifeGrid(population={self.population()})"
