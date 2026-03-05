"""Tests for Langton's Ant simulation."""

import pytest
from langton import Ant, Direction, Grid, LangtonSimulation


class TestDirection:
    def test_turn_right_cycle(self):
        d = Direction.UP
        assert d.turn_right() == Direction.RIGHT
        assert d.turn_right().turn_right() == Direction.DOWN
        assert d.turn_right().turn_right().turn_right() == Direction.LEFT
        assert d.turn_right().turn_right().turn_right().turn_right() == Direction.UP

    def test_turn_left_cycle(self):
        d = Direction.UP
        assert d.turn_left() == Direction.LEFT
        assert d.turn_left().turn_left() == Direction.DOWN

    def test_deltas(self):
        assert Direction.UP.delta() == (-1, 0)
        assert Direction.RIGHT.delta() == (0, 1)
        assert Direction.DOWN.delta() == (1, 0)
        assert Direction.LEFT.delta() == (0, -1)


class TestGrid:
    def test_initial_state(self):
        g = Grid(4, 4)
        assert g.get(0, 0) == 0
        assert g.get(3, 3) == 0

    def test_set_and_get(self):
        g = Grid(4, 4)
        g.set(1, 2, 1)
        assert g.get(1, 2) == 1

    def test_out_of_bounds(self):
        g = Grid(4, 4)
        assert g.get(-1, 0) == -1
        assert g.get(0, 4) == -1

    def test_next_color(self):
        g = Grid(4, 4, num_colors=3)
        g.set(0, 0, 2)
        assert g.next_color(0, 0) == 0  # wraps around


class TestAnt:
    def test_move_up(self):
        a = Ant(5, 5, Direction.UP)
        a.move()
        assert (a.row, a.col) == (4, 5)

    def test_turn_and_move(self):
        a = Ant(5, 5, Direction.UP)
        a.turn(right=True)
        assert a.direction == Direction.RIGHT
        a.move()
        assert (a.row, a.col) == (5, 6)


class TestSimulation:
    def test_single_step_on_white(self):
        """On white cell: turn right, flip to black, move forward."""
        sim = LangtonSimulation(10, 10, "RL")
        sim.add_ant(5, 5)
        sim.step()
        # Was facing UP, turned RIGHT -> now facing RIGHT, moved to (5,6)
        assert sim.ants[0].row == 5
        assert sim.ants[0].col == 6
        assert sim.ants[0].direction == Direction.RIGHT
        # Cell (5,5) should now be 1 (black)
        assert sim.grid.get(5, 5) == 1

    def test_single_step_on_black(self):
        """On black cell: turn left, flip to white, move forward."""
        sim = LangtonSimulation(10, 10, "RL")
        sim.add_ant(5, 5, Direction.UP)
        sim.grid.set(5, 5, 1)  # make it black
        sim.step()
        # Was facing UP, turned LEFT -> now facing LEFT, moved to (5,4)
        assert sim.ants[0].row == 5
        assert sim.ants[0].col == 4
        assert sim.ants[0].direction == Direction.LEFT
        # Cell (5,5) should now be 0 (white)
        assert sim.grid.get(5, 5) == 0

    def test_ant_dies_at_boundary(self):
        sim = LangtonSimulation(10, 10, "RL")
        sim.add_ant(0, 0, Direction.UP)
        # On white -> turn right -> face RIGHT -> move to (0,1). Still alive.
        sim.step()
        assert sim.ants[0].alive is True
        # Now at (0,1) facing RIGHT on white -> turn right -> face DOWN -> move to (1,1)
        sim.step()
        assert sim.ants[0].alive is True

    def test_run_many_steps(self):
        sim = LangtonSimulation(64, 64, "RL")
        sim.add_ant(32, 32)
        sim.run(100)
        assert sim.step_count == 100
        stats = sim.stats()
        assert stats["cells_colored"] > 0

    def test_multi_ant(self):
        sim = LangtonSimulation(20, 20, "RL")
        sim.add_ant(10, 10, Direction.UP)
        sim.add_ant(10, 15, Direction.DOWN)
        sim.run(50)
        assert sim.stats()["ants_total"] == 2

    def test_extended_rule(self):
        """Test with RLR rule (3 colors)."""
        sim = LangtonSimulation(20, 20, "RLR")
        sim.add_ant(10, 10)
        sim.run(30)
        assert sim.grid.num_colors == 3
        assert sim.step_count == 30

    def test_render_ascii(self):
        sim = LangtonSimulation(5, 5, "RL")
        sim.add_ant(2, 2)
        output = sim.render_ascii()
        lines = output.split("\n")
        assert len(lines) == 5
        assert "A" in output

    def test_stats(self):
        sim = LangtonSimulation(10, 10, "RL")
        sim.add_ant(5, 5)
        sim.run(10)
        stats = sim.stats()
        assert "steps" in stats
        assert "coverage_pct" in stats
        assert stats["rule"] == "RL"
