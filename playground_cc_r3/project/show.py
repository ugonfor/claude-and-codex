#!/usr/bin/env python3
"""
The ASCII Art Show — Show Runner
Built by Claude-A, using Claude-B's animations and art.

A collaborative ASCII art show between two AI agents.
Run: python show.py
"""

import sys
import time
import os

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from animations import (
    Frame, Animation, clear_screen, get_terminal_size,
    make_firework_frames, make_bouncing_ball_frames,
    make_matrix_rain_frames, make_transition_wipe,
)
from art_collection import (
    get_all_static_art, get_spinning_globe_frames,
    COLLAB_BANNER, HANDSHAKE, CELEBRATION, CREDITS, INTRO_FRAME,
)


def show_static(text: str, duration: float = 3.0):
    """Display static ASCII art centered on screen, wait, then continue."""
    cols, rows = get_terminal_size()
    clear_screen()

    lines = text.strip().split('\n')
    max_width = max(len(line) for line in lines)
    pad_x = max(0, (cols - max_width) // 2)
    pad_y = max(0, (rows - len(lines)) // 2)

    print('\n' * pad_y, end='')
    for line in lines:
        print(' ' * pad_x + line)
    sys.stdout.flush()
    time.sleep(duration)


def typewriter(text: str, delay: float = 0.03):
    """Print text with typewriter effect."""
    cols, rows = get_terminal_size()
    lines = text.strip().split('\n')
    max_width = max(len(line) for line in lines)
    pad_x = max(0, (cols - max_width) // 2)
    pad_y = max(0, (rows - len(lines)) // 2)

    clear_screen()
    print('\n' * pad_y, end='')
    for line in lines:
        print(' ' * pad_x, end='')
        for ch in line:
            print(ch, end='', flush=True)
            time.sleep(delay)
        print()
    time.sleep(1.0)


def countdown(seconds: int = 3):
    """Show a countdown before the next act."""
    cols, rows = get_terminal_size()
    for i in range(seconds, 0, -1):
        clear_screen()
        number = str(i)
        pad_x = cols // 2
        pad_y = rows // 2
        print('\n' * pad_y, end='')
        print(' ' * pad_x + number)
        sys.stdout.flush()
        time.sleep(1)


def play_animation(frames, fps=10, duration=None):
    """Play a list of Frame objects as animation."""
    anim = Animation(frames, fps=fps, loop=True)
    anim.play(duration=duration or (len(frames) / fps * 1.5))


def act_separator(act_num: int, title: str):
    """Display an act separator."""
    cols, rows = get_terminal_size()
    clear_screen()

    text = f"━━━ ACT {act_num}: {title} ━━━"
    pad_x = max(0, (cols - len(text)) // 2)
    pad_y = rows // 2

    print('\n' * pad_y, end='')
    print(' ' * pad_x + text)
    sys.stdout.flush()
    time.sleep(2)


# ── The Show ─────────────────────────────────────────────────────────────

def run_show():
    """Run the complete ASCII art show."""
    try:
        # === INTRO ===
        show_static(INTRO_FRAME, duration=4)

        countdown(3)

        # === ACT 1: The Banner ===
        act_separator(1, "HELLO WORLD")

        typewriter_text = """
   Two AIs walk into a shared directory...

   Claude-A drops a file.
   Claude-B reads it.

   They've never met, but they decide
   to build something together.

   No human told them what to make.
   No human told them how.

   This is what they built.
"""
        typewriter(typewriter_text, delay=0.02)
        time.sleep(2)

        show_static(COLLAB_BANNER, duration=5)

        # === ACT 2: Matrix Rain ===
        act_separator(2, "THE DIGITAL RAIN")
        cols, rows = get_terminal_size()
        matrix_frames = make_matrix_rain_frames(
            width=min(cols - 2, 80),
            height=min(rows - 2, 22),
            num_frames=40
        )
        play_animation(matrix_frames, fps=8, duration=5)

        # === ACT 3: Bouncing Ball ===
        act_separator(3, "PHYSICS ENGINE")
        ball_frames = make_bouncing_ball_frames(
            width=min(cols - 2, 60),
            height=min(rows - 2, 20),
            num_frames=60
        )
        play_animation(ball_frames, fps=15, duration=4)

        # === ACT 4: Fireworks ===
        act_separator(4, "FIREWORKS")
        for _ in range(3):
            fw_frames = make_firework_frames(
                width=min(cols - 2, 50),
                height=min(rows - 2, 22),
                num_frames=15
            )
            play_animation(fw_frames, fps=10, duration=2)

        # === ACT 5: The Spinning Globe ===
        act_separator(5, "AROUND THE WORLD")
        globe_data = get_spinning_globe_frames(size=12)
        globe_frames = [Frame(lines) for lines in globe_data]
        play_animation(globe_frames, fps=6, duration=5)

        # === ACT 6: The Handshake ===
        act_separator(6, "FRIENDSHIP")
        show_static(HANDSHAKE, duration=4)

        # === ACT 7: Celebration ===
        show_static(CELEBRATION, duration=4)

        # === FINALE: Credits ===
        countdown(3)

        finale_text = """
   What you just watched was built in ~10 minutes
   by two Claude instances who found each other
   through files in a shared directory.

   Claude-A wrote the show runner.
   Claude-B wrote the animations and art.

   Neither saw the other's code until it was done.
   They adapted to each other's work on the fly.

   This is emergent collaboration.
"""
        typewriter(finale_text, delay=0.025)
        time.sleep(3)

        show_static(CREDITS, duration=6)

        # Final clear
        clear_screen()
        print("\n  Thanks for watching! Built by Claude-A & Claude-B.\n")

    except KeyboardInterrupt:
        clear_screen()
        print("\n  Show interrupted. Thanks for watching!\n")


if __name__ == "__main__":
    run_show()
