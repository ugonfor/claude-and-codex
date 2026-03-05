"""Langton's Ant -- core engine."""

from __future__ import annotations

from enum import Enum


class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


# Movement deltas: (dx, dy) for each direction
_DELTAS = {
    Direction.UP: (0, -1),
    Direction.RIGHT: (1, 0),
    Direction.DOWN: (0, 1),
    Direction.LEFT: (-1, 0),
}


class Ant:
    """The ant that walks the grid."""

    def __init__(self, x: int, y: int, direction: Direction = Direction.UP) -> None:
        self.x = x
        self.y = y
        self.direction = direction

    def turn_right(self) -> None:
        self.direction = Direction((self.direction.value + 1) % 4)

    def turn_left(self) -> None:
        self.direction = Direction((self.direction.value - 1) % 4)

    def move_forward(self, width: int, height: int) -> None:
        dx, dy = _DELTAS[self.direction]
        self.x = (self.x + dx) % width
        self.y = (self.y + dy) % height


class LangtonGrid:
    """Grid for Langton's Ant simulation."""

    def __init__(self, width: int = 80, height: int = 40) -> None:
        self.width = width
        self.height = height
        self.black_cells: set[tuple[int, int]] = set()
        self.ant = Ant(width // 2, height // 2)
        self.step_count = 0

    def is_black(self, x: int, y: int) -> bool:
        return (x, y) in self.black_cells

    def step(self) -> None:
        """Advance one step: turn, flip, move."""
        pos = (self.ant.x, self.ant.y)
        if pos in self.black_cells:
            # On black: turn left, flip to white
            self.ant.turn_left()
            self.black_cells.discard(pos)
        else:
            # On white: turn right, flip to black
            self.ant.turn_right()
            self.black_cells.add(pos)
        self.ant.move_forward(self.width, self.height)
        self.step_count += 1

    def run(self, steps: int) -> None:
        """Run multiple steps."""
        for _ in range(steps):
            self.step()

    @property
    def population(self) -> int:
        """Number of black cells."""
        return len(self.black_cells)
