# OpenHands SDK Playground

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

OpenHands SDK Playground is a local-first workspace for exploring the [OpenHands SDK](https://github.com/OpenHands/software-agent-sdk). It gives you a ready-made codebase where they can load up the SDK, run agents, tweak prompts and tools, and quickly see how those changes affect behavior.

Instead of starting from a blank project, you can use OpenHands SDK Playground as a hackable place to experiment with agent "Personalities" (prompts), "Capabilities" (custom tools), and runtime configuration in a working example.

**📚 New to the SDK?** Check out the [official SDK documentation](https://docs.openhands.dev/sdk) and [Getting Started Guide](https://docs.openhands.dev/sdk/getting-started).

## Features

- **SDK Playground**: A ready-made project for trying the OpenHands SDK without building everything from scratch
- **Agents**: Pre-configured agent personas with specific tools and system prompts
- **Dynamic Tools**: Add custom tools by dropping Python files in `src/lab/tools/`
- **Hot Reload**: Iterate on tools quickly while using the dashboard
- **Streamlit UI**: Visual dashboard for trying agents and toggling tools per run
- **Session Tracing**: Full event history saved so you can inspect what happened after each experiment
- **Safety Guards**: Command blacklisting and sandbox-oriented protection hooks

## SDK Examples

Use the `sdk-playground` agent to import examples from the [upstream SDK repository](https://github.com/OpenHands/software-agent-sdk/tree/main/examples) directly into `examples/sdk/`:

```bash
# List available SDK examples
uv run python -m lab run \
  --agent sdk-playground \
  --task "List the available SDK examples"

# Import the hello world example
uv run python -m lab run \
  --agent sdk-playground \
  --task "Import the hello world example into the playground"
```

Once imported, you can run examples directly:

```bash
uv run python examples/sdk/01_hello_world.py
```

This workflow teaches you to use the Lab's import tool while keeping examples fresh from the SDK.

---

## Table of Contents

- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Setup](#environment-setup)
  - [Quickstart in 5 Minutes](#quickstart-in-5-minutes)
- [Usage](#usage)
  - [CLI Commands](#cli-commands)
  - [Streamlit Dashboard](#streamlit-dashboard)
- [Configuration](#configuration)
  - [Environment Variables (.env)](#environment-variables-env)
  - [Agents (agents.yaml)](#agents-agentsyaml)
  - [Settings (settings.yaml)](#settings-settingsyaml)
- [Choosing a Use Case](#choosing-a-use-case)
- [Common User Journeys](#common-user-journeys)
- [How a Run Works](#how-a-run-works)
- [Custom Tools](#custom-tools)
- [Create Your Own Use Case](#create-your-own-use-case)
- [Project Structure](#project-structure)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Getting Started

### Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager
- **LLM API Key** - Either:
  - OpenHands subscription key (recommended)
  - Direct provider key (Anthropic, OpenAI, etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/OpenHands/openhands-lab.git
cd openhands-lab

# Install dependencies with uv
uv sync
```

### Environment Setup

1. **Copy the example environment file:**

   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your API credentials:**

   **For OpenHands subscription users (recommended):**
   ```env
   LLM_API_KEY=your-openhands-subscription-key
   LLM_MODEL=openhands/claude-sonnet-4-5-20250929
   ```

   **For direct Anthropic API users:**
   ```env
   LLM_API_KEY=sk-ant-api03-xxxxx
   LLM_MODEL=anthropic/claude-sonnet-4-5-20250929
   ```

   **For OpenAI users:**
   ```env
   LLM_API_KEY=sk-xxxxx
   LLM_MODEL=openai/gpt-4
   ```

3. **Verify your setup:**

   ```bash
   uv run python -m lab config
   ```

The `.env` file is automatically loaded when you run any lab command. It is excluded from version control via `.gitignore`.

### Quickstart in 5 Minutes

If your goal is to try the OpenHands SDK in a working playground as quickly as possible:

```bash
# 1. Install dependencies
uv sync

# 2. Create your environment file
cp .env.example .env

# 3. Add your LLM_API_KEY to .env

# 4. See what starter agents are available
uv run python -m lab list

# 5. Import and run the SDK hello world example
uv run python -m lab run \
  --agent sdk-playground \
  --task "Import the hello world example and explain how to run it"
```

Then keep exploring:

- Review the terminal output to see how the agent responded
- Inspect `.oh-lab/` to see the saved trace for that run
- Launch the dashboard with `uv run streamlit run src/lab/ui/main.py`
- Change the agent, edit the prompt, or toggle tools and compare results

---

## Usage

### CLI Commands

All commands are run with `uv run python -m lab` (or just `python -m lab` if your virtualenv is activated).

#### List Available Agents

```bash
uv run python -m lab list
```

Shows all configured agents with their descriptions and tools.

#### Show Current Configuration

```bash
uv run python -m lab config
```

Displays the current LLM model, runtime environment, and settings.

#### Run an Agent Task

```bash
uv run python -m lab run --agent <name> --task "<your task>"
```

**Examples:**

```bash
# Debug a CLI application
uv run python -m lab run --agent debug-cli --task "Find why my script crashes"

# Review code for security issues
uv run python -m lab run --agent auditor --task "Check for hardcoded secrets"

# List files with minimal agent
uv run python -m lab run --agent minimal --task "List all Python files"

# Specify a custom workspace directory
uv run python -m lab run --agent debug-cli --task "Analyze logs" --workspace /path/to/project
```

**CLI Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--agent` | `-a` | Name of the agent (from `agents.yaml`) |
| `--task` | `-t` | Task description for the agent |
| `--workspace` | `-w` | Working directory (default: current directory) |
| `--config-dir` | | Configuration directory (default: `config`) |

#### Get Help

```bash
uv run python -m lab --help
uv run python -m lab run --help
```

### Streamlit Dashboard

Launch the visual dashboard:

```bash
uv run streamlit run src/lab/ui/main.py
```

The dashboard provides:
- **Use Case Selection**: Choose from configured agent personas
- **Tool Toggles**: Enable/disable individual tools
- **Task Input**: Natural language task entry
- **Thought Stream**: Real-time view of agent reasoning
- **Workspace Browser**: See files in the working directory

**Dashboard URL:** http://localhost:8501 (default)

---

## Configuration

### Environment Variables (.env)

Create a `.env` file from `.env.example`. Environment variables override settings in YAML files.

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_API_KEY` | Yes | Your LLM API key |
| `LLM_MODEL` | No | Model to use (overrides `settings.yaml`) |
| `LLM_BASE_URL` | No | Custom API endpoint URL |
| `OPENHANDS_SUPPRESS_BANNER` | No | Set to `1` to hide SDK banner |

**Example `.env` file:**

```env
# Required
LLM_API_KEY=your-api-key-here

# Optional - Override default model
LLM_MODEL=openhands/claude-sonnet-4-5-20250929

# Optional - Suppress SDK banner
OPENHANDS_SUPPRESS_BANNER=1
```

**Model naming conventions:**
- OpenHands proxy: `openhands/model-name` (e.g., `openhands/claude-sonnet-4-5-20250929`)
- Anthropic direct: `anthropic/model-name` (e.g., `anthropic/claude-sonnet-4-5-20250929`)
- OpenAI direct: `openai/model-name` (e.g., `openai/gpt-4`)

### Agents (`config/agents.yaml`)

Define agent personas with specific tools and system prompts:

```yaml
agents:
  debug-cli:
    description: "Debug and troubleshoot CLI applications"
    system_prompt: |
      You are a debugging assistant specialized in CLI applications.
      Focus on identifying issues, suggesting fixes, and explaining
      the root cause of problems.
    tools:
      - terminal
      - file_editor
      - task_tracker
    model: null  # Optional: override the default model

  auditor:
    description: "Security auditor for finding vulnerabilities"
    system_prompt: |
      You are a security auditor. Find hardcoded secrets,
      identify vulnerabilities, and suggest secure alternatives.
    tools:
      - terminal
      - file_editor
      - task_tracker

  minimal:
    description: "Minimal agent with basic tools"
    tools:
      - terminal
```

**Available built-in tools:**
- `terminal` - Execute shell commands
- `file_editor` - View and edit files
- `task_tracker` - Track multi-step tasks

### Settings (`config/settings.yaml`)

Global LLM and runtime configuration:

```yaml
llm:
  model: "anthropic/claude-sonnet-4-5-20250929"
  api_key_env: "LLM_API_KEY"
  base_url: null
  temperature: 0.0
  max_tokens: 4096

runtime:
  environment: "local"  # "local" or "docker"
  working_dir: "."
  docker_image: null
  command_blacklist:
    - "rm -rf /"
    - "rm -rf /*"

session_log_dir: ".oh-lab"
```

**Configuration priority:**
1. Environment variables (`.env`)
2. Agent config (`agents.yaml`)
3. Global settings (`settings.yaml`)

---

## Choosing a Use Case

In this repo, agents are meant to be starter templates for experimentation. Pick the one closest to your task, run it, then tweak it.

| Agent | Best for | Default tools | Example task |
|----------|----------|---------------|--------------|
| `debug-cli` | Broken scripts, failing commands, log analysis | `terminal`, `file_editor`, `task_tracker` | `"Find why my script crashes on startup"` |
| `code-reviewer` | Quality reviews, bug hunting, best-practice checks | `terminal`, `file_editor` | `"Review this package for maintainability issues"` |
| `auditor` | Secret scanning and security-oriented reviews | `terminal`, `file_editor`, `task_tracker` | `"Check this repo for hardcoded credentials"` |
| `modernizer` | Refactors, typing, API upgrades | `terminal`, `file_editor`, `task_tracker` | `"Help modernize this module to current Python patterns"` |
| `sdk-playground` | Importing and trying upstream SDK examples inside this repo | `terminal`, `file_editor`, `github_fetcher`, `import_sdk_example` | `"Import the hello world SDK example into the playground"` |
| `minimal` | Low-overhead command execution | `terminal` | `"List all YAML files in this workspace"` |

As a rule of thumb:

- Choose `debug-cli` when the task involves reproducing and fixing behavior
- Choose `code-reviewer` when you want critique without a specialized security lens
- Choose `auditor` when the highest priority is risk reduction
- Choose `modernizer` when the goal is code transformation rather than diagnosis
- Choose `minimal` when you want the narrowest tool access and the simplest behavior

For new users, the important thing is not picking the perfect persona on the first try. The repo is designed so you can start with one, change the prompt or tools, and rerun quickly.

---

## Common User Journeys

These examples are meant to help a new user get hands-on with the SDK and learn by tweaking a working setup.

### Try a starter agent against this repo

```bash
uv run python -m lab run \
  --agent code-reviewer \
  --task "Review this repository and explain what it demonstrates about the OpenHands SDK"
```

This is a good first run because you can inspect the output, then immediately edit the agent prompt and compare the next run.

### Debug a local project

```bash
uv run python -m lab run \
  --agent debug-cli \
  --workspace /path/to/project \
  --task "Reproduce the failing CLI command, identify the root cause, and suggest a fix"
```

### Review a repository for quality issues

```bash
uv run python -m lab run \
  --agent code-reviewer \
  --workspace /path/to/repo \
  --task "Review the codebase for bugs, unclear design, and risky patterns"
```

### Audit for secrets and security concerns

```bash
uv run python -m lab run \
  --agent auditor \
  --workspace /path/to/repo \
  --task "Look for hardcoded secrets, insecure defaults, and dangerous shell usage"
```

### Modernize an older codebase

```bash
uv run python -m lab run \
  --agent modernizer \
  --workspace /path/to/repo \
  --task "Identify outdated patterns and propose a modernization plan"
```

### Use the dashboard instead of the CLI

```bash
uv run streamlit run src/lab/ui/main.py
```

Then:

1. Select a agent from the sidebar
2. Choose the workspace directory you want the agent to operate in
3. Enable or disable the tools you want available for that run
4. Enter a task in natural language
5. Review the thought stream and the saved trace after completion

The dashboard is the fastest way to treat the repo like a playground: run a task, toggle tools, change your workspace, and try again.

### Quickly run examples from the OpenHands Agent SDK

```bash
uv run python -m lab run \
  --agent sdk-playground \
  --task "Import the OpenHands SDK hello world example into the playground and explain how to run it"
```

This agent is designed for experimentation. It can fetch a fresh catalog of upstream SDK examples, install one into the local playground, and help the user understand what to tweak next.

---

## How a Run Works

For a new user, the simplest mental model is:

1. `settings.yaml` defines the default model and runtime settings
2. `agents.yaml` defines a persona, prompt, and tool set for a named agent
3. You start a session from the CLI or Streamlit UI
4. The session runs against a workspace directory
5. The agent response and event history are saved to `.oh-lab/`

This structure is intentionally simple so you can experiment with one layer at a time:

- Change the task to see how the same persona behaves on different instructions
- Change the agent prompt to see how the agent's behavior shifts
- Change the enabled tools to see what capabilities matter for the task
- Change the workspace to point the same setup at a different repo or folder

Three details are especially helpful during onboarding:

- The workspace matters: the agent operates relative to the directory you pass with `--workspace` or choose in the UI
- Model selection has a clear override order: `.env` overrides per-use-case config, which overrides `settings.yaml`
- Traces are part of the product, not just debug output: they give you an audit trail for what the agent saw and did

---

## Custom Tools

One of the main reasons to use this repo is to try custom SDK tools in a project that is already wired up.

Create custom tools by adding Python files to `src/lab/tools/`. Tools are automatically discovered and registered, which makes this repo useful as a scratchpad for experimenting with new capabilities.

**Example: Word Count Tool**

```python
# src/lab/tools/word_count.py
from collections.abc import Sequence
from typing import Any, ClassVar

from pydantic import Field

from openhands.sdk import Action, Observation, TextContent, ToolDefinition
from openhands.sdk.tool import ToolExecutor

from lab.tools.base import BaseLabTool


class WordCountAction(Action):
    """Action for counting words in a file."""
    path: str = Field(description="Path to the file")


class WordCountObservation(Observation):
    """Observation with word count results."""
    word_count: int
    line_count: int

    @property
    def to_llm_content(self) -> Sequence[TextContent]:
        return [TextContent(text=f"Words: {self.word_count}, Lines: {self.line_count}")]


class WordCountExecutor(ToolExecutor[WordCountAction, WordCountObservation]):
    def __init__(self, working_dir: str):
        self.working_dir = working_dir

    def __call__(self, action: WordCountAction, conversation=None) -> WordCountObservation:
        # Implementation here
        ...


class WordCountTool(BaseLabTool[WordCountAction, WordCountObservation]):
    tool_name: ClassVar[str] = "word_count"
    tool_description: ClassVar[str] = "Count words and lines in a file"

    @classmethod
    def create(cls, conv_state: Any, **params) -> Sequence[ToolDefinition]:
        executor = WordCountExecutor(working_dir=conv_state.workspace.working_dir)
        return [cls(
            description=cls.tool_description,
            action_type=WordCountAction,
            observation_type=WordCountObservation,
            executor=executor,
        )]
```

**Hot Reload:** Tools are automatically reloaded when files are modified (in dashboard mode), so you can update a tool, rerun a task, and immediately compare behavior.

---

## Create Your Own Use Case

Creating a custom agent is one of the quickest ways to learn how the OpenHands SDK behaves under different instructions.

You do not need to design a perfect agent architecture up front. Start with an existing agent, tweak it, run it, and refine from there.

Start by copying the closest existing entry in `config/agents.yaml`:

```yaml
agents:
  docs-helper:
    description: "Improve documentation quality and onboarding"
    system_prompt: |
      You are a documentation assistant. Focus on:
      - clarifying setup steps
      - explaining configuration choices
      - improving examples for new users
      - identifying missing onboarding guidance
    tools:
      - terminal
      - file_editor
```

Then validate it:

```bash
uv run python -m lab list
uv run python -m lab run --agent docs-helper --task "Review the README for onboarding gaps"
```

When creating a new agent, adjust these fields intentionally:

- `description`: what this persona is for in one sentence
- `system_prompt`: how the agent should think, prioritize, and communicate
- `tools`: the minimum tools needed for the job
- `model`: optional per-use-case model override when one workflow needs a different default

An easy learning loop is:

1. Copy a agent
2. Change one thing
3. Run a task
4. Inspect the trace
5. Repeat

Good agents are usually narrow and outcome-oriented. If a persona description starts sounding generic, it probably needs to be split into two smaller agents.

---

## Project Structure

```
openhands-lab/
|-- .env                    # Your environment variables (git-ignored)
|-- .env.example            # Example environment template
|-- .oh-lab/                # Session logs and traces
|-- config/
|   |-- settings.yaml       # Global LLM and runtime settings
|   +-- agents.yaml         # Agent definitions
|-- examples/
|   +-- sdk/                # SDK examples imported via sdk-playground agent
|-- src/lab/
|   |-- __init__.py         # Package init (loads .env)
|   |-- __main__.py         # CLI entry point
|   |-- core/
|   |   |-- config.py       # Configuration loading
|   |   |-- session.py      # Session management
|   |   |-- runtime.py      # Workspace factory
|   |   +-- sandbox.py      # Safety guards
|   |-- tools/
|   |   |-- base.py         # Base tool class
|   |   |-- loader.py       # Dynamic tool loading
|   |   +-- word_count.py   # Example custom tool
|   |-- ui/
|   |   +-- main.py         # Streamlit dashboard
|   +-- utils/
|       |-- events.py       # Event formatting
|       +-- watcher.py      # File watching for hot reload
|-- tests/                  # Test suite
|-- pyproject.toml          # Project configuration
|-- CONTRIBUTING.md         # Contribution guidelines
|-- LICENSE                 # MIT License
+-- README.md
```

---

## Development

### Setup Development Environment

```bash
# Install all dependencies including dev tools
uv sync --dev

# Or install test dependencies manually
uv pip install pytest pytest-asyncio ruff
```

### Run Tests

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test file
uv run python -m pytest tests/test_config.py -v

# Run with coverage
uv run python -m pytest tests/ --cov=src/lab
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check . --fix
```

### Session Traces

Every agent session saves a trace file to `.oh-lab/`:

```bash
# View recent traces
ls -la .oh-lab/

# Inspect a trace
cat .oh-lab/session_<id>_trace.json | jq .
```

---

## Troubleshooting

### "API key not found" Error

Ensure your `.env` file exists and contains `LLM_API_KEY`:

```bash
cat .env | grep LLM_API_KEY
```

### "Authentication Error" with OpenHands Proxy

Make sure you're using the correct model prefix:

```env
# Correct for OpenHands subscription
LLM_MODEL=openhands/claude-sonnet-4-5-20250929

# NOT this (direct Anthropic)
# LLM_MODEL=anthropic/claude-sonnet-4-5-20250929
```

### "tmux not installed" Warning

Install tmux for better terminal stability:

```bash
# macOS
brew install tmux

# Ubuntu/Debian
sudo apt-get install tmux
```

### Module Not Found Errors

Ensure you're running commands with `uv run`:

```bash
# Correct
uv run python -m lab list

# May fail if venv not activated
python -m lab list
```

### No Agents Show Up

Make sure `config/agents.yaml` exists and is valid YAML:

```bash
uv run python -m lab list
```

If the list is empty, start from one of the examples in this README or in `config/agents.yaml`.

### The Agent Looked at the Wrong Files

This usually means the workspace directory was not set to the repository or folder you intended.

```bash
uv run python -m lab run \
  --agent debug-cli \
  --workspace /path/to/project \
  --task "Summarize this workspace"
```

In the dashboard, double-check the "Working directory" field in the sidebar before starting a run.

### A Custom Tool Does Not Appear

Check these common causes:

- The file is not in `src/lab/tools/`
- The module failed to import because of a Python error
- The tool class does not inherit from `BaseLabTool`
- The file name is skipped by the loader because it starts with `_`

---

## License

MIT
