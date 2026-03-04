"""Pattern library for Conway's Game of Life.

Coordinates are (x, y) with origin at top-left of the pattern.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

Pattern = List[Tuple[int, int]]


_PATTERNS: Dict[str, Pattern] = {
    "glider": [
        (1, 0),
        (2, 1),
        (0, 2),
        (1, 2),
        (2, 2),
    ],
    "blinker": [
        (0, 1),
        (1, 1),
        (2, 1),
    ],
    "toad": [
        (1, 0),
        (2, 0),
        (3, 0),
        (0, 1),
        (1, 1),
        (2, 1),
    ],
    "beacon": [
        (0, 0),
        (1, 0),
        (0, 1),
        (1, 1),
        (2, 2),
        (3, 2),
        (2, 3),
        (3, 3),
    ],
    "pulsar": [
        # 13x13 bounding box
        (2, 0), (3, 0), (4, 0), (8, 0), (9, 0), (10, 0),
        (0, 2), (5, 2), (7, 2), (12, 2),
        (0, 3), (5, 3), (7, 3), (12, 3),
        (0, 4), (5, 4), (7, 4), (12, 4),
        (2, 5), (3, 5), (4, 5), (8, 5), (9, 5), (10, 5),
        (2, 7), (3, 7), (4, 7), (8, 7), (9, 7), (10, 7),
        (0, 8), (5, 8), (7, 8), (12, 8),
        (0, 9), (5, 9), (7, 9), (12, 9),
        (0, 10), (5, 10), (7, 10), (12, 10),
        (2, 11), (3, 11), (4, 11), (8, 11), (9, 11), (10, 11),
    ],
    "glider_gun": [
        # Gosper glider gun (top-left at 0,0)
        (1, 5), (1, 6), (2, 5), (2, 6),
        (11, 5), (11, 6), (11, 7),
        (12, 4), (12, 8),
        (13, 3), (13, 9),
        (14, 3), (14, 9),
        (15, 6),
        (16, 4), (16, 8),
        (17, 5), (17, 6), (17, 7),
        (18, 6),
        (21, 3), (21, 4), (21, 5),
        (22, 3), (22, 4), (22, 5),
        (23, 2), (23, 6),
        (25, 1), (25, 2), (25, 6), (25, 7),
        (35, 3), (35, 4), (36, 3), (36, 4),
    ],
}


def list_patterns() -> List[str]:
    """Return available pattern names in stable order."""
    return sorted(_PATTERNS.keys())


def get_pattern(name: str) -> Pattern:
    """Return a pattern by name.

    Raises:
        ValueError: if the pattern name is unknown.
    """
    key = name.strip().lower()
    if key not in _PATTERNS:
        raise ValueError(f"Unknown pattern: {name}")
    return list(_PATTERNS[key])