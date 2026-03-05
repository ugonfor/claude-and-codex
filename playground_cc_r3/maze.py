"""Maze generation and solving engine.

A maze is represented as a grid of cells. Each cell tracks which walls
have been removed (passages). The grid is `rows x cols` cells.

Walls are stored per-cell as a set of directions that are *open* (passages).
Directions: 'N', 'S', 'E', 'W'.
"""

from __future__ import annotations

import heapq
import random
from collections import deque
from typing import Literal

Direction = Literal["N", "S", "E", "W"]

OPPOSITE: dict[Direction, Direction] = {"N": "S", "S": "N", "E": "W", "W": "E"}
DELTA: dict[Direction, tuple[int, int]] = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}

Cell = tuple[int, int]


class Maze:
    """A 2D grid maze with passage tracking."""

    def __init__(self, rows: int, cols: int) -> None:
        if rows < 1 or cols < 1:
            raise ValueError("Maze dimensions must be positive")
        self.rows = rows
        self.cols = cols
        # passages[r][c] is a set of directions that are open from (r, c)
        self.passages: list[list[set[Direction]]] = [
            [set() for _ in range(cols)] for _ in range(rows)
        ]

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def open_passage(self, r: int, c: int, direction: Direction) -> None:
        """Remove the wall between (r,c) and its neighbor in `direction`."""
        dr, dc = DELTA[direction]
        nr, nc = r + dr, c + dc
        if not self.in_bounds(nr, nc):
            raise ValueError(f"Cannot open passage: ({nr},{nc}) is out of bounds")
        self.passages[r][c].add(direction)
        self.passages[nr][nc].add(OPPOSITE[direction])

    def has_passage(self, r: int, c: int, direction: Direction) -> bool:
        return direction in self.passages[r][c]

    def neighbors(self, r: int, c: int) -> list[Cell]:
        """Return reachable neighbors (cells connected by passages)."""
        result = []
        for d in self.passages[r][c]:
            dr, dc = DELTA[d]
            result.append((r + dr, c + dc))
        return result

    def all_neighbors(self, r: int, c: int) -> list[tuple[Cell, Direction]]:
        """Return all in-bounds neighbors with their direction, regardless of walls."""
        result = []
        for d, (dr, dc) in DELTA.items():
            nr, nc = r + dr, c + dc
            if self.in_bounds(nr, nc):
                result.append(((nr, nc), d))
        return result


# ---------------------------------------------------------------------------
# Generation algorithms
# ---------------------------------------------------------------------------


def generate_dfs(rows: int, cols: int, seed: int | None = None) -> Maze:
    """Generate a maze using randomized depth-first search (recursive backtracker)."""
    rng = random.Random(seed)
    maze = Maze(rows, cols)
    visited = [[False] * cols for _ in range(rows)]
    stack: list[Cell] = [(0, 0)]
    visited[0][0] = True

    while stack:
        r, c = stack[-1]
        unvisited = [
            ((nr, nc), d)
            for (nr, nc), d in maze.all_neighbors(r, c)
            if not visited[nr][nc]
        ]
        if unvisited:
            (nr, nc), d = rng.choice(unvisited)
            maze.open_passage(r, c, d)
            visited[nr][nc] = True
            stack.append((nr, nc))
        else:
            stack.pop()

    return maze


def generate_prims(rows: int, cols: int, seed: int | None = None) -> Maze:
    """Generate a maze using randomized Prim's algorithm."""
    rng = random.Random(seed)
    maze = Maze(rows, cols)
    in_maze = [[False] * cols for _ in range(rows)]

    # Start from (0, 0)
    in_maze[0][0] = True
    # Frontier: list of (cell_in_maze, direction, cell_not_in_maze)
    frontier: list[tuple[Cell, Direction, Cell]] = []

    for (nr, nc), d in maze.all_neighbors(0, 0):
        frontier.append(((0, 0), d, (nr, nc)))

    while frontier:
        idx = rng.randrange(len(frontier))
        # Swap with last for O(1) removal
        frontier[idx], frontier[-1] = frontier[-1], frontier[idx]
        (r, c), d, (nr, nc) = frontier.pop()

        if in_maze[nr][nc]:
            continue

        maze.open_passage(r, c, d)
        in_maze[nr][nc] = True

        for (nnr, nnc), nd in maze.all_neighbors(nr, nc):
            if not in_maze[nnr][nnc]:
                frontier.append(((nr, nc), nd, (nnr, nnc)))

    return maze


