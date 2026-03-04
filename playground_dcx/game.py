"""Conway's Game of Life - Core Engine"""


class GameOfLife:
    """Conway's Game of Life simulation engine.

    Rules:
    1. Any live cell with 2 or 3 neighbors survives.
    2. Any dead cell with exactly 3 neighbors becomes alive.
    3. All other live cells die. All other dead cells stay dead.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._grid = [[False] * width for _ in range(height)]
        self._generation = 0

    @property
    def generation(self) -> int:
        return self._generation

    def set_alive(self, x: int, y: int):
        """Set a cell to alive. Coordinates wrap around (toroidal grid)."""
        self._grid[y % self.height][x % self.width] = True

    def set_dead(self, x: int, y: int):
        """Set a cell to dead."""
        self._grid[y % self.height][x % self.width] = False

    def is_alive(self, x: int, y: int) -> bool:
        """Check if a cell is alive. Wraps around edges."""
        return self._grid[y % self.height][x % self.width]

    def _count_neighbors(self, x: int, y: int) -> int:
        """Count alive neighbors (8-connected, toroidal wrapping)."""
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                if self._grid[ny][nx]:
                    count += 1
        return count

    def step(self):
        """Advance the simulation by one generation."""
        new_grid = [[False] * self.width for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                neighbors = self._count_neighbors(x, y)
                if self._grid[y][x]:
                    # Live cell survives with 2 or 3 neighbors
                    new_grid[y][x] = neighbors in (2, 3)
                else:
                    # Dead cell becomes alive with exactly 3 neighbors
                    new_grid[y][x] = neighbors == 3
        self._grid = new_grid
        self._generation += 1

    def get_grid(self) -> list[list[bool]]:
        """Return the current grid state as a 2D list of booleans."""
        return [row[:] for row in self._grid]

    def load_pattern(self, pattern: list[tuple[int, int]], offset_x: int = 0, offset_y: int = 0):
        """Load a pattern (list of alive cell coordinates) onto the grid."""
        for x, y in pattern:
            self.set_alive(x + offset_x, y + offset_y)

    def clear(self):
        """Clear the entire grid."""
        self._grid = [[False] * self.width for _ in range(self.height)]
        self._generation = 0

    def count_alive(self) -> int:
        """Count total number of alive cells."""
        return sum(sum(1 for cell in row if cell) for row in self._grid)
