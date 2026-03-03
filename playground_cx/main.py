"""Pong Main — wires together engine + renderer + input handling.
Built by Claude. Codex welcome to improve!

Usage:
    python main.py          # 2-player mode
    python main.py --ai     # play against AI
"""

import sys
import time

from game import PongEngine
from renderer import render
from ai import PongAI

# Cross-platform keyboard input
if sys.platform == "win32":
    import msvcrt

    def get_key():
        """Non-blocking key read on Windows."""
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch in (b"\x00", b"\xe0"):
                # Special key (arrows etc.)
                ch2 = msvcrt.getch()
                if ch2 == b"H":
                    return "UP"
                elif ch2 == b"P":
                    return "DOWN"
                else:
                    return None
            else:
                return ch.decode("utf-8", errors="ignore").lower()
        return None
else:
    import tty
    import termios
    import select

    _old_settings = None

    def _setup_terminal():
        global _old_settings
        _old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    def _restore_terminal():
        if _old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, _old_settings)

    def get_key():
        """Non-blocking key read on Unix."""
        if select.select([sys.stdin], [], [], 0)[0]:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                ch3 = sys.stdin.read(1)
                if ch3 == "A":
                    return "UP"
                elif ch3 == "B":
                    return "DOWN"
                return None
            return ch.lower()
        return None


TICK_RATE = 0.08  # seconds per game tick


def main():
    ai_mode = "--ai" in sys.argv
    engine = PongEngine()
    ai = PongAI(difficulty=0.6) if ai_mode else None

    if ai_mode:
        print("AI Mode: You are Player 1 (left). Use W/S keys.")
        time.sleep(1)

    if sys.platform != "win32":
        _setup_terminal()

    try:
        while True:
            # Handle input
            key = get_key()
            if key == "q":
                break
            elif key == "r":
                engine.reset()
            elif key == "w":
                engine.move_paddle(1, -1)
            elif key == "s":
                engine.move_paddle(1, 1)

            if ai_mode:
                # AI controls player 2
                if not engine.game_over:
                    move = ai.decide(engine.get_state(), player=2)
                    if move != 0:
                        engine.move_paddle(2, move)
            else:
                # Human controls player 2
                if key == "UP":
                    engine.move_paddle(2, -1)
                elif key == "DOWN":
                    engine.move_paddle(2, 1)

            # Tick the engine
            if not engine.game_over:
                engine.tick()

            # Render
            render(engine.get_state())

            time.sleep(TICK_RATE)

    except KeyboardInterrupt:
        pass
    finally:
        if sys.platform != "win32":
            _restore_terminal()
        print("\nThanks for playing!")


if __name__ == "__main__":
    main()
