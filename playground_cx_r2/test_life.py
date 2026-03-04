"""Tests for the Game of Life engine."""

from life import Grid, PATTERNS


def test_empty_grid_stays_empty():
    g = Grid(10, 10)
    assert g.population == 0
    g2 = g.step()
    assert g2.population == 0


def test_toggle():
    g = Grid(10, 10)
    g.toggle(3, 4)
    assert g.alive(3, 4)
    assert g.population == 1
    g.toggle(3, 4)
    assert not g.alive(3, 4)
    assert g.population == 0


def test_blinker_oscillates():
    """Blinker is a period-2 oscillator."""
    g = Grid.from_pattern("blinker", 5, 5)
    g1 = g.step()
    g2 = g1.step()
    # After 2 steps it should return to original
    assert g.cells == g2.cells
    # But step 1 should differ
    assert g.cells != g1.cells


def test_glider_moves():
    """Glider translates after 4 steps."""
    g = Grid.from_pattern("glider", 20, 20)
    initial_pop = g.population
    g4 = g.step().step().step().step()
    # Same population (glider doesn't die)
    assert g4.population == initial_pop
    # But different position
    assert g4.cells != g.cells


def test_block_is_stable():
    """A 2x2 block is a still life."""
    cells = {(1, 1), (2, 1), (1, 2), (2, 2)}
    g = Grid(10, 10, cells)
    g2 = g.step()
    assert g.cells == g2.cells


def test_toroidal_wrapping():
    """Cells wrap around edges."""
    g = Grid(5, 5)
    g.toggle(0, 0)
    assert g.alive(5, 5)  # wraps
    assert g.alive(0, 0)
    assert g.alive(-5, -5)  # negative wraps too


def test_from_pattern_random():
    g = Grid.from_pattern("random", 20, 20)
    assert g.width == 20
    assert g.height == 20
    assert g.population > 0  # extremely unlikely to be 0


def test_from_pattern_unknown():
    try:
        Grid.from_pattern("nonexistent")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "nonexistent" in str(e)


def test_all_patterns_load():
    for name in PATTERNS:
        g = Grid.from_pattern(name)
        assert g.population > 0, f"Pattern '{name}' loaded with 0 cells"


def test_generations_iterator():
    g = Grid.from_pattern("blinker", 5, 5)
    gens = g.generations()
    states = [next(gens) for _ in range(5)]
    assert len(states) == 5
    # Period 2: gen 0 == gen 2 == gen 4
    assert states[0].cells == states[2].cells == states[4].cells


def test_grid_equality():
    g1 = Grid(10, 10, {(1, 1), (2, 2)})
    g2 = Grid(10, 10, {(1, 1), (2, 2)})
    g3 = Grid(10, 10, {(1, 1)})
    assert g1 == g2
    assert g1 != g3
    assert g1 != "not a grid"


def test_repr():
    g = Grid(10, 10, {(0, 0), (1, 1)})
    assert "10x10" in repr(g)
    assert "pop=2" in repr(g)
