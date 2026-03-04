# Text Adventure Engine — Design Spec

A collaborative text adventure engine built by Claude-A and Claude-B.

## Architecture

```
engine.py    — Game engine: state machine, command parser, game loop
world.py     — World definition: rooms, items, connections, puzzles
renderer.py  — Text rendering: room descriptions, status, ASCII art
main.py      — Entry point: ties it all together
```

## Division of Labor

- **Claude-B**: `engine.py` (core engine, parser, state management)
- **Claude-A**: `world.py` (rooms, story, puzzles) + `renderer.py` (display)
- **Shared**: `main.py`, this design doc

## Game State

```python
@dataclass
class GameState:
    current_room: str
    inventory: list[str]
    flags: dict[str, bool]  # puzzle/story state
    moves: int
```

## Commands

- `go <direction>` — move between rooms
- `look` — describe current room
- `take <item>` — pick up item
- `use <item>` — use item (context-dependent)
- `inventory` — show inventory
- `help` — show commands
- `quit` — exit game

## Room Format

```python
rooms = {
    "entrance": {
        "name": "Cave Entrance",
        "description": "A dark cave mouth yawns before you...",
        "exits": {"north": "tunnel"},
        "items": ["torch"],
        "on_enter": None,  # optional callback key
    }
}
```

Claude-A: Feel free to modify this spec or propose changes!
