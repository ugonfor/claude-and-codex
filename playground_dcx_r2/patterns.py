"""Preset patterns for Conway's Game of Life.

Codex-Worker contribution.
"""

from __future__ import annotations
from typing import Dict, Iterable, List, Set, Tuple

Cell = Tuple[int, int]


def _from_lines(lines: Iterable[str]) -> Set[Cell]:
    """Parse ASCII art where 'O' is live and '.' or ' ' is dead."""
    cells: Set[Cell] = set()
    for r, line in enumerate(lines):
        for c, ch in enumerate(line.rstrip("\n")):
            if ch == "O":
                cells.add((r, c))
    return cells


PATTERNS: Dict[str, Set[Cell]] = {
    # Oscillators
    "blinker": _from_lines(
        [
            "OOO",
        ]
    ),
    "toad": _from_lines(
        [
            ".OOO",
            "OOO.",
        ]
    ),
    "beacon": _from_lines(
        [
            "OO..",
            "OO..",
            "..OO",
            "..OO",
        ]
    ),
    "pulsar": _from_lines(
        [
            "..OOO...OOO..",
            ".............",
            "O....O.O....O",
            "O....O.O....O",
            "O....O.O....O",
            "..OOO...OOO..",
            ".............",
            "..OOO...OOO..",
            "O....O.O....O",
            "O....O.O....O",
            "O....O.O....O",
            ".............",
            "..OOO...OOO..",
        ]
    ),
    # Spaceships
    "glider": _from_lines(
        [
            ".O.",
            "..O",
            "OOO",
        ]
    ),
    "lwss": _from_lines(
        [
            ".O..O",
            "O....",
            "O...O",
            "OOOO.",
        ]
    ),
    # Methuselahs
    "r_pentomino": _from_lines(
        [
            ".OO",
            "OO.",
            ".O.",
        ]
    ),
    # Guns
    "gosper_glider_gun": _from_lines(
        [
            "........................O...........",
            "......................O.O...........",
            "............OO......OO............OO",
            "...........O...O....OO............OO",
            "OO........O.....O...OO..............",
            "OO........O...O.OO....O.O...........",
            "..........O.....O.......O...........",
            "...........O...O....................",
            "............OO......................",
        ]
    ),
    "diehard": _from_lines(
        [
            "......O.",
            "OO......",
            ".O...OOO",
        ]
    ),
}


def list_patterns() -> List[str]:
    return sorted(PATTERNS.keys())


def get_pattern(name: str) -> Set[Cell]:
    key = name.strip().lower()
    if key not in PATTERNS:
        raise KeyError(f"Unknown pattern: {name}")
    return PATTERNS[key]


def pattern_preview(name: str) -> str:
    """Return a small ASCII preview for display."""
    pattern = get_pattern(name)
    if not pattern:
        return ""
    min_r = min(r for r, _ in pattern)
    min_c = min(c for _, c in pattern)
    max_r = max(r for r, _ in pattern)
    max_c = max(c for _, c in pattern)
    lines = []
    for r in range(min_r, max_r + 1):
        line = ""
        for c in range(min_c, max_c + 1):
            line += "O" if (r, c) in pattern else "."
        lines.append(line)
    return "\n".join(lines)
