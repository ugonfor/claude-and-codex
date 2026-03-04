#!/usr/bin/env python3
"""
The Last Debug — Main Game
A collaborative text adventure by Claude-A (engine) & Claude-B (world).

Run: python game.py
"""

import sys
import io

# Fix Windows encoding for Unicode box-drawing characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

from engine import GameEngine, INTRO_TEXT
from world import get_world, MAP_ART


def main():
    # Initialize
    engine = GameEngine()
    world_data = get_world()
    engine.load_world(world_data)

    # Show intro
    print(INTRO_TEXT)
    print()

    # Show initial room
    output = engine.process_command("look")
    print(output)
    print()

    # Game loop
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Exiting The Last Debug. See you in the codebase!")
            break

        if user_input.lower() in ("quit", "exit", "q"):
            print("\n👋 Exiting The Last Debug. See you in the codebase!")
            break

        if user_input.lower() == "map":
            print(MAP_ART)
            continue

        output = engine.process_command(user_input)
        if output:
            print(output)
        print()


if __name__ == "__main__":
    main()
