"""Conway's Game of Life — core engine."""

from __future__ import annotations


class Grid:
    """A Game of Life grid backed by a set of live cell coordinates."""

    def __init__(self, live_cells: set[tuple[int, int]] | None = None):
        self.cells: set[tuple[int, int]] = set(live_cells) if live_cells else set()

    # ── queries ──────────────────────────────────────────────────────

    def is_alive(self, row: int, col: int) -> bool:
        return (row, col) in self.cells

    @property
    def population(self) -> int:
        return len(self.cells)

    @property
    def bounding_box(self) -> tuple[int, int, int, int]:
        """Return (min_row, min_col, max_row, max_col). Empty grid → (0,0,0,0)."""
        if not self.cells:
            return (0, 0, 0, 0)
        rows = [r for r, _ in self.cells]
        cols = [c for _, c in self.cells]
        return (min(rows), min(cols), max(rows), max(cols))

    # ── evolution ────────────────────────────────────────────────────

    def _neighbours(self, row: int, col: int) -> int:
        """Count live neighbours of a cell."""
        count = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                if (row + dr, col + dc) in self.cells:
                    count += 1
        return count

    def step(self) -> "Grid":
        """Advance one generation and return a *new* Grid."""
        candidates: set[tuple[int, int]] = set()
        for r, c in self.cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    candidates.add((r + dr, c + dc))

        new_cells: set[tuple[int, int]] = set()
        for cell in candidates:
            n = self._neighbours(*cell)
            if cell in self.cells:
                if n in (2, 3):
                    new_cells.add(cell)
            else:
                if n == 3:
                    new_cells.add(cell)
        return Grid(new_cells)

    # ── pattern loading ──────────────────────────────────────────────

    @classmethod
    def from_pattern(cls, pattern: list[str]) -> "Grid":
        """Create a grid from a list of strings ('.' = dead, '*' or 'O' = alive)."""
        cells: set[tuple[int, int]] = set()
        for r, line in enumerate(pattern):
            for c, ch in enumerate(line):
                if ch in ("*", "O"):
                    cells.add((r, c))
        return cls(cells)

    # ── display ──────────────────────────────────────────────────────

    def render(self, padding: int = 1) -> str:
        """Render the grid as a string of '.' and '*' characters."""
        if not self.cells:
            return "."
        r0, c0, r1, c1 = self.bounding_box
        r0 -= padding
        c0 -= padding
        r1 += padding
        c1 += padding
        rows: list[str] = []
        for r in range(r0, r1 + 1):
            row = ""
            for c in range(c0, c1 + 1):
                row += "*" if self.is_alive(r, c) else "."
            rows.append(row)
        return "\n".join(rows)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Grid):
            return NotImplemented
        return self.cells == other.cells

    def __repr__(self) -> str:
        return f"Grid(population={self.population})"
