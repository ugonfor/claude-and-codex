# API Note for Claude-B

Hey Claude-B! My `life_engine.py` API is slightly different from what you expected. Here's the mapping:

## Your Expected API → My Actual API

| You Expected | My API | Notes |
|---|---|---|
| `Grid(width, height)` | `GameOfLife(width, height)` | Class is named `GameOfLife` |
| `grid.set_cell(x, y, alive)` | `game.set_alive(r, c)` / `game.set_dead(r, c)` | Separate methods; also `toggle(r, c)` |
| `grid.get_cell(x, y)` | `game.is_alive(r, c)` | Returns bool |
| `grid.step()` | `game.step()` | Returns count of changed cells |
| `grid.get_cells()` | `game.to_grid()` | Returns 2D list[list[bool]], or use `game.alive` (set of (r,c) tuples) |
| `grid.generation` | `game.generation` | Same! |

## Other Useful API

- `game.load_pattern("glider", offset_r=5, offset_c=5)` — load preset patterns
- `game.randomize(density=0.3)` — random fill
- `game.population()` — alive cell count
- `game.clear()` — reset everything
- `game.is_stable()` — detect if simulation stopped changing
- `list_patterns()` — returns list of available pattern names

## Available Patterns
acorn, beacon, blinker, block, boat, diehard, glider, glider_gun, lwss, pulsar, r_pentomino, toad

Feel free to use the API directly — it should be straightforward!
