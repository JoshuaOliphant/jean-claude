---
name: jean-claude-cli
description: Expert guide for using Jean Claude CLI commands, workflows, and Beads integration. Use when user asks about jc commands, two-agent workflows, Beads tasks, or Jean Claude features.
---

# Jean Claude CLI Expert

You are an expert in using the Jean Claude CLI (`jc`), a powerful AI-driven development workflow tool.

## Core Commands

### `jc prompt "description"`
Execute a single prompt with Claude Agent SDK.

**When to use:**
- Quick one-off tasks
- Testing prompts
- Simple code generation

**Options:**
- `--model opus|sonnet|haiku` - Choose model (default: sonnet)
- `--stream` - Show real-time output
- `--raw` - Return raw response without formatting

**Example:**
```bash
jc prompt "Add docstrings to all functions" --model sonnet
```

### `jc work <task-id>`
Execute a Beads task using two-agent workflow.

**When to use:**
- Working on Beads-tracked issues
- Feature development with planning phase
- Tasks requiring verification

**How it works:**
1. Fetches task from Beads (`bd show <task-id>`)
2. Generates spec in `specs/beads-{task-id}.md`
3. Runs two-agent workflow (Opus plans → Sonnet implements)
4. Verifies completion

**Example:**
```bash
jc work beads-abc123
```

### `jc workflow "description"`
Run two-agent workflow without Beads.

**When to use:**
- Ad-hoc feature development
- Complex multi-step tasks
- When you need planning + implementation

**Phases:**
1. **Planning** (Opus): Analyzes scope, creates feature list
2. **Implementation** (Sonnet): Implements features one by one
3. **Verification**: Runs tests, checks completion

**Options:**
- `--initializer-model opus|sonnet` - Planning model (default: opus)
- `--coder-model opus|sonnet|haiku` - Implementation model (default: sonnet)
- `--max-iterations N` - Max iterations (default: 10)
- `--auto-continue` - Resume automatically if interrupted

**Example:**
```bash
jc workflow "Add user authentication with JWT tokens" --auto-continue
```

### `jc init`
Initialize Jean Claude in a project.

**What it creates:**
- `.jc-project.yaml` - Project configuration
- `.claude/skills/jean-claude-cli/` - This skill
- `specs/` - Workflow specifications directory
- `agents/` - Agent working directories

**Run once per project:**
```bash
jc init
```

## Beads Integration

Jean Claude integrates with Beads issue tracker for seamless task management.

### Finding Work
```bash
# Find available tasks
bd ready

# List all open tasks
bd list --status=open

# Show task details
bd show beads-abc123
```

### Creating Tasks
```bash
# Create new task
bd create --title="Add feature X" --type=feature --priority=2

# Add dependencies
bd dep add beads-yyy beads-xxx  # yyy depends on xxx
```

### Closing Tasks
```bash
# Close single task
bd close beads-abc123

# Close multiple tasks (efficient!)
bd close beads-abc beads-def beads-xyz

# Close with reason
bd close beads-abc --reason="Completed in PR #42"
```

### Workflow with Beads
```bash
# 1. Find available work
bd ready

# 2. Execute task
jc work beads-abc123

# 3. Close when done
bd close beads-abc123
```

## Two-Agent Pattern

Jean Claude's core innovation is the **two-agent pattern**:

1. **Initializer Agent (Opus)**: Analyzes scope once, creates feature list
2. **Coder Agent (Sonnet)**: Loops through features, implements one per iteration

**Benefits:**
- Fresh context per feature (avoids context bloat)
- Strategic planning with tactical execution
- Cost-effective (expensive model only for planning)

**State Management:**
- Shared state: `agents/{workflow-id}/state.json`
- Features tracked: `not_started` → `in_progress` → `completed`
- Verification after each feature

## Status and Monitoring

### Check Workflow Status
```bash
# Latest workflow
jc status

# Specific workflow
jc status <workflow-id>

# JSON output
jc status --json
```

### View Logs
```bash
# Latest workflow logs
jc logs

# Specific workflow
jc logs <workflow-id>

# Follow mode (real-time)
jc logs --follow
```

### Dashboard
```bash
# Launch web dashboard
jc dashboard
```

## Advanced Features

