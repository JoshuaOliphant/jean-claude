# ABOUTME: Agent instructions for Jean Claude CLI development
# ABOUTME: Provides beads workflow context and development guidelines

# Agent Instructions for Jean Claude CLI

## Issue Tracking

This project uses **bd (beads)** for issue tracking.
Run `bd prime` for workflow context, or install hooks (`bd hooks install`) for auto-injection.

**Quick reference:**
- `bd ready` - Find unblocked work
- `bd create "Title" --type task --priority 2` - Create issue
- `bd close <id>` - Complete work
- `bd sync` - Sync with git (run at session end)

For full workflow details: `bd prime`

## Project Context

Jean Claude CLI (`jc`) is a universal CLI tool for programmatic AI agent orchestration. It transforms any project into an AI-driven development environment.

### Key Development Patterns

1. **TDD Approach**: Write tests before implementation
2. **ABOUTME Comments**: All files start with 2-line ABOUTME comment
3. **Click CLI**: Use Click for command implementation
4. **Pydantic Models**: Use for configuration and data types
5. **Rich Output**: Use Rich library for beautiful terminal output

### Architecture Overview

```
src/jean_claude/
├── core/           # Execution engine, state, templates
├── coordination/   # Event store, telemetry
├── orchestration/  # Workflow execution
├── cli/            # Click commands
└── integrations/   # Git, VCS plugins
```

### Reference Implementation

The mailapi project serves as reference for proven ADW patterns.
