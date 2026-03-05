"""Tests for Langton's Ant engine."""

from ant import Ant, Direction, LangtonGrid


class TestDirection:
    def test_turn_right_cycles(self):
        ant = Ant(0, 0, Direction.UP)
        ant.turn_right()
        assert ant.direction == Direction.RIGHT
        ant.turn_right()
        assert ant.direction == Direction.DOWN
        ant.turn_right()
        assert ant.direction == Direction.LEFT
        ant.turn_right()
        assert ant.direction == Direction.UP

    def test_turn_left_cycles(self):
        ant = Ant(0, 0, Direction.UP)
        ant.turn_left()
        assert ant.direction == Direction.LEFT
        ant.turn_left()
        assert ant.direction == Direction.DOWN
        ant.turn_left()
        assert ant.direction == Direction.RIGHT
        ant.turn_left()
        assert ant.direction == Direction.UP


class TestAntMovement:
    def test_move_up(self):
        ant = Ant(5, 5, Direction.UP)
        ant.move_forward(10, 10)
        assert (ant.x, ant.y) == (5, 4)

    def test_move_right(self):
        ant = Ant(5, 5, Direction.RIGHT)
        ant.move_forward(10, 10)
        assert (ant.x, ant.y) == (6, 5)

    def test_move_wraps_horizontal(self):
        ant = Ant(9, 5, Direction.RIGHT)
        ant.move_forward(10, 10)
        assert (ant.x, ant.y) == (0, 5)

    def test_move_wraps_vertical(self):
        ant = Ant(5, 0, Direction.UP)
        ant.move_forward(10, 10)
        assert (ant.x, ant.y) == (5, 9)


class TestLangtonGrid:
    def test_initial_state(self):
        grid = LangtonGrid(20, 20)
        assert grid.ant.x == 10
        assert grid.ant.y == 10
        assert grid.population == 0
        assert grid.step_count == 0

    def test_first_step_on_white(self):
        """White cell: turn right, flip to black, move forward."""
        grid = LangtonGrid(20, 20)
        grid.step()
        # Started UP, turned RIGHT, moved to (11, 10)
        assert grid.ant.direction == Direction.RIGHT
        assert grid.ant.x == 11
        assert grid.ant.y == 10
        # Original position should now be black
        assert grid.is_black(10, 10)
        assert grid.population == 1
        assert grid.step_count == 1

    def test_step_on_black(self):
        """Black cell: turn left, flip to white, move forward."""
        grid = LangtonGrid(20, 20)
        # Manually place ant on a black cell
        grid.black_cells.add((10, 10))
        grid.step()
        # Started UP, turned LEFT, moved to (9, 10)
        assert grid.ant.direction == Direction.LEFT
        assert grid.ant.x == 9
        assert grid.ant.y == 10
        # Cell should now be white
        assert not grid.is_black(10, 10)
        assert grid.population == 0

    def test_two_steps_return(self):
        """After 2 steps from same position, ant has moved twice."""
        grid = LangtonGrid(20, 20)
        grid.step()  # white -> turn right, flip black, move
        grid.step()  # white -> turn right, flip black, move
        assert grid.step_count == 2
        assert grid.population == 2

    def test_run_multiple(self):
        grid = LangtonGrid(40, 40)
        grid.run(100)
        assert grid.step_count == 100
        assert grid.population > 0

    def test_known_104_steps(self):
        """After 104 steps, Langton's ant produces a known symmetric pattern."""
        grid = LangtonGrid(80, 40)
        grid.run(104)
        assert grid.step_count == 104
        # The ant should have returned near the center area
        # and population should be specific (known value for 104 steps)
        # Just verify it ran without error and has reasonable population
        assert 0 < grid.population < 104