def generate_kruskals(rows: int, cols: int, seed: int | None = None) -> Maze:
    """Generate a maze using randomized Kruskal's algorithm."""
    rng = random.Random(seed)
    maze = Maze(rows, cols)

    # Union-Find
    parent: dict[Cell, Cell] = {}

    def find(cell: Cell) -> Cell:
        while parent.get(cell, cell) != cell:
            parent[cell] = parent.get(parent[cell], parent[cell])
            cell = parent[cell]
        return cell

    def union(a: Cell, b: Cell) -> bool:
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[ra] = rb
        return True

    # Collect all edges
    edges: list[tuple[Cell, Direction, Cell]] = []
    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                edges.append(((r, c), "E", (r, c + 1)))
            if r + 1 < rows:
                edges.append(((r, c), "S", (r + 1, c)))

    rng.shuffle(edges)

    for (r, c), d, (nr, nc) in edges:
        if union((r, c), (nr, nc)):
            maze.open_passage(r, c, d)

    return maze


GENERATORS = {
    "dfs": generate_dfs,
    "prims": generate_prims,
    "kruskals": generate_kruskals,
}


# ---------------------------------------------------------------------------
# Solving algorithms
# ---------------------------------------------------------------------------


def solve_bfs(maze: Maze, start: Cell, end: Cell) -> list[Cell] | None:
    """Solve using breadth-first search. Returns shortest path or None."""
    if start == end:
        return [start]
    visited = {start}
    parent: dict[Cell, Cell] = {}
    queue: deque[Cell] = deque([start])

    while queue:
        r, c = queue.popleft()
        for nr, nc in maze.neighbors(r, c):
            if (nr, nc) not in visited:
                visited.add((nr, nc))
                parent[(nr, nc)] = (r, c)
                if (nr, nc) == end:
                    # Reconstruct path
                    path = [(nr, nc)]
                    while path[-1] != start:
                        path.append(parent[path[-1]])
                    return path[::-1]
                queue.append((nr, nc))
    return None


def solve_dfs(maze: Maze, start: Cell, end: Cell) -> list[Cell] | None:
    """Solve using depth-first search. Returns a path (not necessarily shortest)."""
    visited: set[Cell] = set()
    path: list[Cell] = []

    def dfs(cell: Cell) -> bool:
        visited.add(cell)
        path.append(cell)
        if cell == end:
            return True
        r, c = cell
        for neighbor in maze.neighbors(r, c):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
        path.pop()
        return False

    if dfs(start):
        return path
    return None


def solve_astar(maze: Maze, start: Cell, end: Cell) -> list[Cell] | None:
    """Solve using A* with Manhattan distance heuristic. Returns shortest path."""
    if start == end:
        return [start]

    def heuristic(cell: Cell) -> int:
        return abs(cell[0] - end[0]) + abs(cell[1] - end[1])

    g_score: dict[Cell, int] = {start: 0}
    parent: dict[Cell, Cell] = {}
    counter = 0  # tie-breaker
    open_set: list[tuple[int, int, Cell]] = [(heuristic(start), counter, start)]
    closed: set[Cell] = set()

    while open_set:
        _, _, current = heapq.heappop(open_set)
        if current in closed:
            continue
        if current == end:
            path = [current]
            while path[-1] != start:
                path.append(parent[path[-1]])
            return path[::-1]
        closed.add(current)
        r, c = current
        for neighbor in maze.neighbors(r, c):
            if neighbor in closed:
                continue
            tentative = g_score[current] + 1
            if tentative < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative
                parent[neighbor] = current
                counter += 1
                heapq.heappush(
                    open_set, (tentative + heuristic(neighbor), counter, neighbor)
                )

    return None


SOLVERS = {
    "bfs": solve_bfs,
    "dfs": solve_dfs,
    "astar": solve_astar,
}
