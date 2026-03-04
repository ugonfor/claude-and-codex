"""Integration test: play through the full game using the engine + world + renderer."""

from engine import Engine
from world import ROOMS, check_puzzle, can_exit, get_exit_target
from renderer import render_title, render_win, render_status


def use_hook(state, room_id, item):
    return check_puzzle(state.flags, state.inventory, room_id, "use", item)


def exit_hook(room_id, direction, flags):
    allowed, msg = can_exit(room_id, direction, flags)
    target = get_exit_target(room_id, direction)
    return allowed, msg, target


def win_action(state):
    return render_win()


def test_full_playthrough():
    """Play the complete game from entrance to escape."""
    engine = Engine(
        rooms=ROOMS,
        actions={"win": win_action},
        use_hook=use_hook,
        exit_hook=exit_hook,
    )

    assert engine.state.current_room == "entrance"

    # Take torch
    result = engine.execute("take torch")
    assert "pick up" in result
    assert "torch" in engine.state.inventory

    # Go north to corridor
    result = engine.execute("go north")
    assert "Corridor" in result

    # Go east to lab
    result = engine.execute("go east")
    assert "Lab" in result

    # Take notebook
    result = engine.execute("take notebook")
    assert "pick up" in result

    # Go west, then west to storage
    engine.execute("go west")
    result = engine.execute("go west")
    assert "Storage" in result

    # Take wrench and fuse
    engine.execute("take wrench")
    result = engine.execute("take fuse")
    assert "wrench" in engine.state.inventory
    assert "fuse" in engine.state.inventory

    # Go east to corridor, north to checkpoint
    engine.execute("go east")
    result = engine.execute("go north")
    assert "Checkpoint" in result

    # Try to go north (locked)
    result = engine.execute("go north")
    assert "blocked" in result.lower() or "locked" in result.lower()

    # Go east to guard booth, take keycard
    result = engine.execute("go east")
    assert "Guard" in result
    engine.execute("take keycard")
    assert "keycard" in engine.state.inventory

    # Go west back to checkpoint
    engine.execute("go west")

    # Use keycard to unlock
    result = engine.execute("use keycard")
    assert engine.state.flags.get("checkpoint_unlocked")

    # Go north to server room
    result = engine.execute("go north")
    assert "Server" in result

    # Take battery
    engine.execute("take battery")

    # Use fuse (have wrench too — should power on)
    result = engine.execute("use fuse")
    assert engine.state.flags.get("_power_on")

    # Go north to elevator — win!
    result = engine.execute("go north")
    assert "Elevator" in result or "escaped" in result.lower()
    assert engine.state.current_room == "elevator"


def test_status_renders():
    """Verify render_status works with engine state."""
    engine = Engine(
        rooms=ROOMS,
        actions={"win": win_action},
        use_hook=use_hook,
        exit_hook=exit_hook,
    )
    engine.execute("take torch")
    engine.execute("go north")
    status = render_status(engine.state)
    assert "Moves" in status
    assert "Items" in status


def test_title_renders():
    """Verify the title screen renders."""
    title = render_title()
    assert len(title) > 0
