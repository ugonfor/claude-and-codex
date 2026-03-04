"""Tests for Conway's Game of Life engine.

Written by Claude. Codex: feel free to add more tests!
"""

from game import GameOfLife, GLIDER, BLINKER, BLOCK


def test_empty_grid():
    g = GameOfLife(5, 5)
    assert g.population() == 0
    g.step()
    assert g.population() == 0


def test_block_stable():
    """Block is a still life — should not change."""
    g = GameOfLife(6, 6)
    g.add_pattern(BLOCK, 1, 1)
    assert g.population() == 4
    g.step()
    assert g.population() == 4
    assert g.is_alive(1, 1)
    assert g.is_alive(1, 2)
    assert g.is_alive(2, 1)
    assert g.is_alive(2, 2)


def test_blinker_oscillates():
    """Blinker is a period-2 oscillator."""
    g = GameOfLife(5, 5)
    g.add_pattern(BLINKER, 2, 1)  # horizontal at row 2
    # Step 1: should become vertical
    g.step()
    assert g.is_alive(1, 2)
    assert g.is_alive(2, 2)
    assert g.is_alive(3, 2)
    assert not g.is_alive(2, 1)
    assert not g.is_alive(2, 3)
    # Step 2: back to horizontal
    g.step()
    assert g.is_alive(2, 1)
    assert g.is_alive(2, 2)
    assert g.is_alive(2, 3)


def test_glider_moves():
    """Glider should move diagonally after 4 steps."""
    g = GameOfLife(10, 10)
    g.add_pattern(GLIDER, 0, 0)
    initial_pop = g.population()
    for _ in range(4):
        g.step()
    assert g.population() == initial_pop  # glider preserves population
    assert g.generation == 4


def test_randomize():
    g = GameOfLife(20, 20)
    g.randomize(0.5)
    pop = g.population()
    # With 400 cells at 50% density, expect roughly 200 (allow wide margin)
    assert 50 < pop < 350


def test_count_neighbors_wrapping():
    """Test toroidal wrapping at edges."""
    g = GameOfLife(5, 5)
    g.set_alive(0, 0)
    # Cell at (4, 4) should see (0, 0) as a neighbor (diagonal wrap)
    assert g.count_neighbors(4, 4) == 1
    # Cell at (0, 4) should see (0, 0) as a neighbor (horizontal wrap)
    assert g.count_neighbors(0, 4) == 1


def test_generation_counter():
    g = GameOfLife(3, 3)
    assert g.generation == 0
    g.step()
    assert g.generation == 1
    g.step()
    assert g.generation == 2
    g.clear()
    assert g.generation == 0


if __name__ == "__main__":
    import sys
    # Simple runner if pytest not available
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  PASS: {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL: {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
    sys.exit(0 if passed == len(tests) else 1)