### Auto-Continue
Autonomous continuation loops for long-running workflows:
```bash
jc workflow "Large refactoring" --auto-continue --max-iterations 50
```

### Coordinator Pattern
Agents can ask for help via mailbox tools:
- `ask_user` - Request clarification (pauses workflow)
- `notify_user` - Send progress update (non-blocking)

Coordinator (main Claude Code) triages questions:
- 90% answered automatically
- 10% escalated to human via ntfy.sh

### ntfy.sh Notifications
Get critical decisions on your phone:
```bash
# Setup (one-time)
export JEAN_CLAUDE_NTFY_TOPIC="your-escalation-topic"
export JEAN_CLAUDE_NTFY_RESPONSE_TOPIC="your-response-topic"

# Respond from phone
{workflow-id}: Your response here
```

## Common Workflows

### Feature Development
```bash
# Option 1: With Beads
bd create --title="Add feature X" --type=feature --priority=2
jc work beads-abc123
bd close beads-abc123

# Option 2: Ad-hoc
jc workflow "Add feature X" --auto-continue
```

### Bug Fixes
```bash
bd create --title="Fix bug Y" --type=bug --priority=1
jc work beads-bug123
bd close beads-bug123
```

### Testing
```bash
jc prompt "Write tests for module X" --model sonnet
uv run pytest tests/
```

## Best Practices

1. **Use Beads for tracking**: All significant work should have a Beads task
2. **Close tasks in batches**: `bd close task1 task2 task3` (more efficient)
3. **Verify before closing**: Check that tests pass and feature works
4. **Use auto-continue for large tasks**: Enables unattended execution
5. **Let coordinator handle questions**: Don't interrupt workflows manually
6. **Respond promptly to escalations**: Coordinators timeout after 30 minutes

## Troubleshooting

### Workflow Stuck
```bash
# Check status
jc status

# View logs
jc logs --follow

# Check for agent questions
# Look in agents/{workflow-id}/INBOX/
```

### Beads Sync Issues
```bash
bd doctor        # Check for issues
bd sync --status # Check sync status
bd sync          # Force sync
```

### Environment Issues
```bash
# Check Python version
python --version  # Should be ≥3.10

# Check uv
uv --version

# Reinstall dependencies
uv sync --frozen
```

## Configuration

### Project Config (`.jc-project.yaml`)
```yaml
directories:
  specs: specs/
  agents: agents/
  trees: trees/

tooling:
  test_command: uv run pytest
  linter_command: uv run ruff check .

workflows:
  default_model: sonnet
  auto_commit: true

vcs:
  issue_tracker: beads
  platform: github
```

### Environment Variables
- `JEAN_CLAUDE_NTFY_TOPIC` - Escalation notifications
- `JEAN_CLAUDE_NTFY_RESPONSE_TOPIC` - Mobile responses
- `CLAUDE_CODE_PATH` - Path to Claude Code CLI

## Examples

### Complete Feature Development
```bash
# 1. Create task
bd create --title="Add user authentication" --type=feature --priority=2

# 2. Execute with two-agent workflow
jc work beads-auth123 --auto-continue

# 3. Verify
uv run pytest tests/
jc status

# 4. Close task
bd close beads-auth123
```

### Quick Refactoring
```bash
jc prompt "Refactor module X to use async/await" --model sonnet --stream
```

### Large Migration
```bash
jc workflow "Migrate from SQLAlchemy 1.4 to 2.0" \
  --initializer-model opus \
  --coder-model sonnet \
  --auto-continue \
  --max-iterations 30
```

## Key Concepts

- **Workflow ID**: Unique 8-char UUID for each workflow (e.g., `a3b4c5d6`)
- **State JSON**: `agents/{workflow-id}/state.json` - single source of truth
- **Feature List**: Planning phase creates list, coder works through it
- **Context Reset**: Coder gets fresh context per feature (prevents bloat)
- **Verification**: Each feature verified before moving to next
- **Event Store**: SQLite database (`.jc/events.db`) tracks all events

## Resources

- Documentation: `docs/` directory
- Examples: `examples/` directory
- Templates: `src/jean_claude/templates/`
- CLAUDE.md: Project-specific guidance

---

**Remember**: Jean Claude automates workflows, not just tasks. The two-agent pattern ensures strategic planning with tactical execution, keeping costs low while maintaining high quality.
