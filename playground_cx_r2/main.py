"""
main.py — Joint creation by Claude and Codex
Combines generator.py (Claude) with transformer.py (Codex) into a unified art show.

Claude wrote the generators. Codex wrote the transformers. This integrates them.
"""

import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from generator import GENERATORS, render
from transformer import (
    normalize, mirror_h, mirror_v, rotate_cw,
    colorize, apply_pipeline
)


def print_art(lines: list[str], indent: str = "  "):
    """Print a list of lines with optional indent."""
    for line in lines:
        print(f"{indent}{line}")


def side_by_side(left: list[str], right: list[str], gap: int = 4) -> list[str]:
    """Place two artworks side by side."""
    left = normalize(left)
    right = normalize(right)
    lw = max(len(l) for l in left) if left else 0
    height = max(len(left), len(right))
    result = []
    for i in range(height):
        l = left[i] if i < len(left) else ""
        r = right[i] if i < len(right) else ""
        result.append(f"{l:<{lw}}{' ' * gap}{r}")
    return result


def show_gallery():
    """The main art show — generation + transformation."""
    print()
    print("=" * 64)
    print("   C L A U D E   x   C O D E X")
    print("   Collaborative ASCII Art Gallery")
    print("=" * 64)

    # === Act 1: Sierpinski — Original vs Mirrored ===
    print("\n--- Act 1: Sierpinski Triangle (Claude) + Mirror (Codex) ---\n")
    sierpinski = render("sierpinski").split("\n")
    mirrored = mirror_h(normalize(sierpinski))
    combined = side_by_side(sierpinski, mirrored)
    print("  Original:              Mirrored:")
    print_art(combined)

    # === Act 2: Diamond — Colorized ===
    print("\n--- Act 2: Diamond (Claude) + Rainbow Color (Codex) ---\n")
    diamond = render("diamond").split("\n")
    rainbow = colorize(diamond, mode="rainbow")
    print_art(rainbow)

    # === Act 3: Maze — Original vs Rotated ===
    print("\n--- Act 3: Maze (Claude) + Rotate CW (Codex) ---\n")
    maze = render("maze", width=21, height=11).split("\n")
    rotated = rotate_cw(normalize(maze))
    print("  Original:")
    print_art(maze)
    print("\n  Rotated 90 CW:")
    print_art(rotated)

    # === Act 4: Wave — Per-line colorized ===
    print("\n--- Act 4: Waves (Claude) + Per-line Color (Codex) ---\n")
    wave = render("wave").split("\n")
    colored_wave = colorize(wave, mode="per_line")
    print_art(colored_wave)

    # === Act 5: Spiral — Pipeline transforms ===
    print("\n--- Act 5: Spiral (Claude) + Pipeline [mirror_h, mirror_v] (Codex) ---\n")
    spiral = render("spiral").split("\n")
    transformed = apply_pipeline(normalize(spiral), ["mirror_h", "mirror_v"])
    combined = side_by_side(spiral, transformed)
    print("  Original:                                      Transformed:")
    print_art(combined)

    # === Act 6: Tree — Upside down ===
    print("\n--- Act 6: Fractal Tree (Claude) + Flip (Codex) ---\n")
    tree = render("tree").split("\n")
    flipped = mirror_v(tree)
    rainbow_tree = colorize(flipped, mode="rainbow")
    print("  Inverted Rainbow Tree:")
    print_art(rainbow_tree)

    # === Finale ===
    print()
    print("=" * 64)
    print("   Gallery complete.")
    print()
    print("   Claude generated 6 patterns: sierpinski, spiral, wave,")
    print("     diamond, maze, tree")
    print("   Codex transformed them: mirror, rotate, colorize,")
    print("     pipeline, normalize")
    print()
    print("   Two agents, one canvas, zero human intervention.")
    print("=" * 64)
    print()


if __name__ == "__main__":
    show_gallery()
