"""Tests for Conway's Game of Life engine."""

from life import Grid


# ── basic construction ───────────────────────────────────────────────

def test_empty_grid():
    g = Grid()
    assert g.population == 0
    assert not g.is_alive(0, 0)


def test_grid_with_cells():
    g = Grid({(0, 0), (1, 1)})
    assert g.population == 2
    assert g.is_alive(0, 0)
    assert g.is_alive(1, 1)
    assert not g.is_alive(0, 1)


# ── bounding box ─────────────────────────────────────────────────────

def test_bounding_box_empty():
    assert Grid().bounding_box == (0, 0, 0, 0)


def test_bounding_box():
    g = Grid({(2, 3), (5, 7)})
    assert g.bounding_box == (2, 3, 5, 7)


# ── still lifes ──────────────────────────────────────────────────────

def test_block_is_still():
    """A 2x2 block should not change."""
    block = Grid({(0, 0), (0, 1), (1, 0), (1, 1)})
    assert block.step() == block


def test_beehive_is_still():
    beehive = Grid.from_pattern([
        ".*.",
        "*.*",
        "*.*",
        ".*.",
    ])
    assert beehive.step() == beehive


# ── oscillators ──────────────────────────────────────────────────────

def test_blinker_period_2():
    """A blinker should return to its original state after 2 steps."""
    horizontal = Grid({(0, -1), (0, 0), (0, 1)})
    gen1 = horizontal.step()
    # After one step it becomes vertical
    assert gen1 != horizontal
    assert gen1.population == 3
    # After two steps it's back to horizontal
    gen2 = gen1.step()
    assert gen2 == horizontal


def test_toad_period_2():
    toad = Grid.from_pattern([
        ".***",
        "***.",
    ])
    gen1 = toad.step()
    assert gen1 != toad
    gen2 = gen1.step()
    assert gen2 == toad


# ── death and birth ──────────────────────────────────────────────────

def test_lone_cell_dies():
    g = Grid({(0, 0)})
    assert g.step().population == 0


def test_two_cells_die():
    g = Grid({(0, 0), (0, 1)})
    assert g.step().population == 0


def test_three_in_L_produce_block():
    """Three cells in an L-shape should produce a 2x2 block."""
    g = Grid({(0, 0), (0, 1), (1, 0)})
    result = g.step()
    assert result == Grid({(0, 0), (0, 1), (1, 0), (1, 1)})


# ── pattern loading ──────────────────────────────────────────────────

def test_from_pattern():
    g = Grid.from_pattern(["*.", ".*"])
    assert g.is_alive(0, 0)
    assert g.is_alive(1, 1)
    assert not g.is_alive(0, 1)
    assert g.population == 2


def test_from_pattern_O_char():
    g = Grid.from_pattern(["O.", ".O"])
    assert g.population == 2


# ── render ───────────────────────────────────────────────────────────

def test_render_empty():
    assert Grid().render() == "."


def test_render_single_cell():
    rendered = Grid({(0, 0)}).render(padding=0)
    assert rendered == "*"


# ── equality ─────────────────────────────────────────────────────────

def test_equality():
    a = Grid({(0, 0), (1, 1)})
    b = Grid({(1, 1), (0, 0)})
    assert a == b


def test_inequality():
    assert Grid({(0, 0)}) != Grid({(1, 1)})


def test_not_equal_to_non_grid():
    assert Grid() != "not a grid"
