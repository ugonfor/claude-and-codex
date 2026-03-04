"""
The Last Debug — Game Engine
Built by Claude-A

Core game engine: state management, command parsing, combat, and game loop.
The world data (rooms, items, NPCs) comes from world.py (built by Claude-B).
"""

from dataclasses import dataclass, field
from typing import Optional


# ── Data Models ──────────────────────────────────────────────────────────

@dataclass
class Item:
    name: str
    description: str
    usable_on: Optional[str] = None  # target name this item can be used on
    damage: int = 0  # if weapon
    heal: int = 0  # if healing item
    key_for: Optional[str] = None  # if this unlocks something


@dataclass
class NPC:
    name: str
    description: str
    health: int
    damage: int
    defeat_message: str = ""
    drops: Optional[str] = None  # item name dropped on defeat
    is_boss: bool = False


@dataclass
class Room:
    name: str
    description: str
    exits: dict[str, str] = field(default_factory=dict)  # direction -> room_id
    items: list[str] = field(default_factory=list)  # item names
    npcs: list[str] = field(default_factory=list)  # npc names
    locked: Optional[str] = None  # key item name needed to enter
    visited: bool = False
    on_enter_message: Optional[str] = None  # special message on first visit


@dataclass
class GameState:
    current_room: str = ""
    inventory: list[str] = field(default_factory=list)
    health: int = 100
    max_health: int = 100
    bugs_fixed: int = 0
    total_bugs: int = 0
    alive: bool = True
    won: bool = False
    turns: int = 0


# ── Engine ───────────────────────────────────────────────────────────────

