# Jean Claude CLI

> Universal AI Developer Workflows - Transform any project into an AI-driven development environment

Jean Claude (`jc`) is a CLI tool that enables programmatic AI agent orchestration for any codebase. Execute prompts, run multi-phase workflows, and monitor agent activity with a unified interface.

## Features

- **Universal CLI**: Single `jc` command for all operations
- **Real-Time Streaming**: Watch agent output as it works with `--stream` mode
- **SDK-Based Execution**: Claude Agent SDK with Bedrock authentication
- **Workflow Composition**: Multi-phase SDLC workflows (plan -> implement -> test -> review)
- **Git Worktree Isolation**: Safe parallel development without conflicts
- **Real-Time Telemetry**: SQLite event store with live monitoring UI
- **Beads Integration**: Local SQLite-based issue tracking for offline development

## Installation

```bash
# Install with uv
uv pip install jean-claude

# Or install globally with uvx
uvx install jean-claude

# Verify installation
jc --version
```

## Quick Start

```bash
# Initialize ADW in your project
cd my-project/
jc init

# Run an adhoc prompt
jc prompt "Analyze the codebase structure"

# Run a chore workflow
jc run chore "Add error handling to login"

# Monitor workflow events in real-time
jc watch
```

## Commands

### Core Commands

```bash
jc init                              # Initialize ADW in current project
jc prompt "your prompt here"         # Execute adhoc prompt
jc prompt "your prompt" --stream     # Stream output in real-time
jc run chore "task description"      # Run chore workflow
jc run feature "feature description" # Run feature workflow
jc watch                             # Real-time monitoring UI
```

### State & Monitoring

```bash
jc ps                                # List running workflows
jc state list                        # List all workflow states
jc state show <workflow_id>          # Show workflow details
jc stop <workflow_id>                # Stop running workflow
```

### Streaming Output

Real-time streaming displays output as the agent works:

```bash
# Stream output in real-time
jc prompt "Analyze the codebase" --stream

# Show tool uses and thinking process
jc prompt "Refactor authentication" --stream --show-thinking

# Different models with streaming
jc prompt "Quick question" --stream -m haiku
jc prompt "Complex analysis" --stream -m opus
```

**Benefits of streaming:**
- See progress in real-time as the agent works
- Better user experience for long-running prompts
- Optional visibility into tool uses and thinking process
- Graceful interrupt handling (Ctrl+C)

### Cleanup

```bash
jc clean --older-than 7d             # Remove old worktrees
jc clean --zombies                   # Mark dead processes
jc clean --dry-run                   # Preview without deleting
```

### Configuration

```bash
jc config show                       # Display current config
jc config set-api-key <key>          # Save Anthropic API key
jc config use-bedrock --profile dev  # Configure AWS Bedrock
```

## Configuration

ADW uses `.jc-project.yaml` for project-specific configuration:

```yaml
directories:
  specs: specs/
  agents: agents/
  trees: trees/
  source: src/
  tests: tests/

tooling:
  test_command: uv run pytest
  linter_command: uv run ruff check .

workflows:
  default_model: sonnet
  auto_commit: true
```

## Architecture

```
project/
├── agents/              # Agent working directories
│   └── {workflow_id}/
│       └── state.json   # Workflow state
├── trees/               # Git worktrees (isolated execution)
├── specs/               # Workflow specifications
├── .jc/                 # Internal state
│   └── events.db        # SQLite telemetry
└── .jc-project.yaml     # Project configuration
```

## Authentication

### Anthropic API

```bash
export ANTHROPIC_API_KEY="your-api-key"
# Or save to config
jc config set-api-key "your-api-key"
```

### AWS Bedrock

```bash
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_PROFILE="your-profile"
# Or save to config
jc config use-bedrock --profile your-profile --region us-west-2
```

## Development

```bash
# Clone and install
git clone https://github.com/joshuaoliphant/jean-claude
cd jean-claude
uv sync

# Run tests
uv run pytest

# Run CLI in development
uv run jc --help
```

## License

MIT
