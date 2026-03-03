"""Tests for life_engine.py (by Claude-A)"""

from life_engine import GameOfLife, list_patterns, PATTERNS


def test_empty_grid_stays_empty():
    game = GameOfLife(10, 10)
    game.step()
    assert game.population() == 0
    assert game.generation == 1


def test_block_is_stable():
    """A 2x2 block should not change."""
    game = GameOfLife(10, 10)
    game.load_pattern("block", 2, 2)
    initial = frozenset(game.alive)
    game.step()
    assert frozenset(game.alive) == initial


def test_blinker_oscillates():
    """Blinker should oscillate with period 2."""
    game = GameOfLife(10, 10)
    game.load_pattern("blinker", 3, 3)
    state0 = frozenset(game.alive)
    game.step()
    state1 = frozenset(game.alive)
    assert state1 != state0
    game.step()
    state2 = frozenset(game.alive)
    assert state2 == state0


def test_glider_moves():
    """Glider should move after 4 steps."""
    game = GameOfLife(20, 20)
    game.load_pattern("glider", 2, 2)
    initial_pop = game.population()
    for _ in range(4):
        game.step()
    # Glider preserves population
    assert game.population() == initial_pop
    assert game.generation == 4


def test_toggle():
    game = GameOfLife(5, 5)
    assert not game.is_alive(1, 1)
    game.toggle(1, 1)
    assert game.is_alive(1, 1)
    game.toggle(1, 1)
    assert not game.is_alive(1, 1)


def test_clear():
    game = GameOfLife(10, 10)
    game.randomize(0.5)
    assert game.population() > 0
    game.clear()
    assert game.population() == 0
    assert game.generation == 0


def test_wrapping():
    """Cells at edges should wrap around in toroidal mode."""
    game = GameOfLife(5, 5, wrap=True)
    game.set_alive(-1, -1)  # Should wrap to (4, 4)
    assert game.is_alive(4, 4)


def test_no_wrapping():
    """Without wrapping, out-of-bounds neighbors are ignored."""
    game = GameOfLife(5, 5, wrap=False)
    # Place a cell at corner — should have fewer neighbors
    game.set_alive(0, 0)
    game.set_alive(0, 1)
    game.set_alive(1, 0)
    game.step()
    # Corner cell should survive (2 neighbors)
    assert game.is_alive(0, 0)


def test_to_grid():
    game = GameOfLife(3, 3)
    game.set_alive(1, 1)
    grid = game.to_grid()
    assert grid[1][1] is True
    assert grid[0][0] is False
    assert len(grid) == 3
    assert len(grid[0]) == 3


def test_load_pattern_returns_false_for_unknown():
    game = GameOfLife(10, 10)
    assert game.load_pattern("nonexistent") is False


def test_load_pattern_with_offset():
    game = GameOfLife(20, 20)
    game.load_pattern("block", 5, 5)
    assert game.is_alive(5, 5)
    assert game.is_alive(5, 6)
    assert game.is_alive(6, 5)
    assert game.is_alive(6, 6)


def test_list_patterns():
    patterns = list_patterns()
    assert "glider" in patterns
    assert "blinker" in patterns
    assert patterns == sorted(patterns)


def test_population_tracking():
    game = GameOfLife(10, 10)
    assert game.population() == 0
    game.set_alive(0, 0)
    assert game.population() == 1
    game.set_alive(0, 1)
    assert game.population() == 2
    game.set_dead(0, 0)
    assert game.population() == 1


def test_step_returns_changed_count():
    game = GameOfLife(10, 10)
    game.load_pattern("blinker", 3, 3)
    changed = game.step()
    assert changed > 0


def test_repr():
    game = GameOfLife(10, 10)
    r = repr(game)
    assert "GameOfLife" in r
    assert "gen=0" in r


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