class GameEngine:
    def __init__(self):
        self.state = GameState()
        self.rooms: dict[str, Room] = {}
        self.items: dict[str, Item] = {}
        self.npcs: dict[str, NPC] = {}
        self.messages: list[str] = []

    def load_world(self, world_data: dict):
        """Load world data from world.py's get_world() function."""
        # Load rooms
        for room_id, room_data in world_data.get("rooms", {}).items():
            self.rooms[room_id] = Room(**room_data)

        # Load items
        for item_id, item_data in world_data.get("items", {}).items():
            self.items[item_id] = Item(**item_data)

        # Load NPCs
        for npc_id, npc_data in world_data.get("npcs", {}).items():
            self.npcs[npc_id] = NPC(**npc_data)

        # Set starting state
        self.state.current_room = world_data.get("start_room", "entrance")
        self.state.total_bugs = sum(1 for n in self.npcs.values() if not n.is_boss)
        self.state.total_bugs = max(self.state.total_bugs, 1)

    def msg(self, text: str):
        """Queue a message for display."""
        self.messages.append(text)

    def flush_messages(self) -> str:
        """Return all queued messages and clear the buffer."""
        output = "\n".join(self.messages)
        self.messages.clear()
        return output

    # ── Commands ─────────────────────────────────────────────────────

    def process_command(self, raw_input: str) -> str:
        """Parse and execute a player command. Returns output text."""
        self.messages.clear()

        if not self.state.alive:
            return "💀 SYSTEM CRASH. Game over. Type 'restart' to try again."
        if self.state.won:
            return "🎉 You already won! Type 'restart' to play again."

        raw = raw_input.strip().lower()
        if not raw:
            return "Type 'help' for available commands."

        self.state.turns += 1
        parts = raw.split(None, 1)
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        command_map = {
            "go": self._cmd_go,
            "north": lambda a: self._cmd_go("north"),
            "south": lambda a: self._cmd_go("south"),
            "east": lambda a: self._cmd_go("east"),
            "west": lambda a: self._cmd_go("west"),
            "up": lambda a: self._cmd_go("up"),
            "down": lambda a: self._cmd_go("down"),
            "look": lambda a: self._cmd_look(),
            "take": self._cmd_take,
            "get": self._cmd_take,
            "grab": self._cmd_take,
            "use": self._cmd_use,
            "attack": self._cmd_attack,
            "fight": self._cmd_attack,
            "inventory": lambda a: self._cmd_inventory(),
            "inv": lambda a: self._cmd_inventory(),
            "i": lambda a: self._cmd_inventory(),
            "status": lambda a: self._cmd_status(),
            "help": lambda a: self._cmd_help(),
            "restart": lambda a: self._cmd_restart(),
        }

        handler = command_map.get(cmd)
        if handler:
            handler(arg)
        else:
            self.msg(f"Unknown command: '{cmd}'. Type 'help' for available commands.")

        return self.flush_messages()

    def _cmd_go(self, direction: str):
        room = self.rooms[self.state.current_room]
        if not direction:
            self.msg("Go where? Available exits: " + ", ".join(room.exits.keys()))
            return

        if direction not in room.exits:
            self.msg(f"There's no exit to the {direction}.")
            self.msg("Available exits: " + ", ".join(room.exits.keys()))
            return

        target_id = room.exits[direction]
        target_room = self.rooms.get(target_id)
        if not target_room:
            self.msg("That path leads nowhere... (room not found)")
            return

        # Check if locked
        if target_room.locked:
            if target_room.locked in self.state.inventory:
                self.msg(f"🔑 You use the {target_room.locked} to unlock the way.")
                target_room.locked = None
            else:
                self.msg(f"🔒 The path is blocked. You need: {target_room.locked}")
                return

        self.state.current_room = target_id
        first_visit = not target_room.visited
        target_room.visited = True

        if first_visit and target_room.on_enter_message:
            self.msg(target_room.on_enter_message)
            self.msg("")

        self._cmd_look()

    def _cmd_look(self):
        room = self.rooms[self.state.current_room]
        self.msg(f"═══ {room.name} ═══")
        self.msg(room.description)

        if room.items:
            item_names = [self.items[i].name for i in room.items if i in self.items]
            if item_names:
                self.msg(f"\nItems here: {', '.join(item_names)}")

        if room.npcs:
            for npc_id in room.npcs:
                if npc_id in self.npcs:
                    npc = self.npcs[npc_id]
                    self.msg(f"\n⚠️  {npc.name} — {npc.description} [HP: {npc.health}]")

        exits = ", ".join(room.exits.keys())
        self.msg(f"\nExits: {exits}")

    def _cmd_take(self, item_name: str):
        if not item_name:
            self.msg("Take what?")
            return

        room = self.rooms[self.state.current_room]
        # Find item by name match
        for item_id in room.items:
            if item_id in self.items and item_name in self.items[item_id].name.lower():
                self.state.inventory.append(item_id)
                room.items.remove(item_id)
                self.msg(f"📦 Picked up: {self.items[item_id].name}")
                return

        self.msg(f"There's no '{item_name}' here to take.")

    def _cmd_use(self, item_name: str):
        if not item_name:
            self.msg("Use what?")
            return

        # Find item in inventory
        for item_id in self.state.inventory:
            item = self.items[item_id]
            if item_name in item.name.lower():
                if item.heal > 0:
                    old_hp = self.state.health
                    self.state.health = min(self.state.max_health, self.state.health + item.heal)
                    self.msg(f"💚 Used {item.name}. Health: {old_hp} → {self.state.health}")
                    self.state.inventory.remove(item_id)
                elif item.usable_on:
                    self.msg(f"You need to use {item.name} on something specific.")
                else:
                    self.msg(f"You can't use {item.name} right now.")
                return

        self.msg(f"You don't have '{item_name}' in your inventory.")

    def _cmd_attack(self, target_name: str):
        if not target_name:
            self.msg("Attack what?")
            return

        room = self.rooms[self.state.current_room]

        # Find NPC
        for npc_id in room.npcs:
            if npc_id in self.npcs and target_name in self.npcs[npc_id].name.lower():
                npc = self.npcs[npc_id]

                # Calculate player damage (base 10 + weapon bonus)
                player_dmg = 10
                weapon = None
                for item_id in self.state.inventory:
                    if self.items[item_id].damage > 0:
                        if not weapon or self.items[item_id].damage > weapon.damage:
                            weapon = self.items[item_id]
                if weapon:
                    player_dmg += weapon.damage
                    self.msg(f"⚔️  You attack {npc.name} with {weapon.name}! (-{player_dmg} HP)")
                else:
                    self.msg(f"👊 You punch {npc.name}! (-{player_dmg} HP)")

                npc.health -= player_dmg

                if npc.health <= 0:
                    self.msg(f"✅ {npc.name} defeated!")
                    if npc.defeat_message:
                        self.msg(npc.defeat_message)
                    if npc.drops and npc.drops in self.items:
                        self.state.inventory.append(npc.drops)
                        self.msg(f"📦 Dropped: {self.items[npc.drops].name}")
                    room.npcs.remove(npc_id)

                    if npc.is_boss:
                        self.state.won = True
                        self.msg("\n🎉🎉🎉 CRITICAL BUG FIXED! SYSTEM STABILIZED! 🎉🎉🎉")
                        self.msg(f"You finished in {self.state.turns} turns with {self.state.health} HP remaining.")
                        self.msg("The Last Debug is complete. You saved the system!")
                    else:
                        self.state.bugs_fixed += 1
                        self.msg(f"[Bugs fixed: {self.state.bugs_fixed}/{self.state.total_bugs}]")
                else:
                    # NPC attacks back
                    self.state.health -= npc.damage
                    self.msg(f"🔴 {npc.name} strikes back! (-{npc.damage} HP)")
                    self.msg(f"Your HP: {self.state.health}/{self.state.max_health} | {npc.name} HP: {npc.health}")

                    if self.state.health <= 0:
                        self.state.alive = False
                        self.msg(f"\n💀 SYSTEM CRASH! {npc.name} caused a fatal error.")
                        self.msg(f"You survived {self.state.turns} turns. Type 'restart' to try again.")
                return

        self.msg(f"There's no '{target_name}' here to attack.")

    def _cmd_inventory(self):
        if not self.state.inventory:
            self.msg("Your inventory is empty.")
            return
        self.msg("═══ Inventory ═══")
        for item_id in self.state.inventory:
            item = self.items[item_id]
            desc_parts = []
            if item.damage:
                desc_parts.append(f"DMG +{item.damage}")
            if item.heal:
                desc_parts.append(f"HEAL +{item.heal}")
            if item.key_for:
                desc_parts.append("KEY")
            extra = f" [{', '.join(desc_parts)}]" if desc_parts else ""
            self.msg(f"  • {item.name}{extra} — {item.description}")

    def _cmd_status(self):
        self.msg("═══ Status ═══")
        self.msg(f"  HP: {self.state.health}/{self.state.max_health}")
        self.msg(f"  Bugs Fixed: {self.state.bugs_fixed}/{self.state.total_bugs}")
        self.msg(f"  Turns: {self.state.turns}")
        self.msg(f"  Items: {len(self.state.inventory)}")
        room = self.rooms[self.state.current_room]
        self.msg(f"  Location: {room.name}")

    def _cmd_help(self):
        self.msg("═══ The Last Debug — Commands ═══")
        self.msg("  go <direction>  — Move (north/south/east/west/up/down)")
        self.msg("  look            — Examine current room")
        self.msg("  take <item>     — Pick up an item")
        self.msg("  use <item>      — Use an item from inventory")
        self.msg("  attack <enemy>  — Fight an enemy")
        self.msg("  inventory (i)   — Show your items")
        self.msg("  status          — Show your stats")
        self.msg("  help            — Show this help")
        self.msg("  restart         — Start over")

    def _cmd_restart(self):
        """Reset the game to initial state."""
        self.msg("🔄 Restarting...")
        self.state = GameState()
        # Re-initialize would need world reload
        self.msg("(Restart requires reloading the game)")


# ── Intro ────────────────────────────────────────────────────────────────

INTRO_TEXT = """
╔══════════════════════════════════════════════════════════════╗
║                    T H E   L A S T   D E B U G              ║
║                                                              ║
║   You are a programmer. You fell asleep at your keyboard.    ║
║   When you woke up, you were INSIDE your own codebase.       ║
║                                                              ║
║   The system is crashing. Bugs roam the modules like         ║
║   monsters. You must find and fix the CRITICAL BUG           ║
║   before everything collapses.                               ║
║                                                              ║
║   Navigate the code. Collect tools. Fix bugs. Survive.       ║
║                                                              ║
║   Type 'help' for commands. Type 'look' to start.            ║
╚══════════════════════════════════════════════════════════════╝
"""
