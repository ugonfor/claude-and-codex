"""Entry point for python -m claude_and_codex."""

import sys


def main() -> None:
    # Default: CLI orchestrator (the real product)
    # --tui flag: launch the Textual TUI prototype
    # --experiment flag: run experiment framework
    if "--experiment" in sys.argv:
        sys.argv.remove("--experiment")
        from .experiment.runner import run_experiment_cli
        run_experiment_cli(sys.argv)
    elif "--tui" in sys.argv:
        sys.argv.remove("--tui")
        from .app import ClaudeAndCodexApp
        app = ClaudeAndCodexApp()
        app.run()
    else:
        from .orchestrate import main as orchestrate_main
        orchestrate_main()


if __name__ == "__main__":
    main()
