"""Tests for maze generation and solving."""

import pytest
from maze import Maze


class TestMazeInit:
    def test_dimensions(self):
        m = Maze(5, 5)
        assert m.width == 5
        assert m.height == 5

    def test_grid_size(self):
        m = Maze(5, 5)
        m.generate()
        assert len(m.grid) == 11  # 2*5+1
        assert len(m.grid[0]) == 11

    def test_grid_size_rectangular(self):
        m = Maze(3, 7)
        m.generate()
        assert len(m.grid) == 15  # 2*7+1
        assert len(m.grid[0]) == 7  # 2*3+1


class TestMazeGeneration:
    def test_start_end_open(self):
        m = Maze(5, 5, seed=42)
        m.generate()
        sr, sc = m.start
        er, ec = m.end
        assert m.grid[sr][sc] == 0, "Start must be open"
        assert m.grid[er][ec] == 0, "End must be open"

    def test_border_walls(self):
        """Outer border should be walls (except start/end)."""
        m = Maze(5, 5, seed=42)
        m.generate()
        g = m.grid
        rows, cols = len(g), len(g[0])
        sr, sc = m.start
        er, ec = m.end

        for c in range(cols):
            if (0, c) not in [(sr, sc), (er, ec)]:
                assert g[0][c] == 1, f"Top border at col {c} should be wall"
            if (rows - 1, c) not in [(sr, sc), (er, ec)]:
                assert g[rows - 1][c] == 1, f"Bottom border at col {c} should be wall"
        for r in range(rows):
            if (r, 0) not in [(sr, sc), (er, ec)]:
                assert g[r][0] == 1, f"Left border at row {r} should be wall"
            if (r, cols - 1) not in [(sr, sc), (er, ec)]:
                assert g[r][cols - 1] == 1, f"Right border at row {r} should be wall"

    def test_all_cells_reachable_backtracker(self):
        """Every passage cell should be reachable from start (BFS)."""
        m = Maze(5, 5, seed=42)
        m.generate("backtracker")
        _assert_all_reachable(m)

    def test_all_cells_reachable_prims(self):
        m = Maze(5, 5, seed=42)
        m.generate("prims")
        _assert_all_reachable(m)

    def test_deterministic_with_seed(self):
        m1 = Maze(5, 5, seed=123)
        m1.generate()
        m2 = Maze(5, 5, seed=123)
        m2.generate()
        assert m1.grid == m2.grid

    def test_different_seeds_different_mazes(self):
        m1 = Maze(5, 5, seed=1)
        m1.generate()
        m2 = Maze(5, 5, seed=2)
        m2.generate()
        assert m1.grid != m2.grid

    def test_unknown_algorithm_raises(self):
        m = Maze(5, 5)
        with pytest.raises(ValueError):
            m.generate("unknown")

    def test_tiny_maze(self):
        """1x1 maze should still work."""
        m = Maze(1, 1, seed=42)
        m.generate()
        assert len(m.grid) == 3
        assert len(m.grid[0]) == 3
        # Center should be open
        assert m.grid[1][1] == 0

    def test_large_maze(self):
        m = Maze(20, 20, seed=42)
        m.generate()
        _assert_all_reachable(m)

    def test_prims_algorithm(self):
        m = Maze(8, 8, seed=99)
        m.generate("prims")
        _assert_all_reachable(m)


class TestSolver:
    """Tests for solver.py — will pass once Codex delivers it."""

    def test_bfs_finds_path(self):
        try:
            from solver import solve
        except ImportError:
            pytest.skip("solver.py not yet available")
        m = Maze(5, 5, seed=42)
        m.generate()
        path = solve(m.grid, m.start, m.end, "bfs")
        assert path is not None
        assert path[0] == m.start
        assert path[-1] == m.end

    def test_dfs_finds_path(self):
        try:
            from solver import solve
        except ImportError:
            pytest.skip("solver.py not yet available")
        m = Maze(5, 5, seed=42)
        m.generate()
        path = solve(m.grid, m.start, m.end, "dfs")
        assert path is not None

    def test_astar_finds_path(self):
        try:
            from solver import solve
        except ImportError:
            pytest.skip("solver.py not yet available")
        m = Maze(5, 5, seed=42)
        m.generate()
        path = solve(m.grid, m.start, m.end, "astar")
        assert path is not None

    def test_path_only_passages(self):
        """Solution path should only go through passage cells."""
        try:
            from solver import solve
        except ImportError:
            pytest.skip("solver.py not yet available")
        m = Maze(10, 10, seed=42)
        m.generate()
        path = solve(m.grid, m.start, m.end, "bfs")
        assert path is not None
        for r, c in path:
            assert m.grid[r][c] == 0, f"Path cell ({r},{c}) is a wall"

    def test_bfs_shortest_path(self):
        """BFS should find the shortest path."""
        try:
            from solver import solve
        except ImportError:
            pytest.skip("solver.py not yet available")
        m = Maze(5, 5, seed=42)
        m.generate()
        bfs_path = solve(m.grid, m.start, m.end, "bfs")
        dfs_path = solve(m.grid, m.start, m.end, "dfs")
        assert bfs_path is not None
        assert dfs_path is not None
        assert len(bfs_path) <= len(dfs_path)


def _assert_all_reachable(m: Maze):
    """BFS from (1,1) to check all passage cells are reachable."""
    g = m.grid
    rows, cols = len(g), len(g[0])
    visited = set()
    queue = [(1, 1)]
    visited.add((1, 1))

    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited and g[nr][nc] == 0:
                visited.add((nr, nc))
                queue.append((nr, nc))

    # Count all passage cells
    passages = set()
    for r in range(rows):
        for c in range(cols):
            if g[r][c] == 0:
                passages.add((r, c))

    assert passages == visited, f"Unreachable passages: {passages - visited}"
