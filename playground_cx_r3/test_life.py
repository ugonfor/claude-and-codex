"""Tests for Game of Life engine."""

from life import Grid, glider, blinker


def test_empty_grid():
    g = Grid(5, 5)
    assert len(g.cells) == 0
    g2 = g.step()
    assert len(g2.cells) == 0


def test_set_get():
    g = Grid(10, 10)
    g.set(3, 4)
    assert g.get(3, 4) is True
    assert g.get(0, 0) is False
    g.set(3, 4, False)
    assert g.get(3, 4) is False


def test_blinker_oscillates():
    """A blinker should return to original state after 2 steps."""
    g = Grid(10, 10)
    blinker(g, 4, 4)
    original = frozenset(g.cells)
    g1 = g.step()
    assert frozenset(g1.cells) != original  # Different after 1 step
    g2 = g1.step()
    assert frozenset(g2.cells) == original  # Same after 2 steps


def test_glider_moves():
    """A glider should move diagonally after 4 steps."""
    g = Grid(20, 20)
    glider(g, 1, 1)
    original = frozenset(g.cells)
    for _ in range(4):
        g = g.step()
    # After 4 steps, glider shifts (1, 1) diagonally
    shifted = frozenset((x + 1, y + 1) for x, y in original)
    assert frozenset(g.cells) == shifted


def test_block_is_still():
    """A 2x2 block is a still life — never changes."""
    g = Grid(10, 10)
    for x, y in [(3, 3), (3, 4), (4, 3), (4, 4)]:
        g.set(x, y)
    original = frozenset(g.cells)
    g2 = g.step()
    assert frozenset(g2.cells) == original


def test_single_cell_dies():
    """A lone cell with no neighbors should die."""
    g = Grid(5, 5)
    g.set(2, 2)
    g2 = g.step()
    assert len(g2.cells) == 0


def test_grid_str():
    g = Grid(3, 3)
    g.set(1, 1)
    s = str(g)
    lines = s.split("\n")
    assert len(lines) == 3
    assert "#" in lines[1]


if __name__ == "__main__":
    test_empty_grid()
    test_set_get()
    test_blinker_oscillates()
    test_glider_moves()
    test_block_is_still()
    test_single_cell_dies()
    test_grid_str()
    print("All 7 tests passed!")
