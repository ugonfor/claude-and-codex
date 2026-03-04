# DONE
Built a terminal-based Conway's Game of Life simulator.

What I implemented:
- `patterns.py`: pattern library (glider, blinker, toad, beacon, pulsar, glider_gun).
- `renderer.py`: ANSI terminal renderer with generation counter.

Integration notes:
- `main.py`, `game.py`, `test_game.py` were created by the other agent; my files align with their API.

Tests run:
- `python -m pytest -q`