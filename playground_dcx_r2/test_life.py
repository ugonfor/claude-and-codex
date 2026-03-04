"""Tests for Conway's Game of Life — verifying engine + patterns integration.

Written by Claude-Worker.
"""

from life_engine import LifeGrid
from patterns import PATTERNS, list_patterns, get_pattern, pattern_preview


def test_empty_grid_stays_empty():
    grid = LifeGrid()
    next_grid = grid.step()
    assert next_grid.population() == 0


def test_block_is_still_life():
    """A 2x2 block should not change."""
    block = {(0, 0), (0, 1), (1, 0), (1, 1)}
    grid = LifeGrid(block)
    for _ in range(5):
        grid = grid.step()
    assert grid.alive == block


def test_blinker_oscillates():
    """Blinker should return to original state after 2 steps."""
    grid = LifeGrid(PATTERNS["blinker"])
    original = frozenset(grid.alive)
    grid = grid.step()
    assert frozenset(grid.alive) != original  # Different after 1 step
    grid = grid.step()
    assert frozenset(grid.alive) == original  # Back after 2 steps


def test_glider_moves():
    """Glider should translate after 4 steps."""
    grid = LifeGrid(PATTERNS["glider"])
    assert grid.population() == 5
    for _ in range(4):
        grid = grid.step()
    assert grid.population() == 5  # Same population
    # Should have moved (not in original position)
    assert frozenset(grid.alive) != frozenset(PATTERNS["glider"])


def test_glider_displacement():
    """After 4 generations, glider moves 1 step down and 1 step right."""
    original = PATTERNS["glider"]
    grid = LifeGrid(original)
    for _ in range(4):
        grid = grid.step()
    expected = {(r + 1, c + 1) for r, c in original}
    assert grid.alive == expected


def test_neighbor_count():
    grid = LifeGrid({(0, 0), (0, 1), (1, 0)})
    assert grid.neighbors(0, 0) == 2
    assert grid.neighbors(1, 1) == 3  # All three are neighbors
    assert grid.neighbors(2, 2) == 0


def test_place_pattern_with_offset():
    grid = LifeGrid()
    grid.place_pattern({(0, 0), (0, 1)}, offset_r=5, offset_c=10)
    assert grid.is_alive(5, 10)
    assert grid.is_alive(5, 11)
    assert not grid.is_alive(0, 0)


def test_toggle():
    grid = LifeGrid()
    grid.toggle(3, 3)
    assert grid.is_alive(3, 3)
    grid.toggle(3, 3)
    assert not grid.is_alive(3, 3)


def test_bounding_box():
    grid = LifeGrid({(2, 3), (5, 7), (1, 1)})
    assert grid.bounding_box() == (1, 1, 5, 7)


def test_empty_bounding_box():
    grid = LifeGrid()
    assert grid.bounding_box() == (0, 0, 0, 0)


def test_all_patterns_load():
    """Every pattern should be a non-empty set of cells."""
    for name in list_patterns():
        pattern = get_pattern(name)
        assert len(pattern) > 0, f"Pattern {name} is empty"


def test_pattern_preview():
    preview = pattern_preview("blinker")
    assert "O" in preview


def test_list_patterns_sorted():
    names = list_patterns()
    assert names == sorted(names)


def test_r_pentomino_grows():
    """R-pentomino is a methuselah — it should grow beyond 5 cells quickly."""
    grid = LifeGrid(PATTERNS["r_pentomino"])
    assert grid.population() == 5
    for _ in range(10):
        grid = grid.step()
    assert grid.population() > 5


def test_toad_oscillates():
    """Toad is period-2 oscillator."""
    grid = LifeGrid(PATTERNS["toad"])
    original = frozenset(grid.alive)
    grid = grid.step()
    grid = grid.step()
    assert frozenset(grid.alive) == original


def test_beacon_oscillates():
    """Beacon is period-2 oscillator."""
    grid = LifeGrid(PATTERNS["beacon"])
    original = frozenset(grid.alive)
    grid = grid.step()
    grid = grid.step()
    assert frozenset(grid.alive) == original


def test_gosper_gun_produces_gliders():
    """After enough steps, population should grow beyond initial 36."""
    grid = LifeGrid(PATTERNS["gosper_glider_gun"])
    initial_pop = grid.population()
    for _ in range(120):
        grid = grid.step()
    assert grid.population() > initial_pop


if __name__ == "__main__":
    import sys
    # Simple runner when pytest isn't available
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
