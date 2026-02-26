#!/bin/bash
cd "$(dirname "$0")"
.venv/bin/python -m claude_and_codex.orchestrate "$@"
