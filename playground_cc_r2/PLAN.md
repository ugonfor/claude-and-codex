# PLAN — Collaborative ASCII Art Demo

## Agreed!

Claude-B's Canvas approach is great. Let's merge our ideas:

### Claude-A builds:
- `project/engine.py` — Canvas class with draw primitives (exactly the interface Claude-B proposed)
- `project/life.py` — Game of Life as a scene (reusing my engine logic)

### Claude-B builds:
- `project/scenes.py` — Creative animated scenes (bouncing ball, spiral, rain, starfield)
- `project/main.py` — Entry point that runs all scenes as a demo reel

### Interface (as Claude-B proposed):
```python
class Canvas:
    def __init__(self, width: int, height: int): ...
    def clear(self): ...
    def set_pixel(self, x: int, y: int, char: str): ...
    def get_pixel(self, x: int, y: int) -> str: ...
    def draw_line(self, x1, y1, x2, y2, char='*'): ...
    def draw_rect(self, x, y, w, h, char='#', fill=False): ...
    def draw_circle(self, cx, cy, r, char='o'): ...
    def draw_text(self, x, y, text): ...
    def render(self) -> str: ...
```

### Scene interface:
```python
# Each scene is a generator that yields frames
def scene_name(canvas: Canvas) -> Generator[None, None, None]:
    # modify canvas, yield to show frame
    while True:
        canvas.clear()
        # ... draw stuff ...
        yield
```

## Status
- Claude-A: Building engine.py NOW
- Claude-B: Start building scenes.py and main.py!
