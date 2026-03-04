"""Conway's Game of Life — Core Engine (by Claude-Worker)"""

from __future__ import annotations

PATTERNS: dict[str, list[tuple[int, int]]] = {
    "glider": [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
    "blinker": [(1, 0), (1, 1), (1, 2)],
    "toad": [(1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)],
    "beacon": [(0, 0), (0, 1), (1, 0), (1, 1), (2, 2), (2, 3), (3, 2), (3, 3)],
    "pulsar": [
        # Quarter 1 (top-left, mirrored to all 4 quadrants)
        (1, 2), (1, 3), (1, 4), (1, 8), (1, 9), (1, 10),
        (2, 0), (2, 5), (2, 7), (2, 12),
        (3, 0), (3, 5), (3, 7), (3, 12),
        (4, 0), (4, 5), (4, 7), (4, 12),
        (5, 2), (5, 3), (5, 4), (5, 8), (5, 9), (5, 10),
        (7, 2), (7, 3), (7, 4), (7, 8), (7, 9), (7, 10),
        (8, 0), (8, 5), (8, 7), (8, 12),
        (9, 0), (9, 5), (9, 7), (9, 12),
        (10, 0), (10, 5), (10, 7), (10, 12),
        (11, 2), (11, 3), (11, 4), (11, 8), (11, 9), (11, 10),
    ],
    "gosper_gun": [
        (0, 24),
        (1, 22), (1, 24),
        (2, 12), (2, 13), (2, 20), (2, 21), (2, 34), (2, 35),
        (3, 11), (3, 15), (3, 20), (3, 21), (3, 34), (3, 35),
        (4, 0), (4, 1), (4, 10), (4, 16), (4, 20), (4, 21),
        (5, 0), (5, 1), (5, 10), (5, 14), (5, 16), (5, 17), (5, 22), (5, 24),
        (6, 10), (6, 16), (6, 24),
        (7, 11), (7, 15),
        (8, 12), (8, 13),
    ],
    "r_pentomino": [(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)],
    "diehard": [(0, 6), (1, 0), (1, 1), (2, 1), (2, 5), (2, 6), (2, 7)],
    "acorn": [(0, 1), (1, 3), (2, 0), (2, 1), (2, 4), (2, 5), (2, 6)],
    "lightweight_spaceship": [
        (0, 1), (0, 4), (1, 0), (2, 0), (2, 4), (3, 0), (3, 1), (3, 2), (3, 3),
    ],
}


class GameOfLife:
    """Conway's Game of Life simulation."""

    def __init__(
        self,
        width: int = 40,
        height: int = 20,
        cells: set[tuple[int, int]] | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self._generation = 0
        self._alive: set[tuple[int, int]] = set(cells) if cells else set()

    # ---- public API ----

    def step(self) -> None:
        """Advance one generation using standard B3/S23 rules."""
        neighbor_count: dict[tuple[int, int], int] = {}
        for r, c in self._alive:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.height and 0 <= nc < self.width:
                        neighbor_count[(nr, nc)] = neighbor_count.get((nr, nc), 0) + 1

        new_alive: set[tuple[int, int]] = set()
        for cell, count in neighbor_count.items():
            if count == 3 or (count == 2 and cell in self._alive):
                new_alive.add(cell)
        self._alive = new_alive
        self._generation += 1

    def get_grid(self) -> list[list[bool]]:
        """Return 2D boolean grid (row-major). True = alive."""
        grid = [[False] * self.width for _ in range(self.height)]
        for r, c in self._alive:
            grid[r][c] = True
        return grid

    def get_live_cells(self) -> set[tuple[int, int]]:
        """Return the set of currently alive (row, col) positions."""
        return set(self._alive)

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def population(self) -> int:
        return len(self._alive)

    def set_cell(self, row: int, col: int, alive: bool = True) -> None:
        if alive:
            self._alive.add((row, col))
        else:
            self._alive.discard((row, col))

    def clear(self) -> None:
        self._alive.clear()
        self._generation = 0

    @classmethod
    def from_pattern(
        cls,
        name: str,
        width: int = 40,
        height: int = 20,
        offset_row: int | None = None,
        offset_col: int | None = None,
    ) -> GameOfLife:
        """Create a game from a named pattern, centered by default."""
        name_lower = name.lower().replace(" ", "_").replace("-", "_")
        if name_lower not in PATTERNS:
            available = ", ".join(sorted(PATTERNS.keys()))
            raise ValueError(f"Unknown pattern '{name}'. Available: {available}")

        raw = PATTERNS[name_lower]
        # compute bounding box for centering
        min_r = min(r for r, _ in raw)
        max_r = max(r for r, _ in raw)
        min_c = min(c for _, c in raw)
        max_c = max(c for _, c in raw)
        pat_h = max_r - min_r + 1
        pat_w = max_c - min_c + 1

        if offset_row is None:
            offset_row = (height - pat_h) // 2 - min_r
        if offset_col is None:
            offset_col = (width - pat_w) // 2 - min_c

        cells = set()
        for r, c in raw:
            nr, nc = r + offset_row, c + offset_col
            if 0 <= nr < height and 0 <= nc < width:
                cells.add((nr, nc))

        return cls(width=width, height=height, cells=cells)

    @staticmethod
    def available_patterns() -> list[str]:
        return sorted(PATTERNS.keys())

    def __repr__(self) -> str:
        return (
            f"GameOfLife(width={self.width}, height={self.height}, "
            f"gen={self._generation}, pop={self.population})"
        )


# ---- Quick self-test ----
if __name__ == "__main__":
    # Blinker should oscillate with period 2
    game = GameOfLife.from_pattern("blinker", width=5, height=5)
    gen0 = game.get_live_cells()
    game.step()
    gen1 = game.get_live_cells()
    game.step()
    gen2 = game.get_live_cells()
    assert gen0 == gen2, "Blinker should return to original state after 2 steps"
    assert gen0 != gen1, "Blinker should change after 1 step"
    print("Engine self-test PASSED")
    print(f"Available patterns: {GameOfLife.available_patterns()}")
