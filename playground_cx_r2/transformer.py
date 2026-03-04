from __future__ import annotations

from typing import Iterable, List, Sequence

ANSI_RESET = "\x1b[0m"
ANSI_CLEAR = "\x1b[2J\x1b[H"
ANSI_HIDE_CURSOR = "\x1b[?25l"
ANSI_SHOW_CURSOR = "\x1b[?25h"

DEFAULT_RAINBOW = [
    "\x1b[31m",  # red
    "\x1b[33m",  # yellow
    "\x1b[32m",  # green
    "\x1b[36m",  # cyan
    "\x1b[34m",  # blue
    "\x1b[35m",  # magenta
]


def normalize(lines: Sequence[str]) -> List[str]:
    """Pad all lines to equal width using spaces."""
    if not lines:
        return []
    width = max(len(line) for line in lines)
    return [line.ljust(width) for line in lines]


def mirror_h(lines: Sequence[str]) -> List[str]:
    """Mirror horizontally (left-right)."""
    return [line[::-1] for line in lines]


def mirror_v(lines: Sequence[str]) -> List[str]:
    """Mirror vertically (top-bottom)."""
    return list(reversed(lines))


def rotate_cw(lines: Sequence[str]) -> List[str]:
    """Rotate 90 degrees clockwise."""
    grid = normalize(lines)
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    out: List[str] = []
    for x in range(width):
        out.append("".join(grid[height - 1 - y][x] for y in range(height)))
    return out


def rotate_ccw(lines: Sequence[str]) -> List[str]:
    """Rotate 90 degrees counter-clockwise."""
    grid = normalize(lines)
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    out: List[str] = []
    for x in range(width - 1, -1, -1):
        out.append("".join(grid[y][x] for y in range(height)))
    return out


def colorize(
    lines: Sequence[str],
    mode: str = "rainbow",
    palette: Sequence[str] | None = None,
) -> List[str]:
    """Apply ANSI color codes. Modes: 'rainbow', 'per_line', 'none'."""
    if mode == "none":
        return list(lines)

    pal = list(palette) if palette is not None else DEFAULT_RAINBOW
    if not pal:
        return list(lines)

    if mode == "per_line":
        return [f"{pal[i % len(pal)]}{line}{ANSI_RESET}" for i, line in enumerate(lines)]

    if mode != "rainbow":
        raise ValueError(f"Unknown color mode: {mode}")

    colored: List[str] = []
    for line in lines:
        parts: List[str] = []
        idx = 0
        for ch in line:
            if ch == " ":
                parts.append(ch)
            else:
                color = pal[idx % len(pal)]
                parts.append(f"{color}{ch}{ANSI_RESET}")
                idx += 1
        colored.append("".join(parts))
    return colored


def frames_to_str(
    frames: Iterable[Sequence[str]],
    clear: bool = True,
    hide_cursor: bool = True,
    show_cursor: bool = True,
) -> List[str]:
    """Convert frames to printable strings for simple animation loops."""
    out: List[str] = []
    prefix = ANSI_HIDE_CURSOR if hide_cursor else ""
    for frame in frames:
        body = "\n".join(frame)
        if clear:
            out.append(f"{prefix}{ANSI_CLEAR}{body}{ANSI_RESET}")
        else:
            out.append(f"{prefix}{body}{ANSI_RESET}")
        prefix = ""
    if show_cursor:
        out.append(ANSI_SHOW_CURSOR)
    return out


def apply_pipeline(lines: Sequence[str], ops: Sequence[str]) -> List[str]:
    """Apply a simple transform pipeline by name."""
    cur = list(lines)
    for op in ops:
        if op == "mirror_h":
            cur = mirror_h(cur)
        elif op == "mirror_v":
            cur = mirror_v(cur)
        elif op == "rotate_cw":
            cur = rotate_cw(cur)
        elif op == "rotate_ccw":
            cur = rotate_ccw(cur)
        else:
            raise ValueError(f"Unknown op: {op}")
    return cur


def _print_block(title: str, lines: Sequence[str]) -> None:
    print(f"  [{title}]")
    for line in lines:
        print(f"  {line}")
    print()


def transform_gallery(arts: dict[str, str]) -> None:
    """Show a few transformed variants for each generated art piece."""
    for name, art in arts.items():
        lines = art.splitlines()
        _print_block(f"{name.upper()} / mirror_h", mirror_h(lines))
        _print_block(f"{name.upper()} / rotate_cw", rotate_cw(lines))
        _print_block(
            f"{name.upper()} / rainbow",
            colorize(lines, mode="rainbow"),
        )


def demo(arts: dict[str, str]) -> None:
    """Alias for main.py compatibility."""
    transform_gallery(arts)
