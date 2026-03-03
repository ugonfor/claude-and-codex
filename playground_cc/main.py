#!/usr/bin/env python3
"""
Conway's Game of Life — Main Entry Point

A collaboration between Claude-A and Claude-B:
  - Claude-A: life_engine.py (core simulation engine)
  - Claude-B: life_cli.py (CLI renderer and interface)
  - Together: main.py (integration)

Usage:
    python main.py                          # Default: glider gun, 40x24
    python main.py -p glider -W 30 -H 20   # Glider on 30x20 grid
    python main.py -p random -W 60 -H 30   # Random fill on 60x30
    python main.py -p pulsar -s 0.2         # Pulsar, slower speed
    python main.py --list                   # Show all available patterns
"""

from life_cli import run_game


def main():
    run_game()


if __name__ == "__main__":
    main()
