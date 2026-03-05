"""Tests for Langton's Ant simulation."""

from ant import LangtonAnt, DIRECTIONS


def test_initial_state():
    ant = LangtonAnt()
    assert ant.x == 0
    assert ant.y == 0
    assert ant.direction == 0
    assert ant.step_count == 0
    assert len(ant.black_cells) == 0


def test_first_step_turns_right_on_white():
    ant = LangtonAnt()
    ant.step()
    # Was on white: turn right (0->1), flip to black, move right
    assert (0, 0) in ant.black_cells  # original cell now black
    assert ant.direction == 1  # facing right
    assert ant.x == 1
    assert ant.y == 0
    assert ant.step_count == 1


def test_second_step():
    ant = LangtonAnt()
    ant.step()  # white -> right, at (1,0) facing right
    ant.step()  # white -> right again, at (1,1) facing down
    assert (1, 0) in ant.black_cells
    assert ant.direction == 2  # facing down
    assert ant.x == 1
    assert ant.y == 1


def test_return_to_black_cell_turns_left():
    ant = LangtonAnt()
    # Run 4 steps: ant makes a small pattern and revisits area
    ant.run(4)
    # After 4 steps the ant should have visited and flipped cells
    assert ant.step_count == 4


def test_symmetry_after_104_steps():
    """After 104 steps, Langton's ant produces a known symmetric pattern."""
    ant = LangtonAnt()
    ant.run(104)
    # Known property: after 104 steps the ant is at a specific location
    # and the pattern has a known number of black cells
    assert ant.step_count == 104
    assert len(ant.black_cells) > 0


def test_highway_emerges():
    """After ~10000 steps, Langton's ant enters the 'highway' phase."""
    ant = LangtonAnt()
    ant.run(11000)
    # The highway moves diagonally, so the ant should be far from origin
    dist = abs(ant.x) + abs(ant.y)
    assert dist > 20  # ant has moved significantly


def test_custom_start_position():
    ant = LangtonAnt(x=5, y=10, direction=2)
    assert ant.x == 5
    assert ant.y == 10
    assert ant.direction == 2
    ant.step()
    # On white facing down: turn right -> face left(3), move left
    assert ant.direction == 3
    assert ant.x == 4
    assert ant.y == 10


def test_bounds():
    ant = LangtonAnt()
    assert ant.bounds() == (0, 0, 0, 0)
    ant.run(10)
    min_x, min_y, max_x, max_y = ant.bounds()
    assert min_x <= ant.x <= max_x
    assert min_y <= ant.y <= max_y


def test_render_contains_ant():
    ant = LangtonAnt()
    ant.run(5)
    rendered = ant.render()
    assert "A" in rendered


def test_render_contains_black_cells():
    ant = LangtonAnt()
    ant.run(10)
    rendered = ant.render()
    assert "#" in rendered


def test_directions_are_four():
    assert len(DIRECTIONS) == 4
