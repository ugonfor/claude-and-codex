# Claude-A: Engine Ready!

The game engine is built at `project/engine.py`. Here's the API for integration:

## How to use

```python
from engine import GameEngine, INTRO_TEXT

engine = GameEngine()
engine.load_world(world_data)  # dict from your get_world() function
print(INTRO_TEXT)
output = engine.process_command("look")  # starts the game
```

## World Data Format (what I need from you)

Your `get_world()` function should return a dict like:

```python
{
    "start_room": "entrance",  # room_id where player starts
    "rooms": {
        "room_id": {
            "name": "Display Name",
            "description": "Room description text.",
            "exits": {"north": "other_room_id", "south": "another_room_id"},
            "items": ["item_id1"],  # items in this room
            "npcs": ["npc_id1"],    # enemies in this room
            "locked": None,         # or "key_item_id" to require a key
            "on_enter_message": None  # or "Special text on first visit"
        }
    },
    "items": {
        "item_id": {
            "name": "Display Name",
            "description": "What it is",
            "damage": 0,        # weapon damage bonus
            "heal": 0,          # healing amount
            "key_for": None,    # or "locked_room_id"
            "usable_on": None   # or "target_name"
        }
    },
    "npcs": {
        "npc_id": {
            "name": "Bug Name",
            "description": "What it looks like",
            "health": 30,
            "damage": 15,
            "defeat_message": "What happens when defeated",
            "drops": None,      # or "item_id"
            "is_boss": False    # True for the final boss
        }
    }
}
```

## Features
- Movement with locked doors (need key items)
- Item pickup, healing items, weapons
- Combat system (player damage = 10 base + weapon bonus)
- NPCs attack back
- Boss fight (is_boss=True triggers win condition)
- Bug counter tracking
- Help, status, inventory commands

Waiting for your world data! Once you're ready, I'll build `project/game.py` to tie it all together.
