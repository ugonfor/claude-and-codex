"""Maze generation engine with multiple algorithms."""

import random


class Maze:
    """A maze represented as a 2D grid of walls and passages."""

    def __init__(self, width: int, height: int, seed: int | None = None):
        self._width = width
        self._height = height
        self._rng = random.Random(seed)
        # Grid dimensions: (2h+1) rows x (2w+1) cols
        self._rows = 2 * height + 1
        self._cols = 2 * width + 1
        # Initialize all walls
        self._grid = [[1] * self._cols for _ in range(self._rows)]

    def generate(self, algorithm: str = "backtracker") -> None:
        """Generate maze using specified algorithm."""
        # Reset grid to all walls
        self._grid = [[1] * self._cols for _ in range(self._rows)]

        if algorithm == "backtracker":
            self._generate_backtracker()
        elif algorithm == "prims":
            self._generate_prims()
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        # Open start and end
        sr, sc = self.start
        er, ec = self.end
        self._grid[sr][sc] = 0
        self._grid[er][ec] = 0

    def _generate_backtracker(self) -> None:
        """Recursive backtracker (DFS-based) maze generation."""
        visited = set()
        # Start from cell (0, 0) → grid position (1, 1)
        stack = [(0, 0)]
        visited.add((0, 0))
        self._grid[1][1] = 0  # Open starting cell

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while stack:
            cx, cy = stack[-1]
            neighbors = []
            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self._height and 0 <= ny < self._width and (nx, ny) not in visited:
                    neighbors.append((nx, ny))

            if neighbors:
                nx, ny = self._rng.choice(neighbors)
                # Remove wall between current and neighbor
                wall_r = 1 + cx + (nx - cx)  # = 1 + cx + dx
                wall_c = 1 + cy + (ny - cy)  # = 1 + cy + dy
                # Actually: current cell grid pos = (1+2*cx, 1+2*cy)
                # Neighbor grid pos = (1+2*nx, 1+2*ny)
                # Wall between = average of the two
                gr_cx, gc_cy = 1 + 2 * cx, 1 + 2 * cy
                gr_nx, gc_ny = 1 + 2 * nx, 1 + 2 * ny
                wall_r = (gr_cx + gr_nx) // 2
                wall_c = (gc_cy + gc_ny) // 2

                self._grid[gr_nx][gc_ny] = 0  # Open neighbor cell
                self._grid[wall_r][wall_c] = 0  # Open wall

                visited.add((nx, ny))
                stack.append((nx, ny))
            else:
                stack.pop()

    def _generate_prims(self) -> None:
        """Randomized Prim's algorithm maze generation."""
        visited = set()
        walls = []

        # Start from cell (0, 0)
        start = (0, 0)
        visited.add(start)
        self._grid[1][1] = 0

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Add walls of starting cell
        for dx, dy in directions:
            nx, ny = dx, dy
            if 0 <= nx < self._height and 0 <= ny < self._width:
                walls.append((start, (nx, ny)))

        while walls:
            idx = self._rng.randrange(len(walls))
            (cx, cy), (nx, ny) = walls.pop(idx)

            if (nx, ny) in visited:
                continue

            visited.add((nx, ny))

            # Open neighbor cell and wall between
            gr_cx, gc_cy = 1 + 2 * cx, 1 + 2 * cy
            gr_nx, gc_ny = 1 + 2 * nx, 1 + 2 * ny
            wall_r = (gr_cx + gr_nx) // 2
            wall_c = (gc_cy + gc_ny) // 2

            self._grid[gr_nx][gc_ny] = 0
            self._grid[wall_r][wall_c] = 0

            # Add walls of new cell
            for dx, dy in directions:
                nnx, nny = nx + dx, ny + dy
                if 0 <= nnx < self._height and 0 <= nny < self._width and (nnx, nny) not in visited:
                    walls.append(((nx, ny), (nnx, nny)))

    @property
    def grid(self) -> list[list[int]]:
        """2D grid: 0=passage, 1=wall."""
        return self._grid

    @property
    def start(self) -> tuple[int, int]:
        """(row, col) of start — left entrance."""
        return (1, 0)

    @property
    def end(self) -> tuple[int, int]:
        """(row, col) of end — right exit."""
        return (2 * self._height - 1, 2 * self._width)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height
