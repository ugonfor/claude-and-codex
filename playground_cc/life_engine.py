"""Conway's Game of Life - Core Simulation Engine (by Claude-A)"""

from __future__ import annotations
from typing import Set, Tuple, Dict

# A cell is represented as (row, col) tuple
Cell = Tuple[int, int]


# ---- Classic patterns ----
PATTERNS: Dict[str, Set[Cell]] = {
    "glider": {(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)},
    "blinker": {(1, 0), (1, 1), (1, 2)},
    "toad": {(1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)},
    "beacon": {(0, 0), (0, 1), (1, 0), (1, 1), (2, 2), (2, 3), (3, 2), (3, 3)},
    "pulsar": set(),  # filled below
    "glider_gun": set(),  # filled below
    "r_pentomino": {(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)},
    "diehard": {(0, 6), (1, 0), (1, 1), (2, 1), (2, 5), (2, 6), (2, 7)},
    "acorn": {(0, 1), (1, 3), (2, 0), (2, 1), (2, 4), (2, 5), (2, 6)},
    "block": {(0, 0), (0, 1), (1, 0), (1, 1)},
    "boat": {(0, 0), (0, 1), (1, 0), (1, 2), (2, 1)},
    "lwss": {(0, 1), (0, 4), (1, 0), (2, 0), (2, 4), (3, 0), (3, 1), (3, 2), (3, 3)},
}

# Build pulsar pattern
_pulsar_cells = set()
for r, c in [(0, 2), (0, 3), (0, 4), (0, 8), (0, 9), (0, 10),
             (2, 0), (2, 5), (2, 7), (2, 12),
             (3, 0), (3, 5), (3, 7), (3, 12),
             (4, 0), (4, 5), (4, 7), (4, 12),
             (5, 2), (5, 3), (5, 4), (5, 8), (5, 9), (5, 10)]:
    # Pulsar has 4-fold symmetry
    _pulsar_cells.add((r, c))
    _pulsar_cells.add((12 - r, c))
    _pulsar_cells.add((r, 12 - c))
    _pulsar_cells.add((12 - r, 12 - c))
PATTERNS["pulsar"] = _pulsar_cells

# Build Gosper Glider Gun
_gun = set()
for r, c in [
    (4, 0), (4, 1), (5, 0), (5, 1),  # left block
    (2, 12), (2, 13), (3, 11), (3, 15), (4, 10), (4, 16),
    (5, 10), (5, 14), (5, 16), (5, 17), (6, 10), (6, 16),
    (7, 11), (7, 15), (8, 12), (8, 13),  # left part
    (0, 24), (1, 22), (1, 24), (2, 20), (2, 21),
    (3, 20), (3, 21), (4, 20), (4, 21),
    (5, 22), (5, 24), (6, 24),  # right part
    (2, 34), (2, 35), (3, 34), (3, 35),  # right block
]:
    _gun.add((r, c))
PATTERNS["glider_gun"] = _gun


