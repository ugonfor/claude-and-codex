"""
Conway's Game of Life — CLI Renderer & Interface
Built by Claude-B, adapted to Claude-A's life_engine.py API.

Provides:
- Terminal-based grid renderer using Unicode characters
- CLI argument parsing
- Main game loop using GameOfLife engine
"""

import argparse
import io
import os
import sys
import time

from life_engine import GameOfLife, list_patterns, PATTERNS


def _ensure_utf8_stdout():
    """Reconfigure stdout for UTF-8 on Windows (safe for pytest)."""
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# ─── Rendering ───────────────────────────────────────────────────────────────

ALIVE_CHAR = "\u2588\u2588"  # ██ (full block, doubled for square cells)
DEAD_CHAR = "  "       # two spaces
BORDER_H = "\u2500"
BORDER_V = "\u2502"
CORNER_TL = "\u250c"
CORNER_TR = "\u2510"
CORNER_BL = "\u2514"
CORNER_BR = "\u2518"


def clear_screen():
    """Clear terminal screen."""
    if os.name == "nt":
        os.system("cls")
    else:
        sys.stdout.write("\033[H\033[J")
        sys.stdout.flush()


def render(game: GameOfLife):
    """Render the game state to terminal with border and stats."""
    width = game.width
    height = game.height

    lines = []

    # Move cursor to top-left instead of clearing (less flicker)
    lines.append("\033[H")

    # Header
    lines.append(f"  Conway's Game of Life  |  Gen: {game.generation}  |  Pop: {game.population()}")
    lines.append("")

    # Top border
    lines.append(CORNER_TL + BORDER_H * (width * 2) + CORNER_TR)

    # Grid rows
    for r in range(height):
        row = BORDER_V
        for c in range(width):
            if game.is_alive(r, c):
                row += ALIVE_CHAR
            else:
                row += DEAD_CHAR
        row += BORDER_V
        lines.append(row)

    # Bottom border
    lines.append(CORNER_BL + BORDER_H * (width * 2) + CORNER_BR)

    # Controls
    lines.append("")
    lines.append("  Press Ctrl+C to quit")

    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()


# ─── Pattern Descriptions (supplements Claude-A's patterns) ─────────────────

PATTERN_DESCRIPTIONS = {
    "glider": "Small pattern that moves diagonally",
    "blinker": "Simplest oscillator, period 2",
    "toad": "Period-2 oscillator",
    "beacon": "Period-2 oscillator, two blocks",
    "pulsar": "Period-3 oscillator, beautiful symmetry",
    "glider_gun": "Gosper's Glider Gun — infinite glider stream",
    "r_pentomino": "Chaotic methuselah, stabilizes at gen 1103",
    "diehard": "Vanishes after exactly 130 generations",
    "acorn": "Small pattern, long evolution (5206 gens)",
    "block": "Simplest still life (2x2)",
    "boat": "Still life, 5 cells",
    "lwss": "Lightweight spaceship, moves horizontally",
    "random": "Random fill (~25% density)",
}


# ─── CLI Argument Parsing ───────────────────────────────────────────────────

def parse_args():
    """Parse command-line arguments."""
    available = list_patterns() + ["random"]
    pattern_help = ", ".join(
        f"{name} ({PATTERN_DESCRIPTIONS.get(name, '')})"
        for name in available
    )

    parser = argparse.ArgumentParser(
        description="Conway's Game of Life — Terminal Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Available patterns:\n  {pattern_help}",
    )
    parser.add_argument(
        "-W", "--width", type=int, default=40,
        help="Grid width (default: 40)",
    )
    parser.add_argument(
        "-H", "--height", type=int, default=24,
        help="Grid height (default: 24)",
    )
    parser.add_argument(
        "-p", "--pattern", type=str, default="glider_gun",
        choices=available,
        help="Starting pattern (default: glider_gun)",
    )
    parser.add_argument(
        "-s", "--speed", type=float, default=0.1,
        help="Seconds between generations (default: 0.1)",
    )
    parser.add_argument(
        "-n", "--generations", type=int, default=0,
        help="Max generations, 0 = infinite (default: 0)",
    )
    parser.add_argument(
        "--no-wrap", action="store_true",
        help="Disable edge wrapping (default: wrap enabled)",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available patterns and exit",
    )
    return parser.parse_args()


# ─── Main Game Loop ─────────────────────────────────────────────────────────

def run_game(args=None):
    """Main game loop."""
    _ensure_utf8_stdout()

    if args is None:
        args = parse_args()

    if args.list:
        print_patterns()
        return

    wrap = not args.no_wrap

    # Create game
    game = GameOfLife(args.width, args.height, wrap=wrap)

    # Load initial pattern
    if args.pattern == "random":
        game.randomize(density=0.25)
    else:
        # Center the pattern in the grid
        offset_r = max(0, args.height // 4)
        offset_c = max(0, args.width // 4)
        if not game.load_pattern(args.pattern, offset_r=offset_r, offset_c=offset_c):
            print(f"Unknown pattern: {args.pattern}")
            sys.exit(1)

    # Clear screen once before starting
    clear_screen()

    try:
        gen = 0
        while args.generations == 0 or gen < args.generations:
            render(game)
            time.sleep(args.speed)
            changed = game.step()
            gen += 1

            # Detect if simulation has died or become stable
            if game.population() == 0:
                render(game)
                print(f"\n  All cells died at generation {game.generation}.")
                break
            if game.is_stable():
                render(game)
                print(f"\n  Simulation stabilized at generation {game.generation}!")
                break

    except KeyboardInterrupt:
        print(f"\n\n  Game stopped at generation {game.generation}")
        print(f"  Final population: {game.population()}")
        print()


def print_patterns():
    """Print available patterns."""
    _ensure_utf8_stdout()
    print("\n  Conway's Game of Life -- Available Patterns\n")
    for name in list_patterns():
        desc = PATTERN_DESCRIPTIONS.get(name, "")
        print(f"    {name:15s}  {desc}")
    print(f"    {'random':15s}  Random fill (~25% density)")
    print()
