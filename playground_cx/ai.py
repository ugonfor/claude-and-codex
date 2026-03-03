"""Simple AI opponent for Pong — built by Claude"""

import random


class PongAI:
    """AI that controls a paddle by tracking the ball with some imperfection."""

    def __init__(self, difficulty: float = 0.7):
        """
        difficulty: 0.0 (easy/random) to 1.0 (perfect tracking).
        """
        self.difficulty = max(0.0, min(1.0, difficulty))
        self.reaction_delay = 0  # ticks until AI reacts

    def decide(self, state: dict, player: int = 2) -> int:
        """Return -1 (up), 0 (stay), or 1 (down) for the given player's paddle."""
        ball_y = state["ball_y"]
        ball_dx = state["ball_dx"]
        paddle_y = state[f"paddle{player}_y"]
        ph = state["paddle_height"]
        paddle_center = paddle_y + ph // 2

        # Only react when ball is coming toward this paddle
        if player == 2 and ball_dx < 0:
            return 0  # Ball going away, don't move
        if player == 1 and ball_dx > 0:
            return 0

        # Sometimes make mistakes based on difficulty
        if random.random() > self.difficulty:
            return random.choice([-1, 0, 1])

        # Track the ball
        if ball_y < paddle_center - 1:
            return -1
        elif ball_y > paddle_center + 1:
            return 1
        return 0
