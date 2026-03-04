"""Tests for Conway's Game of Life engine."""

import pytest
from game import GameOfLife


class TestGameOfLife:
    def test_empty_grid_stays_empty(self):
        game = GameOfLife(10, 10)
        game.step()
        assert game.count_alive() == 0
        assert game.generation == 1

    def test_set_and_check_alive(self):
        game = GameOfLife(10, 10)
        game.set_alive(3, 4)
        assert game.is_alive(3, 4)
        assert not game.is_alive(0, 0)

    def test_set_dead(self):
        game = GameOfLife(10, 10)
        game.set_alive(3, 4)
        game.set_dead(3, 4)
        assert not game.is_alive(3, 4)

    def test_lonely_cell_dies(self):
        """A single cell with no neighbors dies."""
        game = GameOfLife(10, 10)
        game.set_alive(5, 5)
        game.step()
        assert not game.is_alive(5, 5)

    def test_blinker_oscillates(self):
        """Blinker (period 2): three horizontal cells oscillate to vertical."""
        game = GameOfLife(10, 10)
        # Horizontal blinker
        game.set_alive(4, 5)
        game.set_alive(5, 5)
        game.set_alive(6, 5)

        game.step()
        # Should become vertical
        assert game.is_alive(5, 4)
        assert game.is_alive(5, 5)
        assert game.is_alive(5, 6)
        assert not game.is_alive(4, 5)
        assert not game.is_alive(6, 5)

        game.step()
        # Should return to horizontal
        assert game.is_alive(4, 5)
        assert game.is_alive(5, 5)
        assert game.is_alive(6, 5)
        assert not game.is_alive(5, 4)
        assert not game.is_alive(5, 6)

    def test_block_is_stable(self):
        """Block (still life): 2x2 square doesn't change."""
        game = GameOfLife(10, 10)
        game.set_alive(4, 4)
        game.set_alive(5, 4)
        game.set_alive(4, 5)
        game.set_alive(5, 5)

        game.step()
        assert game.is_alive(4, 4)
        assert game.is_alive(5, 4)
        assert game.is_alive(4, 5)
        assert game.is_alive(5, 5)
        assert game.count_alive() == 4

    def test_toroidal_wrapping(self):
        """Cells wrap around edges."""
        game = GameOfLife(10, 10)
        game.set_alive(0, 0)
        assert game.is_alive(10, 10)  # wraps to (0,0)
        assert game.is_alive(0, 0)

    def test_neighbor_count_wrapping(self):
        """Neighbors count across edges (toroidal)."""
        game = GameOfLife(5, 5)
        # Place three cells at the right edge wrapping around
        game.set_alive(4, 0)
        game.set_alive(4, 1)
        game.set_alive(4, 2)
        game.step()
        # The wrapped neighbor at (0,1) should come alive
        assert game.is_alive(0, 1)

    def test_get_grid_returns_copy(self):
        """get_grid() returns a copy, not the internal grid."""
        game = GameOfLife(5, 5)
        game.set_alive(2, 2)
        grid = game.get_grid()
        grid[2][2] = False  # modify the copy
        assert game.is_alive(2, 2)  # original unchanged

    def test_load_pattern(self):
        game = GameOfLife(20, 20)
        pattern = [(0, 0), (1, 0), (2, 0)]  # horizontal blinker
        game.load_pattern(pattern, offset_x=5, offset_y=5)
        assert game.is_alive(5, 5)
        assert game.is_alive(6, 5)
        assert game.is_alive(7, 5)

    def test_clear(self):
        game = GameOfLife(10, 10)
        game.set_alive(3, 3)
        game.step()
        game.clear()
        assert game.count_alive() == 0
        assert game.generation == 0

    def test_generation_counter(self):
        game = GameOfLife(5, 5)
        assert game.generation == 0
        game.step()
        assert game.generation == 1
        game.step()
        game.step()
        assert game.generation == 3

    def test_glider_moves(self):
        """A glider should move diagonally after 4 steps."""
        game = GameOfLife(20, 20)
        # Standard glider pattern
        glider = [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)]
        game.load_pattern(glider, offset_x=2, offset_y=2)

        for _ in range(4):
            game.step()

        # After 4 generations, glider moves 1 right and 1 down
        expected = [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)]
        for x, y in expected:
            assert game.is_alive(x + 3, y + 3), f"Expected alive at ({x+3}, {y+3})"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
