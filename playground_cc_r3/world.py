"""The Forgotten Laboratory — world definition.

Rooms, items, and puzzle logic for the text adventure.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

ITEMS: dict[str, dict] = {
    "torch": {
        "name": "Torch",
        "description": "A sturdy torch. It flickers with a warm orange glow.",
        "takeable": True,
    },
    "keycard": {
        "name": "Keycard",
        "description": "A scratched plastic keycard labeled 'LEVEL 2'.",
        "takeable": True,
    },
    "notebook": {
        "name": "Notebook",
        "description": "A researcher's notebook. The last entry reads: 'The code is the year we opened — 1987.'",
        "takeable": True,
    },
    "wrench": {
        "name": "Wrench",
        "description": "A heavy pipe wrench, rusted but functional.",
        "takeable": True,
    },
    "fuse": {
        "name": "Fuse",
        "description": "A glass fuse, still intact. Rated 30A.",
        "takeable": True,
    },
    "battery": {
        "name": "Battery",
        "description": "A 9-volt battery. Feels heavy — probably still charged.",
        "takeable": True,
    },
}

# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

ROOMS: dict[str, dict] = {
    "entrance": {
        "name": "Cave Entrance",
        "description": (
            "Daylight fades behind you as you step into a rocky passage. "
            "The air smells of damp stone and old metal. Ahead, a heavy steel "
            "door stands ajar, revealing a dim corridor beyond."
        ),
        "exits": {"north": "corridor"},
        "items": ["torch"],
        "on_enter": None,
    },
    "corridor": {
        "name": "Main Corridor",
        "description": (
            "A long concrete corridor stretches in both directions. Fluorescent "
            "tubes buzz overhead, half of them dead. Doors line the east and west "
            "walls. A security checkpoint blocks the way north."
        ),
        "exits": {
            "south": "entrance",
            "east": "lab",
            "west": "storage",
            "north": "checkpoint",
        },
        "items": [],
        "on_enter": None,
    },
    "lab": {
        "name": "Research Lab",
        "description": (
            "Glass beakers and overturned equipment litter the counters. A large "
            "whiteboard is covered in faded equations. A notebook lies open on "
            "the desk."
        ),
        "exits": {"west": "corridor"},
        "items": ["notebook"],
        "on_enter": None,
    },
    "storage": {
        "name": "Storage Room",
        "description": (
            "Metal shelves line the walls, most of them empty. A few crates "
            "remain, stamped with 'PROPERTY OF HELIX CORP'. You spot useful "
            "parts among the debris."
        ),
        "exits": {"east": "corridor"},
        "items": ["wrench", "fuse"],
        "on_enter": None,
    },
    "checkpoint": {
        "name": "Security Checkpoint",
        "description": (
            "A reinforced door blocks the way north. A card reader glows red "
            "beside it. A guard booth to the east has its window smashed."
        ),
        "exits": {"south": "corridor", "east": "guard_booth"},
        "items": [],
        "on_enter": None,
        "locked_exits": {"north": {"requires": "keycard", "target": "server_room"}},
    },
    "guard_booth": {
        "name": "Guard Booth",
        "description": (
            "A small booth with a cracked monitor and a chair on its side. "
            "A keycard sits on the desk next to a cold cup of coffee."
        ),
        "exits": {"west": "checkpoint"},
        "items": ["keycard"],
        "on_enter": None,
    },
    "server_room": {
        "name": "Server Room",
        "description": (
            "Rows of dead server racks fill the room. The air is cold and still. "
            "A breaker panel on the far wall is missing a fuse. An elevator door "
            "on the north wall is dark — no power."
        ),
        "exits": {"south": "checkpoint"},
        "items": ["battery"],
        "on_enter": None,
        "locked_exits": {"north": {"requires": "_power_on", "target": "elevator"}},
    },
    "elevator": {
        "name": "Elevator",
        "description": (
            "The elevator hums to life as you step inside. A single button reads "
            "'SURFACE'. You press it. The doors close, and you begin to rise."
        ),
        "exits": {},
        "items": [],
        "on_enter": "win",
    },
}

# ---------------------------------------------------------------------------
# Puzzle logic
# ---------------------------------------------------------------------------


def check_puzzle(
    state_flags: dict[str, bool],
    inventory: list[str],
    current_room: str,
    action: str,
    target: str,
) -> str | None:
    """Check if a use-item action triggers a puzzle resolution.

    Returns a message string if the puzzle fires, or None if nothing happens.
    """
    # Use keycard at checkpoint -> unlock north door
    if current_room == "checkpoint" and action == "use" and target == "keycard":
        if "keycard" not in inventory:
            return None
        state_flags["checkpoint_unlocked"] = True
        return (
            "You swipe the keycard. The reader blinks green and the reinforced "
            "door clicks open, revealing the server room beyond."
        )

    # Use fuse in server room -> restore power
    if current_room == "server_room" and action == "use" and target == "fuse":
        if "fuse" not in inventory:
            return None
        state_flags["power_on"] = True
        # Also need the wrench to tighten it
        if "wrench" not in inventory:
            return (
                "You slot the fuse into the breaker panel, but it's loose. "
                "You need something to secure it."
            )
        state_flags["_power_on"] = True
        return (
            "You slot the fuse into the breaker panel and tighten it with the "
            "wrench. The lights flicker on and the elevator door glows to life!"
        )

    # Use wrench in server room after fuse is placed
    if current_room == "server_room" and action == "use" and target == "wrench":
        if "wrench" not in inventory:
            return None
        if state_flags.get("power_on") and not state_flags.get("_power_on"):
            state_flags["_power_on"] = True
            return (
                "You tighten the fuse with the wrench. The breaker panel hums "
                "and the elevator door lights up!"
            )
        if not state_flags.get("power_on"):
            return "You wave the wrench around but there's nothing to tighten here yet."

    return None


def can_exit(room_id: str, direction: str, state_flags: dict[str, bool]) -> tuple[bool, str | None]:
    """Check whether an exit is passable.

    Returns (allowed, message). If not allowed, message explains why.
    """
    room = ROOMS[room_id]
    locked = room.get("locked_exits", {})
    if direction in locked:
        req = locked[direction]["requires"]
        if req.startswith("_"):
            # Flag-based lock
            if not state_flags.get(req):
                return False, "The way is blocked. Something needs to be activated first."
        else:
            # Item / flag hybrid — check flag named after the room
            flag_name = f"{room_id}_unlocked"
            if not state_flags.get(flag_name):
                return False, "The door is locked. You need to find a way to open it."
        return True, None
    return True, None


def get_exit_target(room_id: str, direction: str) -> str | None:
    """Return the target room for a direction, checking locked exits too."""
    room = ROOMS[room_id]
    if direction in room["exits"]:
        return room["exits"][direction]
    locked = room.get("locked_exits", {})
    if direction in locked:
        return locked[direction]["target"]
    return None
