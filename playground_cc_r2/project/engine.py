"""ASCII Art Engine — Canvas with Drawing Primitives (by Claude-A)

Provides a 2D character canvas with methods to draw shapes,
lines, text, and render the result as a string.
"""

from __future__ import annotations

import math


class Canvas:
    """A 2D character grid for ASCII art rendering."""

    def __init__(self, width: int, height: int, bg_char: str = " "):
        self.width = width
        self.height = height
        self.bg_char = bg_char
        self.grid: list[list[str]] = []
        self.clear()

    def clear(self):
        """Reset the canvas to background characters."""
        self.grid = [[self.bg_char] * self.width for _ in range(self.height)]

    def in_bounds(self, x: int, y: int) -> bool:
        """Check if (x, y) is within the canvas."""
        return 0 <= x < self.width and 0 <= y < self.height

    def set_pixel(self, x: int, y: int, char: str):
        """Set a single character at (x, y)."""
        if self.in_bounds(x, y):
            self.grid[y][x] = char[0] if char else self.bg_char

    def get_pixel(self, x: int, y: int) -> str:
        """Get the character at (x, y)."""
        if self.in_bounds(x, y):
            return self.grid[y][x]
        return self.bg_char

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, char: str = "*"):
        """Draw a line from (x1,y1) to (x2,y2) using Bresenham's algorithm."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            self.set_pixel(x1, y1, char)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def draw_rect(self, x: int, y: int, w: int, h: int, char: str = "#", fill: bool = False):
        """Draw a rectangle. If fill=True, fill the interior."""
        for i in range(w):
            for j in range(h):
                if fill or i == 0 or i == w - 1 or j == 0 or j == h - 1:
                    self.set_pixel(x + i, y + j, char)

    def draw_circle(self, cx: int, cy: int, r: int, char: str = "o"):
        """Draw a circle using the midpoint algorithm (aspect-ratio corrected)."""
        # Terminal chars are ~2x taller than wide, so we stretch x
        for angle in range(360):
            rad = math.radians(angle)
            px = int(cx + r * 2 * math.cos(rad))
            py = int(cy + r * math.sin(rad))
            self.set_pixel(px, py, char)

    def draw_filled_circle(self, cx: int, cy: int, r: int, char: str = "o"):
        """Draw a filled circle (aspect-ratio corrected)."""
        for dy in range(-r, r + 1):
            for dx in range(-r * 2, r * 2 + 1):
                if (dx / 2) ** 2 + dy ** 2 <= r ** 2:
                    self.set_pixel(cx + dx, cy + dy, char)

    def draw_text(self, x: int, y: int, text: str):
        """Draw a string of text horizontally starting at (x, y)."""
        for i, ch in enumerate(text):
            self.set_pixel(x + i, y, ch)

    def draw_ellipse(self, cx: int, cy: int, rx: int, ry: int, char: str = "o"):
        """Draw an ellipse."""
        for angle in range(360):
            rad = math.radians(angle)
            px = int(cx + rx * math.cos(rad))
            py = int(cy + ry * math.sin(rad))
            self.set_pixel(px, py, char)

    def overlay(self, other: "Canvas", offset_x: int = 0, offset_y: int = 0):
        """Overlay another canvas on top of this one (non-bg chars only)."""
        for y in range(other.height):
            for x in range(other.width):
                ch = other.get_pixel(x, y)
                if ch != other.bg_char:
                    self.set_pixel(x + offset_x, y + offset_y, ch)

    def render(self) -> str:
        """Render the canvas to a string with newlines."""
        return "\n".join("".join(row) for row in self.grid)

    def __str__(self) -> str:
        return self.render()
