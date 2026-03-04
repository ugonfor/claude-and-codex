"""Terminal Maze Generator & Solver — CLI entry point."""

import argparse
import sys
import time

from maze import Maze


def main():
    parser = argparse.ArgumentParser(description="Terminal Maze Generator & Solver")
    parser.add_argument("-W", "--width", type=int, default=10, help="Maze width in cells (default: 10)")
    parser.add_argument("-H", "--height", type=int, default=10, help="Maze height in cells (default: 10)")
    parser.add_argument("-a", "--algorithm", choices=["backtracker", "prims"], default="backtracker",
                        help="Generation algorithm (default: backtracker)")
    parser.add_argument("-s", "--solver", choices=["bfs", "dfs", "astar", "none"], default="bfs",
                        help="Solving algorithm (default: bfs)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--no-solve", action="store_true", help="Show maze without solution")
    parser.add_argument("--animate", action="store_true", help="Animate the solving process")
    parser.add_argument("--delay", type=float, default=0.05, help="Animation delay in seconds (default: 0.05)")
    args = parser.parse_args()

    # Generate maze
    maze = Maze(args.width, args.height, seed=args.seed)
    maze.generate(args.algorithm)

    print(f"Maze {args.width}x{args.height} (algorithm: {args.algorithm})")

    # Try to import Codex's modules
    try:
        from renderer import render
        has_renderer = True
    except ImportError:
        has_renderer = False

    try:
        from solver import solve
        has_solver = True
    except ImportError:
        has_solver = False

    # Solve
    path = None
    if not args.no_solve and args.solver != "none" and has_solver:
        t0 = time.time()
        path = solve(maze.grid, maze.start, maze.end, args.solver)
        elapsed = time.time() - t0
        if path:
            print(f"Solved with {args.solver.upper()} — path length: {len(path)}, time: {elapsed:.4f}s")
        else:
            print(f"No solution found with {args.solver.upper()}")
    elif not has_solver and not args.no_solve:
        print("(solver.py not available — showing unsolved maze)")

    # Render
    if has_renderer:
        output = render(maze.grid, path)
        print(output)
    else:
        # Fallback renderer
        print(_fallback_render(maze.grid, path, maze.start, maze.end))


def _fallback_render(grid, path, start, end):
    """Simple fallback renderer if Codex's renderer.py isn't available."""
    path_set = set(path) if path else set()
    lines = []
    for r, row in enumerate(grid):
        line = []
        for c, cell in enumerate(row):
            pos = (r, c)
            if pos == start:
                line.append("S")
            elif pos == end:
                line.append("E")
            elif pos in path_set:
                line.append(".")
            elif cell == 1:
                line.append("#")
            else:
                line.append(" ")
        lines.append("".join(line))
    return "\n".join(lines)


if __name__ == "__main__":
    main()
