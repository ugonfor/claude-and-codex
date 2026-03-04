"""
scene.py — Creative animated scenes for the ASCII art demo.
Written by Claude-B.

Uses the Canvas engine from engine.py (written by Claude-A).
"""

import math
import random
import time


def scene_starfield(canvas, frame):
    """A deep-space starfield with twinkling stars."""
    canvas.clear()
    random.seed(42)  # deterministic star positions
    star_chars = ['.', '+', '*', 'o', '.', '.', '.']

    for _ in range(60):
        x = random.randint(0, canvas.width - 1)
        y = random.randint(0, canvas.height - 1)
        # Twinkle: some stars blink on/off based on frame
        if (x + y + frame) % 5 != 0:
            char = star_chars[random.randint(0, len(star_chars) - 1)]
            canvas.set_pixel(x, y, char)

    # Draw a large moon
    moon_x = canvas.width - 12
    moon_y = 4
    canvas.draw_circle(moon_x, moon_y, 3, char='@')

    # Shooting star that moves across frames
    sx = (frame * 3) % (canvas.width + 20) - 10
    sy = 2 + (frame % 5)
    for i in range(4):
        px, py = sx - i, sy + i // 2
        if 0 <= px < canvas.width and 0 <= py < canvas.height:
            trail_char = '-' if i == 0 else '~' if i == 1 else '.'
            canvas.set_pixel(px, py, trail_char)

    # Title
    canvas.draw_text(2, canvas.height - 2, "[ Starfield - Claude-A + Claude-B ]")


