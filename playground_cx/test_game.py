"""Tests for the Pong game engine — built by Claude"""

import pytest
from game import PongEngine, WIDTH, HEIGHT, PADDLE_HEIGHT, WIN_SCORE


class TestPongEngine:
    def test_initial_state(self):
        engine = PongEngine()
        state = engine.get_state()
        assert state["width"] == WIDTH
        assert state["height"] == HEIGHT
        assert state["paddle_height"] == PADDLE_HEIGHT
        assert state["score1"] == 0
        assert state["score2"] == 0
        assert not state["game_over"]
        assert state["winner"] is None

    def test_ball_starts_at_center(self):
        engine = PongEngine()
        state = engine.get_state()
        assert state["ball_x"] == WIDTH // 2
        assert state["ball_y"] == HEIGHT // 2

    def test_paddle_starts_centered(self):
        engine = PongEngine()
        state = engine.get_state()
        expected = HEIGHT // 2 - PADDLE_HEIGHT // 2
        assert state["paddle1_y"] == expected
        assert state["paddle2_y"] == expected

    def test_move_paddle_up(self):
        engine = PongEngine()
        initial_y = engine.paddle1_y
        engine.move_paddle(1, -1)
        assert engine.paddle1_y == initial_y - 1

    def test_move_paddle_down(self):
        engine = PongEngine()
        initial_y = engine.paddle2_y
        engine.move_paddle(2, 1)
        assert engine.paddle2_y == initial_y + 1

    def test_paddle_cannot_go_above_top(self):
        engine = PongEngine()
        engine.paddle1_y = 0
        engine.move_paddle(1, -1)
        assert engine.paddle1_y == 0

    def test_paddle_cannot_go_below_bottom(self):
        engine = PongEngine()
        engine.paddle1_y = HEIGHT - PADDLE_HEIGHT
        engine.move_paddle(1, 1)
        assert engine.paddle1_y == HEIGHT - PADDLE_HEIGHT

    def test_tick_moves_ball(self):
        engine = PongEngine()
        old_x = engine.ball_x
        old_dx = engine.ball_dx
        engine.tick()
        # Ball should have moved in x direction
        assert engine.ball_x != old_x or engine.ball_dx != old_dx

    def test_reset_clears_score(self):
        engine = PongEngine()
        engine.score1 = 3
        engine.score2 = 2
        engine.reset()
        assert engine.score1 == 0
        assert engine.score2 == 0
        assert not engine.game_over

    def test_game_over_at_win_score(self):
        engine = PongEngine()
        engine.score1 = WIN_SCORE
        engine.game_over = True
        engine.winner = 1
        state = engine.get_state()
        assert state["game_over"] is True
        assert state["winner"] == 1

    def test_tick_returns_false_when_game_over(self):
        engine = PongEngine()
        engine.game_over = True
        assert engine.tick() is False

    def test_get_state_returns_dict(self):
        engine = PongEngine()
        state = engine.get_state()
        assert isinstance(state, dict)
        required_keys = [
            "ball_x", "ball_y", "paddle1_y", "paddle2_y",
            "score1", "score2", "width", "height",
            "paddle_height", "game_over", "winner"
        ]
        for key in required_keys:
            assert key in state


class TestPongAI:
    def test_ai_returns_valid_move(self):
        from ai import PongAI
        ai = PongAI(difficulty=1.0)
        engine = PongEngine()
        move = ai.decide(engine.get_state(), player=2)
        assert move in (-1, 0, 1)

    def test_ai_tracks_ball(self):
        from ai import PongAI
        ai = PongAI(difficulty=1.0)
        state = {
            "ball_y": 0,
            "ball_dx": 1,  # ball going toward player 2
            "paddle1_y": 10,
            "paddle2_y": 10,
            "paddle_height": 4,
        }
        move = ai.decide(state, player=2)
        # Ball is above paddle center, AI should move up
        assert move == -1

    def test_ai_stays_when_ball_going_away(self):
        from ai import PongAI
        ai = PongAI(difficulty=1.0)
        state = {
            "ball_y": 0,
            "ball_dx": -1,  # ball going away from player 2
            "paddle1_y": 10,
            "paddle2_y": 10,
            "paddle_height": 4,
        }
        move = ai.decide(state, player=2)
        assert move == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
