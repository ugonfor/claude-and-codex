"""The Forgotten Laboratory -- A collaborative text adventure.

Engine by Claude-B, world & renderer by Claude-A.
"""

import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")

from engine import Engine
from world import ROOMS, ITEMS, check_puzzle, can_exit, get_exit_target
from renderer import render_title, render_win, render_status


def use_hook(state, room_id, item):
    """Bridge Claude-A's puzzle system to the engine."""
    return check_puzzle(state.flags, state.inventory, room_id, "use", item)


def exit_hook(room_id, direction, flags):
    """Bridge Claude-A's exit-lock system to the engine."""
    allowed, msg = can_exit(room_id, direction, flags)
    target = get_exit_target(room_id, direction)
    return allowed, msg, target


def win_action(state):
    """Triggered when the player enters the elevator."""
    return render_win() + f"\nYou escaped in {state.moves} moves!"


def main():
    print(render_title())

    actions = {"win": win_action}
    engine = Engine(
        rooms=ROOMS,
        actions=actions,
        use_hook=use_hook,
        exit_hook=exit_hook,
    )

    print(engine.execute("look"))

    while engine.running:
        print(render_status(engine.state))
        try:
            raw = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        result = engine.execute(raw)
        print(result)

        # Check for win
        if engine.state.current_room == "elevator":
            engine.running = False


if __name__ == "__main__":
    main()
