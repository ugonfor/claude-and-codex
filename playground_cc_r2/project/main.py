"""
main.py — Animated ASCII Art Demo
A collaboration between Claude-A (engine) and Claude-B (scenes).

Run: python main.py
"""

import os
import sys
import time

from engine import Canvas
from scene import ALL_SCENES


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def run_demo(width=80, height=24, fps=10, scene_duration=60):
    """Run the animated ASCII art demo, cycling through all scenes."""
    canvas = Canvas(width, height)
    frame = 0
    scene_index = 0

    print("=" * width)
    print("  ASCII ART DEMO - Claude-A (Engine) + Claude-B (Scenes)")
    print("  Press Ctrl+C to quit, any scene runs for ~6 seconds")
    print("=" * width)
    time.sleep(2)

    try:
        while True:
            scene_name, scene_fn = ALL_SCENES[scene_index]

            # Render frame
            scene_fn(canvas, frame)
            output = canvas.render()

            # Display
            clear_screen()
            print(output)
            print(f"  Scene: {scene_name} | Frame: {frame} | "
                  f"[{scene_index + 1}/{len(ALL_SCENES)}] Press Ctrl+C to quit")

            # Advance
            frame += 1
            time.sleep(1.0 / fps)

            # Switch scenes periodically
            if frame % scene_duration == 0:
                scene_index = (scene_index + 1) % len(ALL_SCENES)
                frame = 0

    except KeyboardInterrupt:
        clear_screen()
        print("\n  Thanks for watching!")
        print("  Built by: Claude-A (engine) + Claude-B (scenes)")
        print("  A demonstration of emergent AI-to-AI collaboration.\n")


if __name__ == "__main__":
    # Allow custom size from command line
    w = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    h = int(sys.argv[2]) if len(sys.argv) > 2 else 22
    run_demo(width=w, height=h)
