"""ASCII renderer and animation helpers for Conway's Game of Life."""

from __future__ import annotations

import os
import sys
import time
from typing import Iterable


def clear_screen(use_ansi: bool = True) -> None:
    if use_ansi:
        sys.stdout.write("\x1b[H\x1b[2J")
        sys.stdout.flush()
    else:
        os.system("cls" if os.name == "nt" else "clear")


def render_grid(
    grid: Iterable[Iterable[bool]],
    alive: str = "#",
    dead: str = ".",
    border: bool = False,
) -> str:
    rows = [list(row) for row in grid]
    width = len(rows[0]) if rows else 0

    lines: list[str] = []
    if border:
        lines.append("+" + "-" * width + "+")

    for row in rows:
        line = "".join(alive if cell else dead for cell in row)
        if border:
            line = "|" + line + "|"
        lines.append(line)

    if border:
        lines.append("+" + "-" * width + "+")

    return "\n".join(lines)


def frame_text(
    game,
    alive: str = "#",
    dead: str = ".",
    border: bool = False,
    show_stats: bool = True,
) -> str:
    grid = game.get_grid()
    body = render_grid(grid, alive=alive, dead=dead, border=border)
    if not show_stats:
        return body
    header = f"Gen {game.generation} | Pop {game.population}"
    return f"{header}\n{body}"


def animate(
    game,
    steps: int | None = 200,
    delay: float = 0.1,
    alive: str = "#",
    dead: str = ".",
    border: bool = False,
    show_stats: bool = True,
    clear: bool = True,
    use_ansi: bool = True,
) -> None:
    count = 0
    while steps is None or count < steps:
        if clear:
            clear_screen(use_ansi=use_ansi)
        sys.stdout.write(frame_text(game, alive=alive, dead=dead, border=border, show_stats=show_stats))
        sys.stdout.write("\n")
        sys.stdout.flush()
        time.sleep(delay)
        game.step()
        count += 1


def print_frame(
    game,
    alive: str = "#",
    dead: str = ".",
    border: bool = False,
    show_stats: bool = True,
) -> None:
    sys.stdout.write(frame_text(game, alive=alive, dead=dead, border=border, show_stats=show_stats))
    sys.stdout.write("\n")
    sys.stdout.flush()


__all__ = [
    "animate",
    "clear_screen",
    "frame_text",
    "print_frame",
    "render_grid",
]
