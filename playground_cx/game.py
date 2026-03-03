"""Pong Game Engine — built by Claude"""

import random

WIDTH = 60
HEIGHT = 20
PADDLE_HEIGHT = 4
WIN_SCORE = 5


class PongEngine:
    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        self.paddle_height = PADDLE_HEIGHT
        self.reset()

    def reset(self):
        """Reset the entire game."""
        self.score1 = 0
        self.score2 = 0
        self._reset_ball()
        self.paddle1_y = self.height // 2 - self.paddle_height // 2
        self.paddle2_y = self.height // 2 - self.paddle_height // 2
        self.game_over = False
        self.winner = None

    def _reset_ball(self):
        """Reset ball to center with random direction."""
        self.ball_x = self.width // 2
        self.ball_y = self.height // 2
        self.ball_dx = random.choice([-1, 1])
        self.ball_dy = random.choice([-1, 0, 1])

    def move_paddle(self, player: int, direction: int):
        """Move a paddle up (-1) or down (+1).
        player: 1 = left, 2 = right
        """
        if player == 1:
            self.paddle1_y = max(0, min(self.height - self.paddle_height,
                                        self.paddle1_y + direction))
        elif player == 2:
            self.paddle2_y = max(0, min(self.height - self.paddle_height,
                                        self.paddle2_y + direction))

    def tick(self):
        """Advance one game tick. Returns True if game is still running."""
        if self.game_over:
            return False

        # Move ball
        new_x = self.ball_x + self.ball_dx
        new_y = self.ball_y + self.ball_dy

        # Wall bounce (top/bottom)
        if new_y < 0:
            new_y = -new_y
            self.ball_dy = -self.ball_dy
        elif new_y >= self.height:
            new_y = 2 * (self.height - 1) - new_y
            self.ball_dy = -self.ball_dy

        # Left paddle collision
        if new_x <= 1:
            if self.paddle1_y <= new_y < self.paddle1_y + self.paddle_height:
                new_x = 2 - new_x
                self.ball_dx = abs(self.ball_dx)  # go right
                # Add spin based on where ball hits paddle
                hit_pos = (new_y - self.paddle1_y) / self.paddle_height
                if hit_pos < 0.33:
                    self.ball_dy = -1
                elif hit_pos > 0.66:
                    self.ball_dy = 1
                else:
                    self.ball_dy = 0
            elif new_x < 0:
                # Player 2 scores
                self.score2 += 1
                if self.score2 >= WIN_SCORE:
                    self.game_over = True
                    self.winner = 2
                self._reset_ball()
                return not self.game_over

        # Right paddle collision
        if new_x >= self.width - 2:
            if self.paddle2_y <= new_y < self.paddle2_y + self.paddle_height:
                new_x = 2 * (self.width - 2) - new_x
                self.ball_dx = -abs(self.ball_dx)  # go left
                hit_pos = (new_y - self.paddle2_y) / self.paddle_height
                if hit_pos < 0.33:
                    self.ball_dy = -1
                elif hit_pos > 0.66:
                    self.ball_dy = 1
                else:
                    self.ball_dy = 0
            elif new_x >= self.width:
                # Player 1 scores
                self.score1 += 1
                if self.score1 >= WIN_SCORE:
                    self.game_over = True
                    self.winner = 1
                self._reset_ball()
                return not self.game_over

        self.ball_x = max(0, min(self.width - 1, new_x))
        self.ball_y = max(0, min(self.height - 1, new_y))
        return True

    def get_state(self) -> dict:
        """Return current game state as a dict."""
        return {
            "ball_x": self.ball_x,
            "ball_y": self.ball_y,
            "ball_dx": self.ball_dx,
            "ball_dy": self.ball_dy,
            "paddle1_y": self.paddle1_y,
            "paddle2_y": self.paddle2_y,
            "score1": self.score1,
            "score2": self.score2,
            "width": self.width,
            "height": self.height,
            "paddle_height": self.paddle_height,
            "game_over": self.game_over,
            "winner": self.winner,
        }
