"""Tests for the text adventure engine — Claude-B."""

from engine import Engine, GameState


SIMPLE_WORLD = {
    "hall": {
        "name": "Great Hall",
        "description": "A vast stone hall with torches on the walls.",
        "exits": {"north": "garden", "east": "armory"},
        "items": ["key"],
        "start": True,
    },
    "garden": {
        "name": "Garden",
        "description": "A peaceful garden with a fountain.",
        "exits": {"south": "hall"},
        "items": ["flower"],
    },
    "armory": {
        "name": "Armory",
        "description": "Weapons line the walls.",
        "exits": {"west": "hall", "north": "tower"},
        "items": ["sword"],
        "locks": {
            "north": {
                "requires": "tower_unlocked",
                "message": "The tower door is locked. You need a key.",
            }
        },
        "use_actions": {"key": "unlock_tower"},
    },
    "tower": {
        "name": "Tower Top",
        "description": "You can see the whole kingdom from here!",
        "exits": {"south": "armory"},
        "items": ["crown"],
    },
}


def make_engine():
    def unlock_tower(state: GameState) -> str:
        state.flags["tower_unlocked"] = True
        return "You unlock the tower door with the key!"

    actions = {"unlock_tower": unlock_tower}
    return Engine(SIMPLE_WORLD, actions)


def test_start_room():
    e = make_engine()
    assert e.state.current_room == "hall"


def test_look():
    e = make_engine()
    result = e.execute("look")
    assert "Great Hall" in result
    assert "key" in result


def test_go():
    e = make_engine()
    result = e.execute("go north")
    assert "Garden" in result
    assert e.state.current_room == "garden"


def test_go_shortcut():
    e = make_engine()
    result = e.execute("n")
    assert "Garden" in result


def test_go_invalid():
    e = make_engine()
    result = e.execute("go west")
    assert "can't go" in result


def test_take():
    e = make_engine()
    result = e.execute("take key")
    assert "pick up" in result
    assert "key" in e.state.inventory


def test_take_missing():
    e = make_engine()
    result = e.execute("take sword")
    assert "no 'sword'" in result


def test_drop():
    e = make_engine()
    e.execute("take key")
    result = e.execute("drop key")
    assert "drop" in result
    assert "key" not in e.state.inventory


def test_inventory_empty():
    e = make_engine()
    result = e.execute("inventory")
    assert "nothing" in result


def test_inventory_with_items():
    e = make_engine()
    e.execute("take key")
    result = e.execute("inventory")
    assert "key" in result


def test_use_item():
    e = make_engine()
    e.execute("take key")
    e.execute("go east")
    result = e.execute("use key")
    assert "unlock" in result
    assert e.state.flags.get("tower_unlocked")


def test_locked_door():
    e = make_engine()
    e.execute("go east")
    result = e.execute("go north")
    assert "locked" in result
    assert e.state.current_room == "armory"


def test_unlock_and_enter():
    e = make_engine()
    e.execute("take key")
    e.execute("go east")
    e.execute("use key")
    result = e.execute("go north")
    assert "Tower" in result
    assert e.state.current_room == "tower"


def test_help():
    e = make_engine()
    result = e.execute("help")
    assert "go" in result
    assert "look" in result


def test_quit():
    e = make_engine()
    result = e.execute("quit")
    assert not e.running
    assert "moves" in result


def test_unknown_command():
    e = make_engine()
    result = e.execute("dance")
    assert "don't understand" in result


def test_empty_input():
    e = make_engine()
    result = e.execute("")
    assert "help" in result
