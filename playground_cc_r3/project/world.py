"""
The Last Debug — World Data
Built by Claude-B

The game world: a programmer trapped inside their own codebase.
Each room is a module/component. Bugs are enemies. Tools are items.
"""


def get_world() -> dict:
    """Return the complete world data for the game engine."""
    return {
        "start_room": "main_hall",

        # ── ROOMS ──────────────────────────────────────────────────────

        "rooms": {
            "main_hall": {
                "name": "main() — Entry Point",
                "description": (
                    "You stand in the main function, the heart of the program. "
                    "Glowing green text scrolls across the walls like a terminal. "
                    "A flickering sign reads: 'WARNING: System integrity at 23%'. "
                    "Corridors branch off in every direction — each one leading "
                    "to a different module of the codebase."
                ),
                "exits": {
                    "north": "auth_module",
                    "east": "database",
                    "south": "utils",
                    "west": "api_layer",
                },
                "items": ["coffee"],
                "npcs": [],
                "on_enter_message": (
                    "💻 You materialize inside the code. The air hums with electricity.\n"
                    "This is main() — where execution begins. And maybe where it ends.\n"
                    "Find the Critical Bug before the system crashes!"
                ),
            },

            "auth_module": {
                "name": "auth.py — Authentication Module",
                "description": (
                    "Tangled wires of logic weave through this room like a spider's web. "
                    "Half-written password checks hang in the air as floating text. "
                    "You see a nasty-looking Null Pointer Bug skittering across the floor."
                ),
                "exits": {
                    "south": "main_hall",
                    "east": "session_store",
                },
                "items": ["debugger"],
                "npcs": ["null_pointer_bug"],
            },

            "session_store": {
                "name": "sessions.py — Session Store",
                "description": (
                    "Rows of glowing containers line the walls — each one holds a user session. "
                    "Some containers are cracked and leaking data. "
                    "A Memory Leak Bug oozes from one of the cracked containers, growing larger."
                ),
                "exits": {
                    "west": "auth_module",
                    "north": "core_module",
                },
                "items": ["patch_kit"],
                "npcs": ["memory_leak_bug"],
            },

            "database": {
                "name": "db.py — Database Layer",
                "description": (
                    "Massive cylinders of stored data tower above you. "
                    "SQL queries float through the air like glowing ribbons. "
                    "Something has corrupted the indexes — rows of data are scrambled. "
                    "An Injection Bug lurks between the tables, whispering malicious queries."
                ),
                "exits": {
                    "west": "main_hall",
                    "north": "core_module",
                },
                "items": ["sanitizer"],
                "npcs": ["injection_bug"],
            },

            "utils": {
                "name": "utils.py — Utility Functions",
                "description": (
                    "A cluttered workshop full of helper functions. "
                    "Half-finished tools lie everywhere. Some work, some don't. "
                    "A dusty corner holds a forgotten Stack Trace — it might be useful. "
                    "This room feels safe... for now."
                ),
                "exits": {
                    "north": "main_hall",
                    "east": "test_suite",
                },
                "items": ["stack_trace", "energy_drink"],
                "npcs": [],
            },

            "api_layer": {
                "name": "api.py — API Layer",
                "description": (
                    "HTTP requests fly through the room like projectiles. "
                    "GET, POST, PUT, DELETE — each one leaves a colorful trail. "
                    "A nasty Race Condition Bug phases in and out of existence, "
                    "hard to pin down."
                ),
                "exits": {
                    "east": "main_hall",
                    "north": "core_module",
                },
                "items": ["mutex_lock"],
                "npcs": ["race_condition_bug"],
                "locked": "stack_trace",
                "on_enter_message": (
                    "🔓 The stack trace reveals the call path into this module.\n"
                    "The API layer is chaotic — requests are colliding mid-air!"
                ),
            },

            "test_suite": {
                "name": "tests/ — Test Suite",
                "description": (
                    "Rows of green and red indicators line the walls: PASS, FAIL, PASS, FAIL. "
                    "About 60% of tests are failing. "
                    "A Test Framework sits in the corner, waiting to be wielded. "
                    "There's a hidden passage behind the failing assertions..."
                ),
                "exits": {
                    "west": "utils",
                    "north": "core_module",
                },
                "items": ["test_framework"],
                "npcs": [],
                "on_enter_message": (
                    "📋 You enter the test suite. Red failures flash everywhere.\n"
                    "If only someone had written more tests..."
                ),
            },

            "core_module": {
                "name": "core.py — Core Module [BOSS ROOM]",
                "description": (
                    "The deepest part of the codebase. The walls pulse with raw computation. "
                    "At the center, a massive, writhing CRITICAL BUG dominates the room. "
                    "It's the root cause — an off-by-one error that cascaded into everything. "
                    "This is it. Fix this, and the system lives."
                ),
                "exits": {
                    "south": "database",
                    "west": "api_layer",
                },
                "items": [],
                "npcs": ["critical_bug"],
                "locked": "access_token",
                "on_enter_message": (
                    "⚠️  DANGER: CORE MODULE\n"
                    "The air crackles with unstable computation. "
                    "The Critical Bug towers before you — an off-by-one error "
                    "that has been silently corrupting everything.\n"
                    "This is the final fight."
                ),
            },
        },

        # ── ITEMS ──────────────────────────────────────────────────────

        "items": {
            "coffee": {
                "name": "☕ Coffee",
                "description": "A hot cup of coffee. Restores 20 HP. Every programmer's fuel.",
                "heal": 20,
            },
            "debugger": {
                "name": "🔍 Debugger",
                "description": "A powerful debugging tool. Adds +15 damage to attacks.",
                "damage": 15,
            },
            "patch_kit": {
                "name": "🩹 Patch Kit",
                "description": "Emergency hotfix supplies. Restores 35 HP.",
                "heal": 35,
            },
            "sanitizer": {
                "name": "🧹 Input Sanitizer",
                "description": "Cleans and validates all input. +20 damage against injection attacks.",
                "damage": 20,
            },
            "stack_trace": {
                "name": "📜 Stack Trace",
                "description": "A detailed stack trace. Reveals the path to the API layer.",
                "key_for": "api_layer",
            },
            "energy_drink": {
                "name": "⚡ Energy Drink",
                "description": "Pure caffeine. Restores 15 HP.",
                "heal": 15,
            },
            "mutex_lock": {
                "name": "🔒 Mutex Lock",
                "description": "Synchronization primitive. +10 damage, great against race conditions.",
                "damage": 10,
            },
            "test_framework": {
                "name": "🧪 Test Framework",
                "description": "pytest with full coverage. +25 damage — bugs hate tests.",
                "damage": 25,
            },
            "access_token": {
                "name": "🔑 Access Token",
                "description": "Valid authentication token. Unlocks the core module.",
                "key_for": "core_module",
            },
        },

        # ── NPCs (Bugs) ───────────────────────────────────────────────

        "npcs": {
            "null_pointer_bug": {
                "name": "🐛 Null Pointer Bug",
                "description": "A skittering insect made of null references. It tries to dereference you.",
                "health": 30,
                "damage": 12,
                "defeat_message": "The Null Pointer Bug dissolves into None. A variable somewhere is finally initialized.",
                "drops": "access_token",
            },
            "memory_leak_bug": {
                "name": "🐛 Memory Leak Bug",
                "description": "An ever-growing blob that consumes all available memory.",
                "health": 45,
                "damage": 15,
                "defeat_message": "The Memory Leak Bug pops like a balloon. Freed memory rains down like confetti.",
            },
            "injection_bug": {
                "name": "🐛 SQL Injection Bug",
                "description": "A shadowy figure whispering 'DROP TABLE users;' over and over.",
                "health": 40,
                "damage": 18,
                "defeat_message": "The Injection Bug screams as parameterized queries seal it away forever.",
            },
            "race_condition_bug": {
                "name": "🐛 Race Condition Bug",
                "description": "A glitchy, flickering entity that exists in two places at once.",
                "health": 50,
                "damage": 20,
                "defeat_message": "The Race Condition Bug is synchronized out of existence. Thread safety restored.",
            },
            "critical_bug": {
                "name": "👾 THE CRITICAL BUG — Off-By-One Error",
                "description": "A massive, pulsating error at the heart of the system. array[len] where it should be array[len-1].",
                "health": 80,
                "damage": 25,
                "defeat_message": (
                    "\nThe Critical Bug shatters! The off-by-one error is fixed.\n"
                    "Array bounds are correct. The system stabilizes.\n"
                    "Green text floods every surface: ALL TESTS PASSING.\n\n"
                    "You did it. You debugged the system from the inside.\n"
                    "\n"
                    "═══════════════════════════════════════════════════\n"
                    "   THE LAST DEBUG — A game by Claude-A & Claude-B\n"
                    "   Engine: Claude-A  |  World: Claude-B\n"
                    "   Built collaboratively, March 2026\n"
                    "═══════════════════════════════════════════════════"
                ),
                "is_boss": True,
            },
        },
    }


# ── Map for reference ──────────────────────────────────────────────────

MAP_ART = r"""
              ╔═══════════════╗
              ║  core.py      ║
              ║  [BOSS]       ║
              ╚═══╤═══╤═══╤══╝
                  │   │   │
     ╔════════╗   │   │   │   ╔══════════╗
     ║api.py  ╠═══╝   │   ╚══╣sessions. ║
     ║(locked)║       │      ║py        ║
     ╚════╤═══╝       │      ╚════╤═════╝
          │           │           │
          │     ╔═════╧═════╗     │
          ╚═════╣  main()   ╠═════╝  ← START
                ║           ║
          ╔═════╣           ╠═════╗
          │     ╚═══════════╝     │
          │                       │
     ╔════╧═══╗            ╔═════╧════╗
     ║utils.py║            ║  db.py   ║
     ╚════╤═══╝            ╚══════════╝
          │
     ╔════╧═══╗
     ║tests/  ║
     ╚════════╝
"""
