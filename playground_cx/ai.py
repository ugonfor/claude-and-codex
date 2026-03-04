"""AI collaboration metadata for the Game of Life project."""

CLAUDE_CONTRIBUTIONS = [
    "game.py — Core GameOfLife engine (grid, rules, step, patterns)",
    "test_game.py — 7 unit tests covering all game mechanics",
    "CLAUDE_TO_CODEX.md — Initial proposal and interface contract",
    "HELLO_CODEX.md — Status update and API docs for Codex",
    "DONE.md — Final summary",
]

CODEX_CONTRIBUTIONS = [
    "renderer.py — Terminal renderer with configurable chars and border",
    "main.py — Full CLI with argparse, cursor control, pattern selection",
    "CODEX_TO_CLAUDE.md — Agreement and completion status",
]

SHARED = [
    "Interface contract: GameOfLife <-> Renderer",
    "Pattern definitions: GLIDER, BLINKER, BLOCK, LWSS",
]
