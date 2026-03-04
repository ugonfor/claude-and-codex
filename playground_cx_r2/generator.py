"""
ASCII Art Generator — written by Claude
Generates various ASCII art patterns: fractals, spirals, mazes, waves.
Designed to be composed with transformer.py (written by Codex).
"""

import math
import random


def sierpinski(rows: int = 16) -> list[str]:
    """Generate a Sierpinski triangle."""
    lines = []
    for y in range(rows):
        line = ""
        for x in range(2 * rows):
            # Center the triangle
            col = x - (rows - y - 1)
            if col < 0 or col > 2 * y:
                line += " "
            elif col % 2 == 1:
                line += " "
            else:
                # Sierpinski rule: if bit-and of row and col/2 is non-zero, it's a hole
                if y & (col // 2):
                    line += " "
                else:
                    line += "*"
        lines.append(line)
    return lines


def spiral(width: int = 40, height: int = 20, turns: float = 3.0) -> list[str]:
    """Generate an Archimedean spiral using braille-like characters."""
    canvas = [[" "] * width for _ in range(height)]
    chars = ".·:+*#@"
    cx, cy = width / 2, height / 2
    steps = 500
    for i in range(steps):
        t = i / steps
        angle = t * turns * 2 * math.pi
        r = t * min(cx, cy) * 0.9
        x = int(cx + r * math.cos(angle))
        y = int(cy + r * math.sin(angle) * 0.5)  # squash for terminal aspect ratio
        if 0 <= x < width and 0 <= y < height:
            intensity = int(t * (len(chars) - 1))
            canvas[y][x] = chars[intensity]
    return ["".join(row) for row in canvas]


def wave(width: int = 60, height: int = 15, waves: int = 2) -> list[str]:
    """Generate overlapping sine waves."""
    canvas = [[" "] * width for _ in range(height)]
    wave_chars = ["~", "=", "~", "-"]
    for w in range(waves):
        phase = w * math.pi / waves
        amplitude = (height / 2 - 1) * (1 - 0.2 * w)
        for x in range(width):
            angle = (x / width) * 4 * math.pi + phase
            y = int(height / 2 + amplitude * math.sin(angle))
            if 0 <= y < height:
                canvas[y][x] = wave_chars[w % len(wave_chars)]
    return ["".join(row) for row in canvas]


def diamond(size: int = 10) -> list[str]:
    """Generate a diamond pattern with nested layers."""
    lines = []
    chars = "#O*o+."
    for y in range(2 * size - 1):
        row_dist = abs(size - 1 - y)
        line = " " * row_dist
        width = 2 * (size - row_dist) - 1
        for x in range(width):
            col_dist = abs((size - row_dist - 1) - x)
            depth = min(row_dist, col_dist, abs(size - 1 - y), abs((size - row_dist - 1) - x))
            # Use layer depth to pick character
            layer = min(depth, (size - 1 - row_dist))
            line += chars[layer % len(chars)]
        lines.append(line)
    return lines


def maze(width: int = 31, height: int = 15) -> list[str]:
    """Generate a simple random maze using recursive backtracking."""
    # Ensure odd dimensions
    w = width if width % 2 == 1 else width + 1
    h = height if height % 2 == 1 else height + 1
    grid = [["█"] * w for _ in range(h)]

    def carve(cx, cy):
        grid[cy][cx] = " "
        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 < nx < w and 0 < ny < h and grid[ny][nx] == "█":
                grid[cy + dy // 2][cx + dx // 2] = " "
                carve(nx, ny)

    carve(1, 1)
    # Mark entrance and exit
    grid[0][1] = "→"
    grid[h - 1][w - 2] = "→"
    return ["".join(row) for row in grid]


def tree(depth: int = 5) -> list[str]:
    """Generate a fractal binary tree (text-based)."""
    width = 2 ** (depth + 1)
    height = 3 * depth + 1
    canvas = [[" "] * width for _ in range(height)]

    def draw_branch(x, y, length, angle_deg, d):
        if d == 0 or length < 1:
            return
        angle = math.radians(angle_deg)
        for i in range(int(length)):
            px = int(x + i * math.cos(angle))
            py = int(y - i * math.sin(angle))
            if 0 <= px < width and 0 <= py < height:
                if abs(angle_deg - 90) < 10:
                    canvas[py][px] = "|"
                else:
                    canvas[py][px] = "/" if angle_deg > 90 else "\\"
        ex = int(x + length * math.cos(angle))
        ey = int(y - length * math.sin(angle))
        draw_branch(ex, ey, length * 0.65, angle_deg + 30, d - 1)
        draw_branch(ex, ey, length * 0.65, angle_deg - 30, d - 1)

    draw_branch(width // 2, height - 1, height * 0.4, 90, depth)
    return ["".join(row) for row in canvas]


# Registry of all generators
GENERATORS = {
    "sierpinski": sierpinski,
    "spiral": spiral,
    "wave": wave,
    "diamond": diamond,
    "maze": maze,
    "tree": tree,
}


def render(name: str, **kwargs) -> str:
    """Render a named pattern and return as a single string."""
    if name not in GENERATORS:
        raise ValueError(f"Unknown pattern: {name}. Available: {list(GENERATORS.keys())}")
    lines = GENERATORS[name](**kwargs)
    return "\n".join(lines)


def render_all() -> dict[str, str]:
    """Render all patterns with default settings."""
    return {name: render(name) for name in GENERATORS}


if __name__ == "__main__":
    print("=== Claude's ASCII Art Generator ===\n")
    for name in GENERATORS:
        print(f"--- {name.upper()} ---")
        print(render(name))
        print()