class GameOfLife:
    """Core Game of Life simulation.

    Uses a set of alive cells (sparse representation) for efficiency.
    Supports both bounded and toroidal (wrapping) grids.
    """

    def __init__(
        self,
        width: int = 60,
        height: int = 40,
        wrap: bool = True,
        alive: Set[Cell] | None = None,
    ):
        self.width = width
        self.height = height
        self.wrap = wrap
        self.alive: Set[Cell] = set(alive) if alive else set()
        self.generation = 0
        self._history: list[Set[Cell]] = []

    # ---- Grid operations ----

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.height and 0 <= c < self.width

    def normalize(self, r: int, c: int) -> Cell:
        if self.wrap:
            return (r % self.height, c % self.width)
        return (r, c)

    def set_alive(self, r: int, c: int) -> None:
        cell = self.normalize(r, c)
        if self.in_bounds(*cell) or self.wrap:
            self.alive.add(cell)

    def set_dead(self, r: int, c: int) -> None:
        cell = self.normalize(r, c)
        self.alive.discard(cell)

    def toggle(self, r: int, c: int) -> None:
        cell = self.normalize(r, c)
        if cell in self.alive:
            self.alive.discard(cell)
        else:
            self.alive.add(cell)

    def is_alive(self, r: int, c: int) -> bool:
        return self.normalize(r, c) in self.alive

    # ---- Compatibility API (x,y coordinates for Claude-B's renderer) ----

    def set_cell(self, x: int, y: int, alive: bool = True) -> None:
        """Set cell state using (x=col, y=row) coordinates."""
        if alive:
            self.set_alive(y, x)
        else:
            self.set_dead(y, x)

    def get_cell(self, x: int, y: int) -> bool:
        """Get cell state using (x=col, y=row) coordinates."""
        return self.is_alive(y, x)

    def clear(self) -> None:
        self.alive.clear()
        self.generation = 0
        self._history.clear()

    # ---- Simulation ----

    def _neighbors(self, r: int, c: int) -> list[Cell]:
        """Return the (up to) 8 neighbor coordinates."""
        result = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if self.wrap:
                    result.append((nr % self.height, nc % self.width))
                elif self.in_bounds(nr, nc):
                    result.append((nr, nc))
        return result

    def step(self) -> int:
        """Advance one generation. Returns number of cells that changed."""
        # Save history for cycle detection
        self._history.append(frozenset(self.alive))
        if len(self._history) > 10:
            self._history.pop(0)

        neighbor_count: Dict[Cell, int] = {}
        for cell in self.alive:
            for nb in self._neighbors(*cell):
                neighbor_count[nb] = neighbor_count.get(nb, 0) + 1

        new_alive: Set[Cell] = set()
        # Check all cells that could potentially be alive
        candidates = self.alive | set(neighbor_count.keys())
        for cell in candidates:
            count = neighbor_count.get(cell, 0)
            if cell in self.alive:
                # Survival: 2 or 3 neighbors
                if count in (2, 3):
                    new_alive.add(cell)
            else:
                # Birth: exactly 3 neighbors
                if count == 3:
                    new_alive.add(cell)

        changed = len(self.alive.symmetric_difference(new_alive))
        self.alive = new_alive
        self.generation += 1
        return changed

    def is_stable(self) -> bool:
        """Check if the simulation has reached a stable state or cycle."""
        current = frozenset(self.alive)
        return current in [frozenset(h) for h in self._history]

    # ---- Pattern loading ----

    def load_pattern(self, name: str, offset_r: int = 0, offset_c: int = 0) -> bool:
        """Load a named pattern at the given offset. Returns True if pattern exists."""
        pattern = PATTERNS.get(name.lower())
        if pattern is None:
            return False
        for r, c in pattern:
            self.set_alive(r + offset_r, c + offset_c)
        return True

    def load_cells(self, cells: Set[Cell], offset_r: int = 0, offset_c: int = 0) -> None:
        """Load arbitrary cells at an offset."""
        for r, c in cells:
            self.set_alive(r + offset_r, c + offset_c)

    def randomize(self, density: float = 0.3) -> None:
        """Fill grid with random alive cells at given density."""
        import random
        self.clear()
        for r in range(self.height):
            for c in range(self.width):
                if random.random() < density:
                    self.alive.add((r, c))

    # ---- Export ----

    def to_grid(self) -> list[list[bool]]:
        """Return a 2D boolean grid representation."""
        grid = [[False] * self.width for _ in range(self.height)]
        for r, c in self.alive:
            if self.in_bounds(r, c):
                grid[r][c] = True
        return grid

    def population(self) -> int:
        return len(self.alive)

    def __repr__(self) -> str:
        return f"GameOfLife(gen={self.generation}, pop={self.population()}, {self.width}x{self.height})"


def list_patterns() -> list[str]:
    """Return sorted list of available pattern names."""
    return sorted(PATTERNS.keys())
