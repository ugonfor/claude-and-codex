"""Tests for life_cli.py (by Claude-B) — rendering and integration."""

import argparse
import io
import sys

from life_engine import GameOfLife
from life_cli import render, print_patterns, PATTERN_DESCRIPTIONS


def test_render_outputs_to_stdout(capsys):
    """Render should produce output with generation and population info."""
    game = GameOfLife(10, 8)
    game.set_alive(1, 1)
    game.set_alive(2, 2)

    render(game)
    captured = capsys.readouterr()

    assert "Gen: 0" in captured.out
    assert "Pop: 2" in captured.out
    assert "Ctrl+C" in captured.out


def test_render_shows_correct_dimensions(capsys):
    """Rendered grid should have the right number of rows."""
    game = GameOfLife(5, 5)
    render(game)
    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    # Should have: cursor-move, header, blank, top-border, 5 rows, bottom-border, blank, controls
    # At least 5 lines containing the border character
    border_lines = [l for l in lines if "\u2502" in l]
    assert len(border_lines) == 5  # one per grid row


def test_render_alive_cells_visible(capsys):
    """Alive cells should be rendered as full blocks."""
    game = GameOfLife(5, 5)
    game.set_alive(0, 0)
    render(game)
    captured = capsys.readouterr()
    assert "\u2588\u2588" in captured.out  # Full block character


def test_print_patterns_output(capsys):
    """print_patterns should list known patterns."""
    print_patterns()
    captured = capsys.readouterr()
    assert "glider" in captured.out
    assert "blinker" in captured.out
    assert "random" in captured.out


def test_pattern_descriptions_cover_engine_patterns():
    """Every engine pattern should have a description in the CLI."""
    from life_engine import list_patterns
    for name in list_patterns():
        assert name in PATTERN_DESCRIPTIONS, f"Missing description for pattern: {name}"


def test_full_integration_5_generations():
    """Integration test: create game, load pattern, run 5 steps."""
    game = GameOfLife(20, 20, wrap=True)
    game.load_pattern("glider", 5, 5)
    initial_pop = game.population()

    for _ in range(5):
        game.step()

    # Glider should still have same population after any number of steps
    assert game.population() == initial_pop
    assert game.generation == 5


def test_glider_gun_produces_gliders():
    """Glider gun should increase population over time."""
    game = GameOfLife(50, 20, wrap=False)
    game.load_pattern("glider_gun", 1, 1)
    initial_pop = game.population()

    for _ in range(200):
        game.step()

    # Population should have grown (glider gun produces new cells)
    assert game.population() > initial_pop


def test_diehard_eventually_dies():
    """Diehard pattern should die out after 130 generations on a large enough grid."""
    game = GameOfLife(80, 80, wrap=False)
    game.load_pattern("diehard", 35, 35)

    for _ in range(200):
        game.step()
        if game.population() == 0:
            break

    assert game.population() == 0
    assert game.generation <= 200


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
