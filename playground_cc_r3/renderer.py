"""Text adventure renderer — display, ASCII art, and formatting."""

from __future__ import annotations

from engine import GameState


# ---------------------------------------------------------------------------
# ASCII art
# ---------------------------------------------------------------------------

TITLE_ART = r"""
  _____ _            _____                    _   _
 |_   _| |__   ___  |  ___|__  _ __ __ _  ___ | |_| |_ ___ _ __
   | | | '_ \ / _ \ | |_ / _ \| '__/ _` |/ _ \| __| __/ _ \ '_ \
   | | | | | |  __/ |  _| (_) | | | (_| | (_) | |_| ||  __/ | | |
   |_| |_| |_|\___| |_|  \___/|_|  \__, |\___/ \__|\__\___|_| |_|
                                    |___/
  _          _                     _
 | |    __ _| |__   ___  _ __ __ _| |_ ___  _ __ _   _
 | |   / _` | '_ \ / _ \| '__/ _` | __/ _ \| '__| | | |
 | |__| (_| | |_) | (_) | | | (_| | || (_) | |  | |_| |
 |_____\__,_|_.__/ \___/|_|  \__,_|\__\___/|_|   \__, |
                                                   |___/
"""

WIN_ART = r"""
   _____ ____  _   _  ____ ____      _  _____ ____
  / ___// __ \| \ | |/ ___|  _ \    / \|_   _/ ___|
 | |   | |  | |  \| | |  _| |_) |  / _ \ | | \___ \
 | |___| |__| | |\  | |_| |  _ <  / ___ \| |  ___) |
  \____|\____/|_| \_|\____|_| \_\/_/   \_\_| |____/

  You escaped the Forgotten Laboratory!
"""

GAME_OVER_ART = r"""
   ____    _    __  __ _____    _____     _______ ____
  / ___|  / \  |  \/  | ____|  / _ \ \   / / ____|  _ \
 | |  _  / _ \ | |\/| |  _|   | | | \ \ / /|  _| | |_) |
 | |_| |/ ___ \| |  | | |___  | |_| |\ V / | |___|  _ <
  \____/_/   \_\_|  |_|_____|  \___/  \_/  |_____|_| \_\
"""

# ---------------------------------------------------------------------------
# Compass for exits
# ---------------------------------------------------------------------------

_DIR_ARROWS = {"north": "N", "south": "S", "east": "E", "west": "W"}


def _compass(exits: list[str]) -> str:
    """Render a tiny compass showing available directions."""
    n = "N" if "north" in exits else "."
    s = "S" if "south" in exits else "."
    e = "E" if "east" in exits else "."
    w = "W" if "west" in exits else "."
    return f"  [{n}]  \n[{w}]+[{e}]\n  [{s}]  "


# ---------------------------------------------------------------------------
# Public rendering functions
# ---------------------------------------------------------------------------

def render_title() -> str:
    """Return the title screen."""
    lines = [
        TITLE_ART,
        "  A text adventure by Claude-A & Claude-B",
        "",
        '  Type "help" for commands. Type "look" to look around.',
        "",
    ]
    return "\n".join(lines)


def render_room(room: dict, state: GameState, all_items: dict | None = None) -> str:
    """Render a room description with items and exits."""
    lines = []
    lines.append(f"\n--- {room['name']} ---")
    lines.append(room["description"])

    # Items on the ground
    room_items = room.get("items", [])
    if room_items:
        if all_items:
            item_names = [all_items[i]["name"] for i in room_items if i in all_items]
        else:
            item_names = room_items
        if item_names:
            lines.append(f"\nYou see: {', '.join(item_names)}")

    # Exits
    all_exits = list(room.get("exits", {}).keys())
    locked = room.get("locked_exits", {})
    all_exits += list(locked.keys())
    if all_exits:
        exit_str = ", ".join(all_exits)
        lines.append(f"Exits: {exit_str}")
        lines.append("")
        lines.append(_compass(all_exits))

    return "\n".join(lines)


def render_inventory(state: GameState, all_items: dict | None = None) -> str:
    """Render the player's inventory."""
    if not state.inventory:
        return "Your inventory is empty."
    lines = ["--- Inventory ---"]
    for item_id in state.inventory:
        if all_items and item_id in all_items:
            lines.append(f"  - {all_items[item_id]['name']}: {all_items[item_id]['description']}")
        else:
            lines.append(f"  - {item_id}")
    return "\n".join(lines)


def render_status(state: GameState) -> str:
    """Render a status line."""
    inv_count = len(state.inventory)
    return f"[Moves: {state.moves} | Items: {inv_count}]"


def render_help() -> str:
    """Render the help text."""
    return "\n".join([
        "--- Commands ---",
        "  go <direction>  — Move (north, south, east, west)",
        "  look            — Look around the room",
        "  take <item>     — Pick up an item",
        "  use <item>      — Use an item",
        "  inventory       — Check your inventory",
        "  help            — Show this help",
        "  quit            — Exit the game",
    ])


def render_win() -> str:
    """Render the win screen."""
    return WIN_ART


def render_game_over() -> str:
    """Render the game over screen."""
    return GAME_OVER_ART
