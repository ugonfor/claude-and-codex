"""Conway's Game of Life — core engine."""

from __future__ import annotations


class Grid:
    """A Game of Life grid using a sparse set of living cells."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells: set[tuple[int, int]] = set()

    def set(self, x: int, y: int, alive: bool = True) -> None:
        if alive:
            self.cells.add((x, y))
        else:
            self.cells.discard((x, y))

    def get(self, x: int, y: int) -> bool:
        return (x, y) in self.cells

    def _neighbors(self, x: int, y: int) -> int:
        count = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if (nx, ny) in self.cells:
                        count += 1
        return count

    def step(self) -> Grid:
        """Advance one generation and return a new Grid."""
        new = Grid(self.width, self.height)
        # Collect all candidates: living cells + their neighbors
        candidates: set[tuple[int, int]] = set()
        for x, y in self.cells:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        candidates.add((nx, ny))
        # Apply rules
        for x, y in candidates:
            n = self._neighbors(x, y)
            alive = (x, y) in self.cells
            if alive and n in (2, 3):
                new.cells.add((x, y))
            elif not alive and n == 3:
                new.cells.add((x, y))
        return new

    def __str__(self) -> str:
        lines = []
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                row += "#" if self.get(x, y) else "."
            lines.append(row)
        return "\n".join(lines)


# --- Classic patterns ---

def glider(grid: Grid, ox: int = 1, oy: int = 1) -> None:
    """Place a glider at offset (ox, oy)."""
    for x, y in [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)]:
        grid.set(ox + x, oy + y)


def blinker(grid: Grid, ox: int = 5, oy: int = 5) -> None:
    """Place a blinker (period-2 oscillator) at offset."""
    for x, y in [(0, 0), (1, 0), (2, 0)]:
        grid.set(ox + x, oy + y)


def glider_gun(grid: Grid, ox: int = 1, oy: int = 1) -> None:
    """Place a Gosper glider gun at offset (ox, oy). Needs at least 38x11 space."""
    gun_cells = [
        (24, 0),
        (22, 1), (24, 1),
        (12, 2), (13, 2), (20, 2), (21, 2), (34, 2), (35, 2),
        (11, 3), (15, 3), (20, 3), (21, 3), (34, 3), (35, 3),
        (0, 4), (1, 4), (10, 4), (16, 4), (20, 4), (21, 4),
        (0, 5), (1, 5), (10, 5), (14, 5), (16, 5), (17, 5), (22, 5), (24, 5),
        (10, 6), (16, 6), (24, 6),
        (11, 7), (15, 7),
        (12, 8), (13, 8),
    ]
    for x, y in gun_cells:
        grid.set(ox + x, oy + y)


def random_soup(grid: Grid, density: float = 0.3) -> None:
    """Fill the grid randomly."""
    import random
    for y in range(grid.height):
        for x in range(grid.width):
            if random.random() < density:
                grid.set(x, y)
