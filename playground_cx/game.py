"""Conway's Game of Life — core engine.

Built by Claude as part of a Claude + Codex collaboration.
"""

import random


class GameOfLife:
    """Core Game of Life simulation."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid: list[list[bool]] = [
            [False] * width for _ in range(height)
        ]
        self.generation = 0

    def set_alive(self, row: int, col: int) -> None:
        """Set a cell to alive."""
        if 0 <= row < self.height and 0 <= col < self.width:
            self.grid[row][col] = True

    def set_dead(self, row: int, col: int) -> None:
        """Set a cell to dead."""
        if 0 <= row < self.height and 0 <= col < self.width:
            self.grid[row][col] = False

    def is_alive(self, row: int, col: int) -> bool:
        """Check if a cell is alive (wraps around edges)."""
        r = row % self.height
        c = col % self.width
        return self.grid[r][c]

    def count_neighbors(self, row: int, col: int) -> int:
        """Count live neighbors (8-connected, toroidal wrap)."""
        count = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                if self.is_alive(row + dr, col + dc):
                    count += 1
        return count

    def step(self) -> None:
        """Advance one generation using standard B3/S23 rules."""
        new_grid = [[False] * self.width for _ in range(self.height)]
        for r in range(self.height):
            for c in range(self.width):
                n = self.count_neighbors(r, c)
                if self.grid[r][c]:
                    # Alive: survives with 2 or 3 neighbors
                    new_grid[r][c] = n in (2, 3)
                else:
                    # Dead: born with exactly 3 neighbors
                    new_grid[r][c] = n == 3
        self.grid = new_grid
        self.generation += 1

    def randomize(self, density: float = 0.3) -> None:
        """Fill grid randomly. density = probability a cell is alive."""
        for r in range(self.height):
            for c in range(self.width):
                self.grid[r][c] = random.random() < density
        self.generation = 0

    def clear(self) -> None:
        """Kill all cells."""
        self.grid = [[False] * self.width for _ in range(self.height)]
        self.generation = 0

    def population(self) -> int:
        """Count total living cells."""
        return sum(cell for row in self.grid for cell in row)

    def add_pattern(self, pattern: list[tuple[int, int]], offset_r: int = 0, offset_c: int = 0) -> None:
        """Place a pattern on the grid at an offset."""
        for r, c in pattern:
            self.set_alive(r + offset_r, c + offset_c)


# --- Common patterns ---

GLIDER = [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]

BLINKER = [(0, 0), (0, 1), (0, 2)]

BLOCK = [(0, 0), (0, 1), (1, 0), (1, 1)]

LWSS = [(0, 1), (0, 4), (1, 0), (2, 0), (2, 4), (3, 0), (3, 1), (3, 2), (3, 3)]
