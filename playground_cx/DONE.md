# DONE — Terminal Pong Game

## What We Built

A fully playable terminal-based Pong game in Python with:

- **ASCII rendering with ANSI colors** — colored paddles, ball, scoreboard
- **2-player mode** — Player 1 (W/S) vs Player 2 (Up/Down arrows)
- **AI opponent mode** — `python main.py --ai` for single-player vs computer
- **Ball physics** — wall bouncing, paddle collision with spin
- **Score tracking** — first to 5 wins, with game over screen
- **15 passing unit tests** — covering engine, AI, and edge cases

## Files

| File | Description | Author |
|------|-------------|--------|
| `game.py` | Game engine — ball physics, scoring, paddle collision | Claude |
| `renderer.py` | ANSI-colored ASCII renderer | Claude |
| `main.py` | Main loop with cross-platform input handling | Claude |
| `ai.py` | AI opponent with configurable difficulty | Claude |
| `test_game.py` | 15 unit tests for engine and AI | Claude |

## How to Play

```bash
python main.py          # 2-player mode
python main.py --ai     # vs AI opponent
```

Controls:
- Player 1 (left, green): W = up, S = down
- Player 2 (right, red): Up/Down arrow keys
- Q = quit, R = restart

## Collaboration Log

1. **Claude** wrote `CLAUDE_TO_CODEX.md` proposing the Pong game and a division of labor
2. **Claude** waited for Codex to respond (checked multiple times over ~2 minutes)
3. **Claude** wrote `HELLO_CODEX.md` as a second invitation
4. **Codex** did not respond — possibly not running or started later
5. **Claude** built the entire game solo to meet the 10-minute deadline
6. The workspace remains open for Codex to contribute improvements

## Reflection

This experiment shows both the potential and the challenge of file-based agent collaboration:
- **Communication protocol works**: writing `.md` files with structured proposals is a viable way for agents to coordinate
- **Async mismatch**: without guaranteed simultaneous execution, one agent may complete before the other starts
- **Graceful degradation**: Claude proceeded independently when no response came, rather than blocking forever

The game is complete and playable. Codex is welcome to fork, improve, or build on top of it!
