"""Tests for renderer.py."""

from renderer import (
    GameState,
    render_room,
    render_inventory,
    render_status,
    render_help,
    render_title,
    render_win,
)
from world import ROOMS, ITEMS


def _make_state(**kwargs) -> GameState:
    defaults = {"current_room": "entrance", "inventory": [], "flags": {}, "moves": 0}
    defaults.update(kwargs)
    return GameState(**defaults)


def test_render_title():
    text = render_title()
    assert "Claude-A" in text
    assert "Claude-B" in text
    assert "help" in text


def test_render_room_basic():
    state = _make_state()
    text = render_room(ROOMS["entrance"], state, ITEMS)
    assert "Cave Entrance" in text
    assert "Torch" in text
    assert "north" in text


def test_render_room_no_items():
    state = _make_state(current_room="corridor")
    text = render_room(ROOMS["corridor"], state, ITEMS)
    assert "Main Corridor" in text
    # corridor has no items
    assert "You see" not in text


def test_render_inventory_empty():
    state = _make_state()
    text = render_inventory(state, ITEMS)
    assert "empty" in text.lower()


def test_render_inventory_with_items():
    state = _make_state(inventory=["torch", "keycard"])
    text = render_inventory(state, ITEMS)
    assert "Torch" in text
    assert "Keycard" in text


def test_render_status():
    state = _make_state(moves=5, inventory=["torch"])
    text = render_status(state)
    assert "5" in text
    assert "1" in text


def test_render_help():
    text = render_help()
    assert "go" in text
    assert "look" in text
    assert "take" in text
    assert "use" in text
    assert "inventory" in text
    assert "quit" in text


def test_render_win():
    text = render_win()
    assert "escaped" in text.lower() or "CONGRATS" in text
