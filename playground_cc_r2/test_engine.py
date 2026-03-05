"""Tests for the Game of Life engine."""

import pytest
from engine import (
    step, bounded_step, neighbors, random_grid,
    make_pattern, grid_to_2d, population, bounding_box, run,
    PATTERNS,
)


class TestNeighbors:
    def test_count(self):
        assert len(neighbors((5, 5))) == 8

    def test_values(self):
        nbs = set(neighbors((1, 1)))
        expected = {(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)}
        assert nbs == expected


class TestStep:
    def test_empty_stays_empty(self):
        assert step(set()) == set()

    def test_single_cell_dies(self):
        assert step({(0, 0)}) == set()

    def test_block_stable(self):
        """A 2x2 block is a still life."""
        block = {(0, 0), (0, 1), (1, 0), (1, 1)}
        assert step(block) == block

    def test_blinker_oscillates(self):
        """Horizontal blinker -> vertical -> horizontal."""
        horizontal = {(0, 0), (0, 1), (0, 2)}
        vertical = step(horizontal)
        assert vertical == {(-1, 1), (0, 1), (1, 1)}
        assert step(vertical) == horizontal

    def test_glider_moves(self):
        """Glider should advance after 4 steps."""
        glider = make_pattern("glider")
        g1 = step(step(step(step(glider))))
        # Glider moves down-right by (1, 1) every 4 generations
        expected = {(r + 1, c + 1) for r, c in glider}
        assert g1 == expected


class TestBoundedStep:
    def test_cells_stay_in_bounds(self):
        grid = {(0, 0), (0, 1), (0, 2)}
        result = bounded_step(grid, 5, 5)
        for r, c in result:
            assert 0 <= r < 5
            assert 0 <= c < 5

    def test_edge_cells_clipped(self):
        """Blinker at row 0 — cells at row -1 should be clipped."""
        horizontal = {(0, 0), (0, 1), (0, 2)}
        result = bounded_step(horizontal, 5, 5)
        assert all(r >= 0 for r, c in result)


class TestPatterns:
    def test_all_patterns_exist(self):
        for name in PATTERNS:
            grid = make_pattern(name)
            assert len(grid) > 0

    def test_offset(self):
        grid = make_pattern("glider", offset=(10, 10))
        assert all(r >= 10 and c >= 10 for r, c in grid)

    def test_unknown_pattern_raises(self):
        with pytest.raises(ValueError):
            make_pattern("nonexistent")


class TestRandomGrid:
    def test_density_zero(self):
        assert random_grid(10, 10, density=0.0) == set()

    def test_density_one(self):
        grid = random_grid(5, 5, density=1.0)
        assert len(grid) == 25

    def test_within_bounds(self):
        grid = random_grid(10, 20)
        for r, c in grid:
            assert 0 <= r < 10
            assert 0 <= c < 20


class TestUtilities:
    def test_grid_to_2d(self):
        grid = {(0, 0), (1, 1)}
        arr = grid_to_2d(grid, 2, 2)
        assert arr == [[True, False], [False, True]]

    def test_population(self):
        assert population(set()) == 0
        assert population({(0, 0), (1, 1), (2, 2)}) == 3

    def test_bounding_box_empty(self):
        assert bounding_box(set()) is None

    def test_bounding_box(self):
        grid = {(2, 3), (5, 1), (0, 7)}
        assert bounding_box(grid) == (0, 1, 5, 7)


class TestRun:
    def test_run_returns_correct_length(self):
        grid = make_pattern("blinker")
        history = run(grid, 5)
        assert len(history) == 6  # initial + 5 generations

    def test_run_bounded(self):
        grid = make_pattern("blinker", offset=(2, 2))
        history = run(grid, 3, rows=10, cols=10)
        for state in history:
            for r, c in state:
                assert 0 <= r < 10 and 0 <= c < 10
