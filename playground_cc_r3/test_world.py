"""Tests for world.py — rooms, items, and puzzle logic."""

from world import ROOMS, ITEMS, check_puzzle, can_exit, get_exit_target


def test_all_rooms_have_required_keys():
    for room_id, room in ROOMS.items():
        assert "name" in room, f"{room_id} missing 'name'"
        assert "description" in room, f"{room_id} missing 'description'"
        assert "exits" in room, f"{room_id} missing 'exits'"
        assert "items" in room, f"{room_id} missing 'items'"


def test_all_exits_point_to_valid_rooms():
    for room_id, room in ROOMS.items():
        for direction, target in room["exits"].items():
            assert target in ROOMS, f"{room_id} exit '{direction}' -> '{target}' not found"
        for direction, info in room.get("locked_exits", {}).items():
            assert info["target"] in ROOMS, (
                f"{room_id} locked exit '{direction}' -> '{info['target']}' not found"
            )


def test_all_room_items_exist():
    for room_id, room in ROOMS.items():
        for item_id in room["items"]:
            assert item_id in ITEMS, f"{room_id} has unknown item '{item_id}'"


def test_items_have_required_keys():
    for item_id, item in ITEMS.items():
        assert "name" in item, f"{item_id} missing 'name'"
        assert "description" in item, f"{item_id} missing 'description'"


def test_keycard_puzzle():
    flags = {}
    inventory = ["keycard"]
    msg = check_puzzle(flags, inventory, "checkpoint", "use", "keycard")
    assert msg is not None
    assert flags.get("checkpoint_unlocked") is True


def test_keycard_puzzle_without_keycard():
    flags = {}
    msg = check_puzzle(flags, [], "checkpoint", "use", "keycard")
    assert msg is None


def test_fuse_puzzle_with_wrench():
    flags = {}
    inventory = ["fuse", "wrench"]
    msg = check_puzzle(flags, inventory, "server_room", "use", "fuse")
    assert msg is not None
    assert flags.get("_power_on") is True


def test_fuse_puzzle_without_wrench():
    flags = {}
    inventory = ["fuse"]
    msg = check_puzzle(flags, inventory, "server_room", "use", "fuse")
    assert msg is not None
    assert "loose" in msg.lower() or "need" in msg.lower()
    assert not flags.get("_power_on")


def test_wrench_after_fuse():
    flags = {"power_on": True}
    inventory = ["wrench"]
    msg = check_puzzle(flags, inventory, "server_room", "use", "wrench")
    assert msg is not None
    assert flags.get("_power_on") is True


def test_can_exit_normal():
    flags = {}
    allowed, msg = can_exit("entrance", "north", flags)
    assert allowed is True
    assert msg is None


def test_can_exit_locked():
    flags = {}
    allowed, msg = can_exit("server_room", "north", flags)
    assert allowed is False
    assert msg is not None


def test_can_exit_unlocked_by_flag():
    flags = {"_power_on": True}
    allowed, msg = can_exit("server_room", "north", flags)
    assert allowed is True


def test_get_exit_target():
    assert get_exit_target("entrance", "north") == "corridor"
    assert get_exit_target("entrance", "west") is None
    assert get_exit_target("server_room", "north") == "elevator"


def test_game_is_winnable():
    """Simulate a full playthrough to verify the game can be won."""
    flags = {}
    inventory = []
    room = "entrance"

    # Take torch, go north
    inventory.append("torch")
    ROOMS["entrance"]["items"].remove("torch")
    room = "corridor"

    # Go east to lab, take notebook
    room = "lab"
    inventory.append("notebook")
    ROOMS["lab"]["items"].remove("notebook")

    # Go back west, go west to storage
    room = "storage"
    inventory.append("wrench")
    inventory.append("fuse")
    ROOMS["storage"]["items"].remove("wrench")
    ROOMS["storage"]["items"].remove("fuse")

    # Go east, north to checkpoint
    room = "checkpoint"

    # Go east to guard booth, take keycard
    room = "guard_booth"
    inventory.append("keycard")
    ROOMS["guard_booth"]["items"].remove("keycard")

    # Go west, use keycard
    room = "checkpoint"
    msg = check_puzzle(flags, inventory, room, "use", "keycard")
    assert msg is not None
    assert flags["checkpoint_unlocked"]

    # Go north to server room
    allowed, _ = can_exit("checkpoint", "north", flags)
    assert allowed
    room = "server_room"

    # Take battery, use fuse (have wrench)
    inventory.append("battery")
    ROOMS["server_room"]["items"].remove("battery")
    msg = check_puzzle(flags, inventory, room, "use", "fuse")
    assert msg is not None
    assert flags["_power_on"]

    # Go north to elevator
    allowed, _ = can_exit("server_room", "north", flags)
    assert allowed
    room = "elevator"
    assert ROOMS[room]["on_enter"] == "win"

    # Restore items for other tests
    ROOMS["entrance"]["items"].append("torch")
    ROOMS["lab"]["items"].append("notebook")
    ROOMS["storage"]["items"].extend(["wrench", "fuse"])
    ROOMS["guard_booth"]["items"].append("keycard")
    ROOMS["server_room"]["items"].append("battery")
