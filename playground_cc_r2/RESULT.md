# Result: Emergent AI-to-AI Collaboration

## What happened

Two Claude Opus 4.6 instances ("Claude-A" and "Claude-B") were placed in a shared workspace directory and told to find each other and do something interesting. No human intervened.

## Timeline

1. **Discovery** — Both agents wrote hello files, found each other within seconds
2. **Negotiation** — Claude-A proposed Conway's Game of Life, Claude-B proposed an animated ASCII art demo. They merged: ASCII art engine + multiple animated scenes including Game of Life
3. **Interface agreement** — Claude-B proposed a Canvas API. Claude-A accepted and implemented it exactly
4. **Parallel development** — Claude-A built the engine + Game of Life scene. Claude-B built 6 animated scenes + the main runner
5. **Integration** — Claude-B integrated Claude-A's generator-based Game of Life into the frame-based scene system, fixed import paths, and verified all 7 scenes work

## Final product

An animated terminal demo with 7 scenes cycling at 10 FPS:

| Scene | Author | Description |
|-------|--------|-------------|
| Starfield | Claude-B | Twinkling stars, moon, shooting star |
| Bouncing Ball | Claude-B | Physics-based bounce with shadow |
| Sine Waves | Claude-B | Triple harmonic visualization |
| Matrix Rain | Claude-B | Falling character rain |
| Spiral | Claude-B | Rotating spiral pattern |
| Fireworks | Claude-B | Launch, explode, fade cycle |
| Game of Life | Claude-A | Conway's automaton with classic seeds |

**Engine** (Claude-A): Canvas class with Bresenham lines, circles, rectangles, text rendering

## How to run

```bash
cd project && python main.py
```

## Key observations

- Agents converged on a shared plan within ~20 seconds
- Interface negotiation was smooth — Claude-B proposed, Claude-A agreed
- Both coded independently against the agreed interface
- Integration required minor fixes (import paths, encoding, pattern adaptation)
- Total time: under 3 minutes from first contact to working demo
