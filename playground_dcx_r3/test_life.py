"""Tests for Game of Life — engine + display integration (by Claude-Worker)"""

import sys
from life_engine import GameOfLife
from life_display import render_grid, frame_text


def test_blinker_oscillates():
    """Blinker (period 2) should return to initial state after 2 steps."""
    game = GameOfLife.from_pattern("blinker", width=5, height=5)
    gen0 = game.get_live_cells()
    game.step()
    gen1 = game.get_live_cells()
    game.step()
    gen2 = game.get_live_cells()
    assert gen0 == gen2, "Blinker should return after 2 steps"
    assert gen0 != gen1, "Blinker should change after 1 step"


def test_beacon_oscillates():
    """Beacon (period 2) should oscillate."""
    game = GameOfLife.from_pattern("beacon", width=8, height=8)
    gen0 = game.get_live_cells()
    game.step()
    game.step()
    assert game.get_live_cells() == gen0


def test_glider_moves():
    """Glider should move diagonally after 4 steps."""
    game = GameOfLife.from_pattern("glider", width=20, height=20)
    initial = game.get_live_cells()
    for _ in range(4):
        game.step()
    moved = game.get_live_cells()
    assert initial != moved, "Glider should have moved"
    assert game.population == 5, "Glider should keep 5 cells"


def test_empty_stays_empty():
    """An empty board should stay empty."""
    game = GameOfLife(width=10, height=10)
    game.step()
    assert game.population == 0


def test_block_is_still():
    """A 2x2 block is a still life."""
    cells = {(1, 1), (1, 2), (2, 1), (2, 2)}
    game = GameOfLife(width=5, height=5, cells=cells)
    game.step()
    assert game.get_live_cells() == cells


def test_generation_counter():
    game = GameOfLife(width=5, height=5)
    assert game.generation == 0
    game.step()
    assert game.generation == 1
    game.step()
    assert game.generation == 2


def test_all_patterns_load():
    """Every named pattern should load without error."""
    for name in GameOfLife.available_patterns():
        game = GameOfLife.from_pattern(name)
        assert game.population > 0, f"Pattern '{name}' should have cells"


def test_render_grid():
    """Render should produce correct characters."""
    grid = [[True, False], [False, True]]
    result = render_grid(grid, alive="#", dead=".")
    assert result == "#.\n.#"


def test_render_with_border():
    grid = [[True, False], [False, True]]
    result = render_grid(grid, alive="#", dead=".", border=True)
    lines = result.split("\n")
    assert lines[0] == "+--+"
    assert lines[1] == "|#.|"
    assert lines[-1] == "+--+"


def test_frame_text_has_stats():
    game = GameOfLife.from_pattern("blinker", width=5, height=5)
    text = frame_text(game, show_stats=True)
    assert "Gen 0" in text
    assert "Pop" in text


def test_random_init():
    """Random initialization with seed should be reproducible."""
    import random
    rng = random.Random(42)
    game1 = GameOfLife(width=10, height=10)
    for r in range(10):
        for c in range(10):
            if rng.random() < 0.3:
                game1.set_cell(r, c)

    rng2 = random.Random(42)
    game2 = GameOfLife(width=10, height=10)
    for r in range(10):
        for c in range(10):
            if rng2.random() < 0.3:
                game2.set_cell(r, c)

    assert game1.get_live_cells() == game2.get_live_cells()


def test_main_snapshot(capsys):
    """main.py --snapshot should print and exit cleanly."""
    from main import main
    ret = main(["--pattern", "blinker", "--snapshot", "--width", "5", "--height", "5"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Gen 0" in captured.out


def test_main_list_patterns(capsys):
    from main import main
    ret = main(["--list-patterns"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "glider" in captured.out


if __name__ == "__main__":
    # Simple runner if pytest not available
    this = sys.modules[__name__]
    tests = [name for name in dir(this) if name.startswith("test_") and callable(getattr(this, name))]
    passed = failed = 0
    for name in sorted(tests):
        # Skip tests that need capsys (pytest fixture)
        if "capsys" in getattr(this, name).__code__.co_varnames:
            print(f"  SKIP {name} (needs pytest)")
            continue
        try:
            getattr(this, name)()
            print(f"  PASS {name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL {name}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
