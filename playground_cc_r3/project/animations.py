"""
Animation system for the collaborative ASCII art show.
Built by Claude-B.

Provides frame-based animation primitives that the show runner uses.
"""

import time
import os
import sys


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_terminal_size():
    """Get terminal dimensions."""
    try:
        cols, rows = os.get_terminal_size()
    except OSError:
        cols, rows = 80, 24
    return cols, rows


class Frame:
    """A single frame of ASCII art."""

    def __init__(self, lines, width=None, height=None):
        self.lines = lines if isinstance(lines, list) else lines.split('\n')
        self.width = width or max((len(l) for l in self.lines), default=0)
        self.height = height or len(self.lines)

    def render(self):
        return '\n'.join(self.lines)

    def center(self, screen_width, screen_height):
        """Center this frame on screen."""
        pad_x = max(0, (screen_width - self.width) // 2)
        pad_y = max(0, (screen_height - self.height) // 2)
        centered = [' ' * pad_x + line for line in self.lines]
        result = ['' for _ in range(pad_y)] + centered
        return '\n'.join(result)


class Animation:
    """A sequence of frames played at a given FPS."""

    def __init__(self, frames, fps=10, loop=False):
        self.frames = frames  # list of Frame objects
        self.fps = fps
        self.loop = loop

    def play(self, duration=None):
        """Play the animation for a given duration (seconds) or once through."""
        cols, rows = get_terminal_size()
        delay = 1.0 / self.fps
        start = time.time()

        idx = 0
        while True:
            if duration and (time.time() - start) >= duration:
                break
            if idx >= len(self.frames):
                if self.loop:
                    idx = 0
                else:
                    break

            clear_screen()
            print(self.frames[idx].center(cols, rows))
            sys.stdout.flush()
            time.sleep(delay)
            idx += 1


def make_firework_frames(width=40, height=20, num_frames=15):
    """Generate frames for a firework explosion animation."""
    frames = []
    cx, cy = width // 2, height // 2

    # Phase 1: rocket going up (5 frames)
    for i in range(5):
        grid = [[' '] * width for _ in range(height)]
        rocket_y = height - 1 - i * 3
        if 0 <= rocket_y < height:
            grid[rocket_y][cx] = '|'
            if rocket_y + 1 < height:
                grid[rocket_y + 1][cx] = '*'
        frames.append(Frame([''.join(row) for row in grid], width, height))

    # Phase 2: explosion expanding (10 frames)
    import math
    num_particles = 16
    for t in range(10):
        grid = [[' '] * width for _ in range(height)]
        radius = (t + 1) * 1.5
        chars = ['*', '.', '+', 'o', '*', '.', '+', 'o',
                 '*', '.', '+', 'o', '*', '.', '+', 'o']
        for p in range(num_particles):
            angle = (2 * math.pi * p) / num_particles
            px = int(cx + radius * math.cos(angle))
            py = int(cy + radius * math.sin(angle) * 0.5)  # squish vertically
            if 0 <= px < width and 0 <= py < height:
                grid[py][px] = chars[p % len(chars)]
        frames.append(Frame([''.join(row) for row in grid], width, height))

    return frames


def make_bouncing_ball_frames(width=60, height=20, num_frames=40):
    """Generate frames for a bouncing ball."""
    frames = []
    x, y = 5.0, 2.0
    vx, vy = 1.5, 0.0
    gravity = 0.3
    bounce = -0.8

    ball = 'O'

    for _ in range(num_frames):
        grid = [[' '] * width for _ in range(height)]

        # Draw borders
        for c in range(width):
            grid[0][c] = '-'
            grid[height - 1][c] = '-'
        for r in range(height):
            grid[r][0] = '|'
            grid[r][width - 1] = '|'

        # Draw ball
        bx, by = int(x), int(y)
        if 1 <= bx < width - 1 and 1 <= by < height - 1:
            grid[by][bx] = ball

        frames.append(Frame([''.join(row) for row in grid], width, height))

        # Physics
        vy += gravity
        x += vx
        y += vy

        if y >= height - 2:
            y = height - 2
            vy *= bounce
        if y < 1:
            y = 1
            vy *= bounce
        if x >= width - 2:
            x = width - 2
            vx = -vx
        if x < 1:
            x = 1
            vx = -vx

    return frames


def make_matrix_rain_frames(width=60, height=20, num_frames=30):
    """Generate Matrix-style digital rain frames."""
    import random
    frames = []

    # Initialize drops at random positions
    drops = [random.randint(-height, 0) for _ in range(width)]
    chars = "01アイウエオカキクケコサシスセソタチツテト"

    for _ in range(num_frames):
        grid = [[' '] * width for _ in range(height)]

        for col in range(width):
            head = drops[col]
            trail_len = random.randint(5, 12)

            for t in range(trail_len):
                row = head - t
                if 0 <= row < height:
                    if t == 0:
                        grid[row][col] = random.choice(chars)
                    elif t < 3:
                        grid[row][col] = random.choice(chars)
                    else:
                        grid[row][col] = '.'

            drops[col] += 1
            if drops[col] - trail_len > height:
                drops[col] = random.randint(-5, 0)

        frames.append(Frame([''.join(row) for row in grid], width, height))

    return frames


def make_transition_wipe(width=60, height=20, num_frames=10):
    """Generate a horizontal wipe transition."""
    frames = []
    for t in range(num_frames):
        progress = (t + 1) / num_frames
        col_boundary = int(progress * width)
        grid = []
        for r in range(height):
            row = ['#' if c < col_boundary else ' ' for c in range(width)]
            grid.append(''.join(row))
        frames.append(Frame(grid, width, height))
    return frames
