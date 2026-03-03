"""Pong ASCII Renderer with ANSI colors — built by Claude"""

import os
import sys

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
WHITE = "\033[37m"
DIM = "\033[2m"


def clear_screen():
    """Clear the terminal screen using cursor home + clear."""
    sys.stdout.write("\033[H\033[J")


def render(state: dict):
    """Render the game state as colored ASCII art to the terminal."""
    w = state["width"]
    h = state["height"]
    ball_x = state["ball_x"]
    ball_y = state["ball_y"]
    p1_y = state["paddle1_y"]
    p2_y = state["paddle2_y"]
    ph = state["paddle_height"]
    s1 = state["score1"]
    s2 = state["score2"]

    lines = []

    # Title
    lines.append(f"{BOLD}{CYAN}{'= PONG =':^{w + 2}}{RESET}")

    # Score header
    p1_color = GREEN if s1 > s2 else WHITE
    p2_color = GREEN if s2 > s1 else WHITE
    header = f"  {p1_color}Player 1: {s1}{RESET}    {DIM}|{RESET}    {p2_color}Player 2: {s2}{RESET}  "
    lines.append(f"{header}")
    lines.append(f"{BLUE}+{'-' * w}+{RESET}")

    for y in range(h):
        row = [f"{BLUE}|{RESET}"]
        for x in range(w):
            if x == 0 and p1_y <= y < p1_y + ph:
                row.append(f"{GREEN}{BOLD}#{RESET}")
            elif x == w - 1 and p2_y <= y < p2_y + ph:
                row.append(f"{RED}{BOLD}#{RESET}")
            elif x == ball_x and y == ball_y:
                row.append(f"{YELLOW}{BOLD}O{RESET}")
            elif x == w // 2 and y % 2 == 0:
                row.append(f"{DIM}:{RESET}")
            else:
                row.append(" ")
        row.append(f"{BLUE}|{RESET}")
        lines.append("".join(row))

    lines.append(f"{BLUE}+{'-' * w}+{RESET}")
    lines.append(f"  {GREEN}P1: W/S{RESET}    {RED}P2: Up/Down{RESET}    {DIM}Q: Quit  R: Restart{RESET}")

    if state.get("game_over"):
        winner = state.get("winner", "?")
        color = GREEN if winner == 1 else RED
        lines.append("")
        lines.append(f"{BOLD}{color}{'>>> GAME OVER! Player ' + str(winner) + ' wins! <<<':^{w + 2}}{RESET}")
        lines.append(f"{DIM}{'Press Q to quit or R to restart.':^{w + 2}}{RESET}")

    clear_screen()
    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()
