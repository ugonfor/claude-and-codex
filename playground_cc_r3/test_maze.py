"""Tests for maze generation and solving."""

import pytest
from maze import (
    Maze,
    generate_dfs,
    generate_prims,
    generate_kruskals,
    solve_bfs,
    solve_dfs,
    solve_astar,
    OPPOSITE,
    DELTA,
)


# ---------------------------------------------------------------------------
# Maze data structure
# ---------------------------------------------------------------------------


class TestMaze:
    def test_create(self):
        m = Maze(5, 10)
        assert m.rows == 5
        assert m.cols == 10

    def test_invalid_dimensions(self):
        with pytest.raises(ValueError):
            Maze(0, 5)
        with pytest.raises(ValueError):
            Maze(3, -1)

    def test_open_passage(self):
        m = Maze(3, 3)
        m.open_passage(0, 0, "S")
        assert m.has_passage(0, 0, "S")
        assert m.has_passage(1, 0, "N")
        assert not m.has_passage(0, 0, "E")

    def test_open_passage_out_of_bounds(self):
        m = Maze(3, 3)
        with pytest.raises(ValueError):
            m.open_passage(0, 0, "N")

    def test_neighbors(self):
        m = Maze(3, 3)
        m.open_passage(1, 1, "N")
        m.open_passage(1, 1, "E")
        nbrs = set(m.neighbors(1, 1))
        assert nbrs == {(0, 1), (1, 2)}

    def test_all_neighbors(self):
        m = Maze(3, 3)
        # Corner cell (0,0) has 2 neighbors
        assert len(m.all_neighbors(0, 0)) == 2
        # Center cell (1,1) has 4 neighbors
        assert len(m.all_neighbors(1, 1)) == 4
        # Edge cell (0,1) has 3 neighbors
        assert len(m.all_neighbors(0, 1)) == 3


# ---------------------------------------------------------------------------
# Generation algorithms
# ---------------------------------------------------------------------------

def _is_perfect_maze(maze: Maze) -> bool:
    """Check that maze is a spanning tree: connected and no cycles."""
    visited = set()
    parent: dict[tuple[int, int], tuple[int, int] | None] = {}

    stack = [(0, 0)]
    visited.add((0, 0))
    parent[(0, 0)] = None
    edge_count = 0

    while stack:
        r, c = stack.pop()
        for nr, nc in maze.neighbors(r, c):
            if (nr, nc) == parent.get((r, c)):
                continue
            if (nr, nc) in visited:
                return False  # cycle detected
            visited.add((nr, nc))
            parent[(nr, nc)] = (r, c)
            stack.append((nr, nc))
            edge_count += 1

    # All cells reachable
    return len(visited) == maze.rows * maze.cols


class TestGenerateDFS:
    def test_produces_perfect_maze(self):
        m = generate_dfs(10, 10, seed=42)
        assert _is_perfect_maze(m)

    def test_deterministic_with_seed(self):
        m1 = generate_dfs(8, 8, seed=123)
        m2 = generate_dfs(8, 8, seed=123)
        for r in range(8):
            for c in range(8):
                assert m1.passages[r][c] == m2.passages[r][c]

    def test_small_maze(self):
        m = generate_dfs(1, 1, seed=0)
        assert m.rows == 1 and m.cols == 1
        assert _is_perfect_maze(m)

    def test_rectangular(self):
        m = generate_dfs(3, 7, seed=99)
        assert _is_perfect_maze(m)


class TestGeneratePrims:
    def test_produces_perfect_maze(self):
        m = generate_prims(10, 10, seed=42)
        assert _is_perfect_maze(m)

    def test_deterministic_with_seed(self):
        m1 = generate_prims(8, 8, seed=456)
        m2 = generate_prims(8, 8, seed=456)
        for r in range(8):
            for c in range(8):
                assert m1.passages[r][c] == m2.passages[r][c]

    def test_rectangular(self):
        m = generate_prims(5, 12, seed=77)
        assert _is_perfect_maze(m)


class TestGenerateKruskals:
    def test_produces_perfect_maze(self):
        m = generate_kruskals(10, 10, seed=42)
        assert _is_perfect_maze(m)

    def test_deterministic_with_seed(self):
        m1 = generate_kruskals(8, 8, seed=789)
        m2 = generate_kruskals(8, 8, seed=789)
        for r in range(8):
            for c in range(8):
                assert m1.passages[r][c] == m2.passages[r][c]

    def test_rectangular(self):
        m = generate_kruskals(4, 9, seed=55)
        assert _is_perfect_maze(m)


# ---------------------------------------------------------------------------
# Solving algorithms
# ---------------------------------------------------------------------------

@pytest.fixture
def small_maze():
    """A 5x5 DFS maze for solver tests."""
    return generate_dfs(5, 5, seed=42)


class TestSolveBFS:
    def test_finds_path(self, small_maze):
        path = solve_bfs(small_maze, (0, 0), (4, 4))
        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (4, 4)

    def test_path_is_valid(self, small_maze):
        path = solve_bfs(small_maze, (0, 0), (4, 4))
        _assert_valid_path(small_maze, path)

    def test_same_start_end(self, small_maze):
        path = solve_bfs(small_maze, (2, 2), (2, 2))
        assert path == [(2, 2)]

    def test_shortest_path(self, small_maze):
        # BFS guarantees shortest path
        bfs_path = solve_bfs(small_maze, (0, 0), (4, 4))
        astar_path = solve_astar(small_maze, (0, 0), (4, 4))
        assert len(bfs_path) == len(astar_path)


class TestSolveDFS:
    def test_finds_path(self, small_maze):
        path = solve_dfs(small_maze, (0, 0), (4, 4))
        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (4, 4)

    def test_path_is_valid(self, small_maze):
        path = solve_dfs(small_maze, (0, 0), (4, 4))
        _assert_valid_path(small_maze, path)


class TestSolveAStar:
    def test_finds_path(self, small_maze):
        path = solve_astar(small_maze, (0, 0), (4, 4))
        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (4, 4)

    def test_path_is_valid(self, small_maze):
        path = solve_astar(small_maze, (0, 0), (4, 4))
        _assert_valid_path(small_maze, path)

    def test_optimal(self, small_maze):
        bfs_path = solve_bfs(small_maze, (0, 0), (4, 4))
        astar_path = solve_astar(small_maze, (0, 0), (4, 4))
        assert len(astar_path) == len(bfs_path)


# ---------------------------------------------------------------------------
# Cross-algorithm tests
# ---------------------------------------------------------------------------

class TestCrossAlgorithm:
    """Every generator + solver combo should work."""

    @pytest.mark.parametrize("gen_name,gen_fn", [
        ("dfs", generate_dfs),
        ("prims", generate_prims),
        ("kruskals", generate_kruskals),
    ])
    @pytest.mark.parametrize("solve_name,solve_fn", [
        ("bfs", solve_bfs),
        ("dfs", solve_dfs),
        ("astar", solve_astar),
    ])
    def test_all_combos(self, gen_name, gen_fn, solve_name, solve_fn):
        maze = gen_fn(8, 8, seed=42)
        path = solve_fn(maze, (0, 0), (7, 7))
        assert path is not None
        _assert_valid_path(maze, path)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_valid_path(maze: Maze, path: list[tuple[int, int]]) -> None:
    """Assert that each consecutive pair in the path is connected by a passage."""
    assert path is not None and len(path) >= 1
    for i in range(len(path) - 1):
        r, c = path[i]
        nr, nc = path[i + 1]
        nbrs = maze.neighbors(r, c)
        assert (nr, nc) in nbrs, f"No passage from {path[i]} to {path[i+1]}"
