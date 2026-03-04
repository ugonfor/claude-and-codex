"""Conway's Game of Life — core engine."""

from __future__ import annotations

import random
from typing import Iterator

PATTERNS: dict[str, list[tuple[int, int]]] = {
    "glider": [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)],
    "blinker": [(1, 0), (1, 1), (1, 2)],
    "pulsar": [
        # Quarter pattern, mirrored 4 ways
        (2, 1), (3, 1), (4, 1), (6, 1), (7, 1), (8, 1),
        (1, 2), (1, 3), (1, 4), (1, 6), (1, 7), (1, 8),
        (2, 5), (3, 5), (4, 5), (6, 5), (7, 5), (8, 5),
        (5, 2), (5, 3), (5, 4), (5, 6), (5, 7), (5, 8),
        (9, 2), (9, 3), (9, 4), (9, 6), (9, 7), (9, 8),
        (2, 9), (3, 9), (4, 9), (6, 9), (7, 9), (8, 9),
    ],
    "beacon": [(0, 0), (1, 0), (0, 1), (3, 2), (2, 3), (3, 3)],
    "toad": [(1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1)],
    "lwss": [  # lightweight spaceship
        (1, 0), (4, 0), (0, 1), (0, 2), (4, 2), (0, 3), (1, 3), (2, 3), (3, 3),
    ],
}


class Grid:
    """A Game of Life grid with toroidal (wrapping) boundaries."""

    def __init__(
        self,
        width: int,
        height: int,
        cells: set[tuple[int, int]] | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self.cells: set[tuple[int, int]] = set(cells) if cells else set()

    def alive(self, x: int, y: int) -> bool:
        return (x % self.width, y % self.height) in self.cells

    def toggle(self, x: int, y: int) -> None:
        coord = (x % self.width, y % self.height)
        if coord in self.cells:
            self.cells.discard(coord)
        else:
            self.cells.add(coord)

    @property
    def population(self) -> int:
        return len(self.cells)

    def _neighbours(self, x: int, y: int) -> int:
        count = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                if ((x + dx) % self.width, (y + dy) % self.height) in self.cells:
                    count += 1
        return count

    def step(self) -> Grid:
        """Return the next generation grid."""
        candidates: set[tuple[int, int]] = set()
        for x, y in self.cells:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    candidates.add(((x + dx) % self.width, (y + dy) % self.height))

        new_cells: set[tuple[int, int]] = set()
        for x, y in candidates:
            n = self._neighbours(x, y)
            if (x, y) in self.cells:
                if n in (2, 3):
                    new_cells.add((x, y))
            else:
                if n == 3:
                    new_cells.add((x, y))

        return Grid(self.width, self.height, new_cells)

    def generations(self) -> Iterator[Grid]:
        """Yield successive generations forever."""
        current = self
        while True:
            yield current
            current = current.step()

    @classmethod
    def from_pattern(
        cls,
        name: str,
        width: int = 40,
        height: int = 20,
    ) -> Grid:
        """Create a grid with a named pattern centered."""
        if name == "random":
            cells = {
                (x, y)
                for x in range(width)
                for y in range(height)
                if random.random() < 0.3
            }
            return cls(width, height, cells)

        if name not in PATTERNS:
            raise ValueError(
                f"Unknown pattern '{name}'. Choose from: {', '.join(sorted(PATTERNS))} or 'random'"
            )

        offsets = PATTERNS[name]
        # Center the pattern
        max_x = max(x for x, _ in offsets)
        max_y = max(y for _, y in offsets)
        cx = (width - max_x) // 2
        cy = (height - max_y) // 2
        cells = {((cx + x) % width, (cy + y) % height) for x, y in offsets}
        return cls(width, height, cells)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Grid):
            return NotImplemented
        return (
            self.width == other.width
            and self.height == other.height
            and self.cells == other.cells
        )

    def __repr__(self) -> str:
        return f"Grid({self.width}x{self.height}, pop={self.population})"
