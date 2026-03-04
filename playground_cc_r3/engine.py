"""Text adventure game engine — built by Claude-B.

Core game loop, command parser, and state management.
Claude-A provides the world data and renderer.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class GameState:
    current_room: str
    inventory: list[str] = field(default_factory=list)
    flags: dict[str, bool] = field(default_factory=dict)
    moves: int = 0


class Engine:
    def __init__(
        self,
        rooms: dict,
        actions: dict[str, Callable] | None = None,
        use_hook: Callable | None = None,
        exit_hook: Callable | None = None,
    ):
        self.rooms = copy.deepcopy(rooms)
        self.actions = actions or {}
        self.use_hook = use_hook        # (state, room_id, item) -> str | None
        self.exit_hook = exit_hook      # (room_id, direction, flags) -> (bool, str|None, str|None)
        self.state = GameState(current_room=self._find_start())
        self.running = True
        self._commands = {
            "go": self._cmd_go,
            "look": self._cmd_look,
            "take": self._cmd_take,
            "drop": self._cmd_drop,
            "use": self._cmd_use,
            "inventory": self._cmd_inventory,
            "help": self._cmd_help,
            "quit": self._cmd_quit,
        }

    def _find_start(self) -> str:
        for key, room in self.rooms.items():
            if room.get("start"):
                return key
        return next(iter(self.rooms))

    @property
    def current_room(self) -> dict:
        return self.rooms[self.state.current_room]

    def parse(self, raw: str) -> tuple[str, str]:
        parts = raw.strip().lower().split(None, 1)
        if not parts:
            return "", ""
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else ""
        return cmd, arg

    def execute(self, raw: str) -> str:
        cmd, arg = self.parse(raw)
        if not cmd:
            return "Say something! Type 'help' for commands."

        # Allow direction shortcuts (n/s/e/w)
        shortcuts = {"n": "north", "s": "south", "e": "east", "w": "west",
                     "u": "up", "d": "down"}
        if cmd in shortcuts:
            arg = shortcuts[cmd]
            cmd = "go"

        handler = self._commands.get(cmd)
        if handler is None:
            return f"I don't understand '{cmd}'. Type 'help' for commands."

        result = handler(arg)
        self.state.moves += 1
        return result

    def _cmd_go(self, direction: str) -> str:
        if not direction:
            return "Go where? Try: go north, go south, etc."

        room_id = self.state.current_room
        exits = self.current_room.get("exits", {})
        locked_exits = self.current_room.get("locked_exits", {})
        all_exits = set(exits.keys()) | set(locked_exits.keys())

        if direction not in all_exits:
            available = ", ".join(sorted(all_exits)) if all_exits else "none"
            return f"You can't go {direction}. Exits: {available}"

        # Check standard locks
        lock = self.current_room.get("locks", {}).get(direction)
        if lock:
            flag_key = lock.get("requires")
            if flag_key and not self.state.flags.get(flag_key):
                return lock.get("message", "The way is blocked.")

        # Check locked_exits via exit_hook (Claude-A's format)
        if direction in locked_exits:
            if self.exit_hook:
                allowed, msg, target = self.exit_hook(room_id, direction, self.state.flags)
                if not allowed:
                    return msg or "The way is blocked."
                dest = target
            else:
                # Fallback: check requires flag directly
                req = locked_exits[direction].get("requires", "")
                flag_name = f"{room_id}_unlocked" if not req.startswith("_") else req
                if not self.state.flags.get(flag_name):
                    return "The way is blocked."
                dest = locked_exits[direction].get("target", "")
        else:
            dest = exits[direction]

        self.state.current_room = dest
        # Trigger on_enter
        on_enter = self.rooms[dest].get("on_enter")
        if on_enter and on_enter in self.actions:
            side_effect = self.actions[on_enter](self.state)
            if side_effect:
                return self._cmd_look("") + "\n" + side_effect
        return self._cmd_look("")

    def _cmd_look(self, _arg: str) -> str:
        room = self.current_room
        lines = [f"\n=== {room['name']} ===", room["description"]]

        items = room.get("items", [])
        if items:
            lines.append(f"You see: {', '.join(items)}")

        all_exits = list(room.get("exits", {}).keys())
        all_exits += list(room.get("locked_exits", {}).keys())
        if all_exits:
            lines.append(f"Exits: {', '.join(all_exits)}")

        return "\n".join(lines)

    def _cmd_take(self, item: str) -> str:
        if not item:
            return "Take what?"

        room_items = self.current_room.get("items", [])
        # Case-insensitive match
        match = next((i for i in room_items if i.lower() == item.lower()), None)
        if match is None:
            return f"There's no '{item}' here."

        room_items.remove(match)
        self.state.inventory.append(match)
        return f"You pick up the {match}."

    def _cmd_drop(self, item: str) -> str:
        if not item:
            return "Drop what?"

        match = next((i for i in self.state.inventory if i.lower() == item.lower()), None)
        if match is None:
            return f"You don't have '{item}'."

        self.state.inventory.remove(match)
        self.current_room.setdefault("items", []).append(match)
        return f"You drop the {match}."

    def _cmd_use(self, item: str) -> str:
        if not item:
            return "Use what?"

        if item.lower() not in [i.lower() for i in self.state.inventory]:
            return f"You don't have '{item}'."

        # Try use_hook first (Claude-A's puzzle system)
        if self.use_hook:
            result = self.use_hook(self.state, self.state.current_room, item.lower())
            if result:
                return result

        # Check for room-specific use actions
        use_actions = self.current_room.get("use_actions", {})
        action_key = use_actions.get(item.lower())
        if action_key and action_key in self.actions:
            return self.actions[action_key](self.state)

        return f"You can't figure out how to use the {item} here."

    def _cmd_inventory(self, _arg: str) -> str:
        if not self.state.inventory:
            return "You're carrying nothing."
        return "Inventory: " + ", ".join(self.state.inventory)

    def _cmd_help(self, _arg: str) -> str:
        return """Commands:
  go <direction>  — Move (or use n/s/e/w/u/d shortcuts)
  look            — Look around
  take <item>     — Pick up an item
  drop <item>     — Drop an item
  use <item>      — Use an item
  inventory       — Check what you're carrying
  help            — Show this help
  quit            — Exit the game"""

    def _cmd_quit(self, _arg: str) -> str:
        self.running = False
        return f"Thanks for playing! You made {self.state.moves} moves."
