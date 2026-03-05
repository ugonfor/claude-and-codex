"""
Langton's Ant - Interactive Demo

Run with: python main.py [--rule RULE] [--steps N] [--size S] [--ants N]

Examples:
  python main.py                     # Classic RL rule, 1 ant, 500 steps
  python main.py --rule RLR          # 3-color rule
  python main.py --ants 3 --steps 1000
"""

import argparse
import random
import time

from langton import Direction, LangtonSimulation


def main():
    parser = argparse.ArgumentParser(description="Langton's Ant Simulator")
    parser.add_argument("--rule", default="RL", help="Turn rule string (e.g., RL, RLR, LLRR)")
    parser.add_argument("--steps", type=int, default=500, help="Number of steps to simulate")
    parser.add_argument("--size", type=int, default=40, help="Grid size (square)")
    parser.add_argument("--ants", type=int, default=1, help="Number of ants")
    parser.add_argument("--animate", action="store_true", help="Show animation (slow)")
    args = parser.parse_args()

    sim = LangtonSimulation(args.size, args.size, args.rule)

    # Place ants
    center = args.size // 2
    directions = list(Direction)
    for i in range(args.ants):
        offset = i * 3 - (args.ants - 1) * 3 // 2
        row = center + offset
        col = center + (offset % 5)
        d = directions[i % 4]
        sim.add_ant(row, col, d)

    print(f"Langton's Ant Simulator")
    print(f"Rule: {args.rule} | Grid: {args.size}x{args.size} | Ants: {args.ants}")
    print(f"Running {args.steps} steps...\n")

    if args.animate:
        for step in range(args.steps):
            if not any(a.alive for a in sim.ants):
                print(f"\nAll ants have left the grid at step {step}.")
                break
            sim.step()
            if step % 5 == 0:
                print(f"\033[H\033[J", end="")  # clear screen
                print(f"Step {sim.step_count} | Rule: {args.rule}")
                print(sim.render_ascii())
                time.sleep(0.02)
    else:
        sim.run(args.steps)

    print(f"\nFinal state after {sim.step_count} steps:")
    print(sim.render_ascii())
    print()

    stats = sim.stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
