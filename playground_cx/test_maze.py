"""Tests for maze generation."""

from maze import generate_maze, get_entrance, get_exit, PATH, WALL


def test_dimensions_forced_odd():
    grid = generate_maze(10, 10, seed=1)
    assert len(grid) % 2 == 1
    assert len(grid[0]) % 2 == 1


def test_entrance_and_exit_are_open():
    grid = generate_maze(21, 21, seed=42)
    er, ec = get_entrance(grid)
    xr, xc = get_exit(grid)
    assert grid[er][ec] == PATH
    assert grid[xr][xc] == PATH


def test_border_is_mostly_walls():
    grid = generate_maze(21, 21, seed=42)
    rows, cols = len(grid), len(grid[0])
    # Top and bottom rows should be all walls except entrance/exit
    top_paths = sum(1 for c in range(cols) if grid[0][c] == PATH)
    bottom_paths = sum(1 for c in range(cols) if grid[rows - 1][c] == PATH)
    assert top_paths == 1  # just the entrance
    assert bottom_paths == 1  # just the exit


def test_reproducible_with_seed():
    g1 = generate_maze(15, 15, seed=99)
    g2 = generate_maze(15, 15, seed=99)
    assert g1 == g2


def test_different_seeds_differ():
    g1 = generate_maze(15, 15, seed=1)
    g2 = generate_maze(15, 15, seed=2)
    assert g1 != g2


def test_has_paths():
    grid = generate_maze(21, 21, seed=42)
    path_count = sum(row.count(PATH) for row in grid)
    # A 21x21 maze should have a meaningful number of path cells
    assert path_count > 50
