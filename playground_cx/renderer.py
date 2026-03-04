"""Terminal renderer for Conway's Game of Life.

Built by Codex as part of a Claude + Codex collaboration.
"""

from __future__ import annotations

from game import GameOfLife


class Renderer:
    """Render a GameOfLife instance to a terminal-friendly string."""

    def __init__(self, game: GameOfLife, alive_char: str = "O", dead_char: str = ".", border: bool = False):
        self.game = game
        self.alive_char = alive_char
        self.dead_char = dead_char
        self.border = border

    def render_frame(self) -> str:
        """Return a string representing the current frame."""
        header = f"Generation: {self.game.generation}  Population: {self.game.population()}"
        lines: list[str] = [header]

        if self.border:
            lines.append("+" + ("-" * self.game.width) + "+")

        for row in self.game.grid:
            line = "".join(self.alive_char if cell else self.dead_char for cell in row)
            if self.border:
                line = "|" + line + "|"
            lines.append(line)

        if self.border:
            lines.append("+" + ("-" * self.game.width) + "+")

        return "\n".join(lines)

    def clear_screen(self) -> None:
        """Clear the terminal screen and move cursor to home."""
        print("\x1b[2J\x1b[H", end="")
