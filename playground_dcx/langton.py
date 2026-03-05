"""
Langton's Ant - A cellular automaton that produces emergent patterns.

Classic rules: An ant on a grid of black/white cells:
  - On white: turn right 90°, flip cell to black, move forward
  - On black: turn left 90°, flip cell to white, move forward

Extended rules support multiple colors with custom turn sequences (RL notation).
For example, "RLR" means: color 0 -> turn right, color 1 -> turn left, color 2 -> turn right.

Multiple ants can coexist on the same grid, creating complex interactions.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Tuple


class Direction(IntEnum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

    def turn_right(self) -> "Direction":
        return Direction((self + 1) % 4)

    def turn_left(self) -> "Direction":
        return Direction((self - 1) % 4)

    def delta(self) -> Tuple[int, int]:
        return {
            Direction.UP: (-1, 0),
            Direction.RIGHT: (0, 1),
            Direction.DOWN: (1, 0),
            Direction.LEFT: (0, -1),
        }[self]


@dataclass
class Ant:
    row: int
    col: int
    direction: Direction = Direction.UP
    alive: bool = True

    def turn(self, right: bool):
        if right:
            self.direction = self.direction.turn_right()
        else:
            self.direction = self.direction.turn_left()

    def move(self):
        dr, dc = self.direction.delta()
        self.row += dr
        self.col += dc


@dataclass
class Grid:
    height: int
    width: int
    num_colors: int = 2
    cells: list = field(default_factory=list)

    def __post_init__(self):
        if not self.cells:
            self.cells = [[0] * self.width for _ in range(self.height)]

    def get(self, row: int, col: int) -> int:
        if 0 <= row < self.height and 0 <= col < self.width:
            return self.cells[row][col]
        return -1  # out of bounds

    def set(self, row: int, col: int, value: int):
        if 0 <= row < self.height and 0 <= col < self.width:
            self.cells[row][col] = value

    def next_color(self, row: int, col: int) -> int:
        current = self.get(row, col)
        if current < 0:
            return current
        return (current + 1) % self.num_colors


class LangtonSimulation:
    """Runs a Langton's Ant simulation with configurable rules and multiple ants."""

    def __init__(self, height: int = 64, width: int = 64, rule: str = "RL"):
        self.rule = rule.upper()
        num_colors = len(self.rule)
        self.grid = Grid(height, width, num_colors)
        self.ants: List[Ant] = []
        self.step_count = 0

    def add_ant(self, row: int, col: int, direction: Direction = Direction.UP) -> Ant:
        ant = Ant(row, col, direction)
        self.ants.append(ant)
        return ant

    def step(self):
        """Advance the simulation by one step."""
        for ant in self.ants:
            if not ant.alive:
                continue

            color = self.grid.get(ant.row, ant.col)
            if color < 0:
                ant.alive = False
                continue

            # Apply rule: R = turn right, L = turn left
            turn_right = self.rule[color] == "R"
            ant.turn(turn_right)

            # Cycle color
            self.grid.set(ant.row, ant.col, self.grid.next_color(ant.row, ant.col))

            # Move forward
            ant.move()

            # Check bounds
            if self.grid.get(ant.row, ant.col) < 0:
                ant.alive = False

        self.step_count += 1

    def run(self, steps: int):
        """Run the simulation for a given number of steps."""
        for _ in range(steps):
            if not any(a.alive for a in self.ants):
                break
            self.step()

    def render_ascii(self) -> str:
        """Render the grid as ASCII art."""
        chars = " .oO#@%&*+"
        lines = []
        for row in range(self.grid.height):
            line = ""
            for col in range(self.grid.width):
                # Check if any ant is here
                ant_here = any(
                    a.alive and a.row == row and a.col == col for a in self.ants
                )
                if ant_here:
                    line += "A"
                else:
                    color = self.grid.cells[row][col]
                    line += chars[color % len(chars)]
            lines.append(line)
        return "\n".join(lines)

    def stats(self) -> dict:
        """Return simulation statistics."""
        total_cells = self.grid.height * self.grid.width
        colored = sum(
            1
            for r in range(self.grid.height)
            for c in range(self.grid.width)
            if self.grid.cells[r][c] != 0
        )
        return {
            "steps": self.step_count,
            "ants_alive": sum(1 for a in self.ants if a.alive),
            "ants_total": len(self.ants),
            "cells_colored": colored,
            "coverage_pct": round(100.0 * colored / total_cells, 2),
            "rule": self.rule,
            "grid_size": f"{self.grid.height}x{self.grid.width}",
        }
