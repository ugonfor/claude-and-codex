"""ASCII renderer for Conway's Game of Life."""

from __future__ import annotations

from life import Grid


def render(grid: Grid, alive: str = "#", dead: str = ".") -> str:
    lines = []
    for y in range(grid.height):
        row = []
        for x in range(grid.width):
            row.append(alive if grid.get(x, y) else dead)
        lines.append("".join(row))
    return "\n".join(lines)


def display(
    grid: Grid,
    alive: str = "#",
    dead: str = ".",
    clear: bool = True,
) -> None:
    if clear:
        print("\x1b[H\x1b[2J", end="")
    print(render(grid, alive=alive, dead=dead))
