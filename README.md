# claude-and-codex

A TUI coding agent where Claude (Anthropic) and Codex (OpenAI) collaborate freely on coding tasks.

## Setup

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
```

## Usage

```bash
# Set API keys (or use OAuth from CLI logins)
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...

# Run
python -m claude_and_codex
```

## Authentication

Supports two methods (tried in order):
1. **OAuth**: Reuse tokens from `claude` CLI and `codex` CLI logins
2. **API keys**: `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` environment variables
