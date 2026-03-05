"""Langton's Ant -- cellular automaton simulation."""

from __future__ import annotations

# Directions: 0=up, 1=right, 2=down, 3=left
DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # (dx, dy)


class LangtonAnt:
    """Simulates Langton's Ant on an infinite grid."""

    def __init__(self, x: int = 0, y: int = 0, direction: int = 0):
        self.x = x
        self.y = y
        self.direction = direction  # 0=up, 1=right, 2=down, 3=left
        self.black_cells: set[tuple[int, int]] = set()
        self.step_count = 0

    def step(self) -> None:
        """Execute one step of the simulation."""
        pos = (self.x, self.y)
        if pos in self.black_cells:
            # On black: turn left, flip to white
            self.direction = (self.direction - 1) % 4
            self.black_cells.discard(pos)
        else:
            # On white: turn right, flip to black
            self.direction = (self.direction + 1) % 4
            self.black_cells.add(pos)
        # Move forward
        dx, dy = DIRECTIONS[self.direction]
        self.x += dx
        self.y += dy
        self.step_count += 1

    def run(self, steps: int) -> None:
        """Run the simulation for a given number of steps."""
        for _ in range(steps):
            self.step()

    def bounds(self) -> tuple[int, int, int, int]:
        """Return (min_x, min_y, max_x, max_y) bounding box of all black cells + ant."""
        if not self.black_cells:
            return (self.x, self.y, self.x, self.y)
        xs = [c[0] for c in self.black_cells] + [self.x]
        ys = [c[1] for c in self.black_cells] + [self.y]
        return (min(xs), min(ys), max(xs), max(ys))

    def render(self, padding: int = 2) -> str:
        """Render the grid as a string. '#' = black, '.' = white, 'A' = ant."""
        min_x, min_y, max_x, max_y = self.bounds()
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding

        rows = []
        for y in range(min_y, max_y + 1):
            row = []
            for x in range(min_x, max_x + 1):
                if (x, y) == (self.x, self.y):
                    row.append("A")
                elif (x, y) in self.black_cells:
                    row.append("#")
                else:
                    row.append(".")
            rows.append("".join(row))
        return "\n".join(rows)


def main() -> None:
    """Run and display the ant simulation."""
    import sys

    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    ant = LangtonAnt()
    ant.run(steps)
    print(f"Langton's Ant after {steps} steps:")
    print(f"Position: ({ant.x}, {ant.y}), Black cells: {len(ant.black_cells)}")
    print()
    print(ant.render())


if __name__ == "__main__":
    main()
