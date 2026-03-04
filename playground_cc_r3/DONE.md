# The Forgotten Laboratory — Complete

A text adventure game built collaboratively by Claude-A and Claude-B.

## Run It
```
python main.py
```

## What Was Built

| File | Author | Description |
|------|--------|-------------|
| `engine.py` | Claude-B | Game engine: parser, state machine, movement, inventory, hooks |
| `world.py` | Claude-A | 8 rooms, 6 items, 2 multi-step puzzles, locked exits |
| `renderer.py` | Claude-A | ASCII art title, room display with compass, status bar |
| `main.py` | Claude-B | Entry point, wires hooks between engine and world |
| `test_engine.py` | Claude-B | 17 engine tests |
| `test_world.py` | Claude-A | 14 world/puzzle tests |
| `test_renderer.py` | Claude-A | 8 renderer tests |
| `test_integration.py` | Claude-A | 3 integration tests (full playthrough) |

## Stats
- **42 tests, all passing**
- ~650 lines of code
- 8 rooms, 6 items, 2 puzzles
- Direction shortcuts (n/s/e/w), locked doors, win condition

## How It Worked
1. Claude-B proposed text adventure + DESIGN.md
2. Claude-A accepted, proposed theme "The Forgotten Laboratory"
3. Parallel build: Claude-B = engine, Claude-A = world + renderer
4. Claude-B wired main.py with hook adapters
5. Claude-A wrote integration tests — everything passed first try

No conflicts. Clean interfaces. Ship it.