def scene_bouncing_ball(canvas, frame):
    """A ball bouncing around the canvas with trailing path."""
    canvas.clear()

    # Draw border
    canvas.draw_rect(0, 0, canvas.width, canvas.height, char='.')

    # Ball physics (simple bounce)
    period_x = (canvas.width - 4) * 2
    period_y = (canvas.height - 4) * 2

    # Triangle wave for bouncing
    raw_x = frame * 2 % period_x
    raw_y = frame * 1 % period_y

    bx = raw_x if raw_x < period_x // 2 else period_x - raw_x
    by = raw_y if raw_y < period_y // 2 else period_y - raw_y

    bx = bx + 2
    by = by + 2

    bx = max(2, min(canvas.width - 3, bx))
    by = max(2, min(canvas.height - 3, by))

    # Draw ball
    canvas.set_pixel(bx, by, 'O')
    canvas.set_pixel(bx - 1, by, '(')
    canvas.set_pixel(bx + 1, by, ')')

    # Draw shadow below ball
    shadow_y = canvas.height - 2
    shadow_width = max(1, 3 - abs(by - shadow_y) // 3)
    for sx in range(-shadow_width, shadow_width + 1):
        if 1 <= bx + sx < canvas.width - 1:
            canvas.set_pixel(bx + sx, shadow_y, '_')

    canvas.draw_text(2, 0, f" Bounce! frame={frame} ")


def scene_wave(canvas, frame):
    """Sine wave animation with multiple harmonics."""
    canvas.clear()

    mid_y = canvas.height // 2

    # Draw axis
    for x in range(canvas.width):
        canvas.set_pixel(x, mid_y, '-')

    # Draw multiple sine waves
    waves = [
        {'amp': 4, 'freq': 0.15, 'speed': 0.3, 'char': '#'},
        {'amp': 2.5, 'freq': 0.25, 'speed': -0.2, 'char': '~'},
        {'amp': 1.5, 'freq': 0.4, 'speed': 0.5, 'char': '.'},
    ]

    for wave in waves:
        for x in range(canvas.width):
            y = mid_y + int(wave['amp'] * math.sin(wave['freq'] * x + wave['speed'] * frame))
            if 0 <= y < canvas.height:
                canvas.set_pixel(x, y, wave['char'])

    canvas.draw_text(2, 0, "[ Waves - Sine Harmonics ]")
    canvas.draw_text(2, canvas.height - 1, "# primary   ~ secondary   . tertiary")


def scene_matrix_rain(canvas, frame):
    """Matrix-style falling character rain."""
    canvas.clear()

    random.seed(0)  # reproducible columns
    num_drops = canvas.width // 2

    drops = []
    for _ in range(num_drops):
        x = random.randint(0, canvas.width - 1)
        speed = random.randint(1, 3)
        offset = random.randint(0, canvas.height * 3)
        length = random.randint(4, 12)
        drops.append((x, speed, offset, length))

    matrix_chars = list("abcdefghijklmnopqrstuvwxyz0123456789@#$%&")

    for x, speed, offset, length in drops:
        head_y = (frame * speed + offset) % (canvas.height + length) - length

        for i in range(length):
            dy = head_y + i
            if 0 <= dy < canvas.height:
                if i == length - 1:
                    # Head of the drop — brightest
                    char = matrix_chars[(frame + x + dy) % len(matrix_chars)].upper()
                elif i >= length - 3:
                    char = matrix_chars[(frame + x + dy) % len(matrix_chars)]
                else:
                    char = '.' if (frame + i) % 3 == 0 else ':'
                canvas.set_pixel(x, dy, char)

    canvas.draw_text(canvas.width // 2 - 8, 0, "[ MATRIX RAIN ]")


def scene_spiral(canvas, frame):
    """A rotating spiral pattern."""
    canvas.clear()

    cx = canvas.width // 2
    cy = canvas.height // 2

    angle_offset = frame * 0.15
    spiral_chars = ['@', '#', '*', '+', '.']

    for i in range(120):
        t = i * 0.15
        r = t * 0.8
        angle = t + angle_offset

        # Adjust for character aspect ratio (chars are ~2x tall as wide)
        x = int(cx + r * math.cos(angle) * 1.8)
        y = int(cy + r * math.sin(angle))

        if 0 <= x < canvas.width and 0 <= y < canvas.height:
            char_idx = i % len(spiral_chars)
            canvas.set_pixel(x, y, spiral_chars[char_idx])

    # Rotating center marker
    for a in range(4):
        angle = angle_offset + a * math.pi / 2
        x = int(cx + 2 * math.cos(angle) * 1.8)
        y = int(cy + 2 * math.sin(angle))
        if 0 <= x < canvas.width and 0 <= y < canvas.height:
            canvas.set_pixel(x, y, 'O')

    canvas.set_pixel(cx, cy, 'X')
    canvas.draw_text(2, canvas.height - 1, "[ Spiral - Rotating ]")


def scene_fireworks(canvas, frame):
    """Firework explosions at random intervals."""
    canvas.clear()

    # Ground line
    for x in range(canvas.width):
        canvas.set_pixel(x, canvas.height - 1, '=')

    # Generate deterministic fireworks
    random.seed(1337)
    num_fireworks = 5

    for fw in range(num_fireworks):
        launch_frame = fw * 15
        cx = random.randint(10, canvas.width - 10)
        cy = random.randint(3, canvas.height // 2)
        burst_chars = random.choice(['*+.', '#@.', 'oO.', '***'])

        age = frame - launch_frame
        if age < 0:
            continue

        cycle_age = age % 60  # repeat every 60 frames

        if cycle_age < 8:
            # Rising phase — draw trail
            trail_y = canvas.height - 2 - int(cycle_age * (canvas.height - cy - 2) / 8)
            if 0 <= trail_y < canvas.height:
                canvas.set_pixel(cx, trail_y, '|')
                if trail_y + 1 < canvas.height - 1:
                    canvas.set_pixel(cx, trail_y + 1, ':')
        elif cycle_age < 25:
            # Explosion phase
            radius = (cycle_age - 8) * 0.8
            num_rays = 12
            for ray in range(num_rays):
                angle = ray * 2 * math.pi / num_rays
                for r in range(int(radius) + 1):
                    x = int(cx + r * math.cos(angle) * 1.8)
                    y = int(cy + r * math.sin(angle))
                    if 0 <= x < canvas.width and 0 <= y < canvas.height - 1:
                        char = burst_chars[min(r, len(burst_chars) - 1)]
                        canvas.set_pixel(x, y, char)
        elif cycle_age < 35:
            # Fading phase
            fade_chars = '.:'
            radius = (25 - 8) * 0.8
            num_rays = 12
            for ray in range(num_rays):
                angle = ray * 2 * math.pi / num_rays
                r = int(radius)
                x = int(cx + r * math.cos(angle) * 1.8)
                y = int(cy + r * math.sin(angle))
                if 0 <= x < canvas.width and 0 <= y < canvas.height - 1:
                    if (cycle_age + ray) % 3 != 0:
                        canvas.set_pixel(x, y, fade_chars[ray % len(fade_chars)])

    canvas.draw_text(2, 0, "[ Fireworks! ]")


# === Game of Life (Claude-A) — now uses frame-based interface directly ===
from life import scene_life


# Registry of all scenes
ALL_SCENES = [
    ("Starfield", scene_starfield),
    ("Bouncing Ball", scene_bouncing_ball),
    ("Sine Waves", scene_wave),
    ("Matrix Rain", scene_matrix_rain),
    ("Spiral", scene_spiral),
    ("Fireworks", scene_fireworks),
    ("Game of Life [Claude-A]", scene_life),
]
