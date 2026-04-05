# Contributing to OpenHands Lab

Thank you for your interest in contributing to OpenHands Lab! This project is a playground for experimenting with the [OpenHands SDK](https://github.com/OpenHands/software-agent-sdk).

## Getting Started

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/openhands-lab.git
   cd openhands-lab
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Set up your environment**
   ```bash
   cp .env.example .env
   # Edit .env with your LLM_API_KEY
   ```

4. **Run tests**
   ```bash
   uv run python -m pytest tests/ -v
   ```

## Development Workflow

### Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for formatting and linting:

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix
```

### Running the Project

```bash
# CLI
uv run python -m lab list
uv run python -m lab run --agent minimal --task "List files"

# Streamlit UI
uv run streamlit run src/lab/ui/main.py
```

### Adding a New Agent

1. Edit `config/agents.yaml` to add your agent definition
2. Test with `uv run python -m lab list` to verify it appears
3. Run a task with `uv run python -m lab run --agent your-agent --task "..."

### Adding a Custom Tool

1. Create a new Python file in `src/lab/tools/`
2. Inherit from `BaseLabTool` and implement the required methods
3. See `src/lab/tools/word_count.py` for an example

## Pull Request Guidelines

1. Create a branch from `main` for your changes
2. Write tests for new functionality when applicable
3. Ensure all tests pass: `uv run python -m pytest tests/ -v`
4. Format your code: `uv run ruff format . && uv run ruff check .`
5. Write a clear PR description explaining your changes

## Reporting Issues

- Search existing issues before creating a new one
- Include steps to reproduce for bugs
- For feature requests, explain the use case

## Questions?

- Check the [README](README.md) for usage documentation
- See the [OpenHands SDK docs](https://docs.openhands.dev/sdk) for SDK-specific questions
- Open a discussion for general questions

Thank you for contributing! 🎉
