# Jean Claude CLI

> Universal AI Developer Workflows - Transform any project into an AI-driven development environment

Jean Claude (`jc`) is a CLI tool that enables programmatic AI agent orchestration for any codebase. Execute prompts, run multi-phase workflows, and monitor agent activity with a unified interface.

## Features

- **Universal CLI**: Single `jc` command for all operations
- **Two-Agent Workflow**: Opus plans features, Sonnet implements them
- **Beads Integration**: Execute workflows directly from Beads tasks with `jc work`
- **Real-Time Streaming**: Watch agent output as it works with `--stream` mode
- **SDK-Based Execution**: Claude Agent SDK with Bedrock authentication
- **Workflow Composition**: Multi-phase SDLC workflows (plan → implement → verify → complete)
- **Git Worktree Isolation**: Safe parallel development without conflicts
- **Real-Time Telemetry**: SQLite event store with live monitoring UI

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

# Run a two-agent workflow (Opus plans, Sonnet implements)
jc workflow "Add user authentication with JWT"

# Or work on a Beads task directly
jc work jean_claude-2sz.4

# Run a simple chore workflow
jc run chore "Add error handling to login"
```

## Commands

### Core Commands

```bash
jc init                              # Initialize ADW in current project
jc prompt "your prompt here"         # Execute adhoc prompt
jc prompt "your prompt" --stream     # Stream output in real-time
jc run chore "task description"      # Run chore workflow
jc run feature "feature description" # Run feature workflow
```

### Two-Agent Workflow

The flagship workflow pattern: Opus plans, Sonnet implements.

```bash
# Full workflow (plan + implement)
jc workflow "Build user authentication"

# Use custom models
jc workflow "Complex feature" -i opus -c opus

# Run initializer and coder separately (modular approach)
jc initialize "Task description" -w my-workflow
jc implement my-workflow
```

### Beads Integration

Work directly from Beads tasks:

```bash
# Execute workflow from Beads task
jc work jean_claude-2sz.4

# Plan only, don't implement
jc work task-123 --dry-run

# Pause for approval after planning
jc work task-123 --show-plan

# Use Opus for both agents
jc work task-123 --model opus
```

### Project Management

```bash
jc prime                             # Gather project context
jc migrate                           # Update project to latest version
jc onboard                           # Show CLAUDE.md content
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

## Configuration

Jean Claude uses `.jc-project.yaml` for project-specific configuration:

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
├── agents/                     # Agent working directories
│   └── {workflow_id}/
│       ├── state.json          # Workflow state with features
│       └── events.jsonl        # Event log (JSONL format)
├── trees/                      # Git worktrees (isolated execution)
├── specs/                      # Workflow specifications
│   └── beads-{task_id}.md      # Auto-generated from Beads tasks
├── .jc/                        # Internal state
│   └── events.db               # SQLite event store
└── .jc-project.yaml            # Project configuration
```

## Authentication

### Anthropic API

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### AWS Bedrock

```bash
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_PROFILE="your-profile"
export AWS_REGION="us-west-2"
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
