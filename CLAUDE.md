# Jean Claude - AI Developer Workflows (ADW)

Scaled ADW infrastructure for programmatic Claude Code orchestration with Beads issue tracking.

## Project Overview

Jean Claude is a fully scaffolded AI Developer Workflows (ADW) system that enables:
- **Programmatic agent orchestration**: Execute Claude Code prompts via SDK with async support
- **Security-first execution**: Pre-tool-use hooks validate bash commands against configurable allowlists
- **Beads integration**: Local SQLite-based issue tracking for offline development
- **Workflow composition**: Multi-phase SDLC workflows (plan → build → test → review → ship)
- **Git worktree isolation**: Safe parallel development without conflicts
- **Comprehensive observability**: All agent outputs saved to `agents/{adw_id}/`

## Architecture

### Two-Layer Design

```
┌─────────────────────────────────────────┐
│   Agentic Layer (ADWs)                  │
│   - Templates (slash commands)          │
│   - Orchestration scripts               │
│   - State management                    │
└─────────────────────────────────────────┘
            ↓ operates on
┌─────────────────────────────────────────┐
│   Application Layer                     │
│   - Your Python code                    │
│   - Tests                               │
│   - Documentation                       │
└─────────────────────────────────────────┘
```

### Directory Structure

```
jean_claude/
├── adws/                       # AI Developer Workflows
│   ├── adw_prompt.py          # Adhoc prompt execution
│   ├── adw_slash_command.py   # Execute slash commands
│   ├── adw_chore_implement.py # Plan + implement workflow
│   ├── adw_plan_tdd.py        # TDD task breakdown
│   ├── adw_beads_ready.py     # Interactive Beads task picker
│   └── adw_modules/           # Core modules
│       ├── agent.py           # Subprocess execution
│       ├── state.py           # Workflow state management
│       ├── beads_integration.py  # Beads issue tracker
│       ├── git_ops.py         # Git operations
│       ├── worktree_ops.py    # Worktree isolation
│       ├── workflow_ops.py    # Orchestration helpers
│       ├── data_types.py      # Pydantic models
│       └── utils.py           # Utilities
├── .claude/commands/          # Slash command templates
│   ├── chore.md               # Small tasks
│   ├── feature.md             # New features
│   ├── bug.md                 # Bug fixes
│   ├── implement.md           # Implementation
│   ├── plan-tdd.md            # TDD planning
│   ├── test.md                # Test planning
│   ├── review.md              # Code review
│   └── ...                    # 15 total templates
├── specs/                     # Plans and specifications
│   └── plans/                 # TDD task breakdowns
├── agents/                    # Agent execution outputs (gitignored)
│   └── {adw_id}/
│       ├── {agent_name}/      # Per-agent outputs
│       └── adw_state.json     # Workflow state
└── trees/                     # Git worktrees (gitignored)
```

## Quick Start

### 1. Two-Agent Workflow (Recommended for Complex Tasks)

For complex features, use the two-agent pattern where Opus plans and Sonnet codes:

```bash
# Basic usage - Opus plans features, Sonnet implements them
jc workflow "Build a user authentication system with JWT and OAuth2"

# Custom workflow ID for tracking
jc workflow "Add logging middleware" --workflow-id auth-logging

# Use Opus for both agents (slower but higher quality)
jc workflow "Complex architecture" -i opus -c opus

# Auto-confirm without prompt
jc workflow "Simple task" --auto-confirm
```

See [Two-Agent Workflow Documentation](docs/two-agent-workflow.md) for details.

### 2. Adhoc Prompts

Execute any prompt directly:

```bash
# Basic usage
./adws/adw_prompt.py "Explain what this project does"

# Use different models
./adws/adw_prompt.py "Analyze the architecture" --model opus
./adws/adw_prompt.py "Quick question" --model haiku

# Custom working directory
./adws/adw_prompt.py "List files" --working-dir /path/to/project
```

### 3. Slash Commands

Execute templated workflows:

```bash
# Run any slash command
./adws/adw_slash_command.py /chore "Update documentation"
./adws/adw_slash_command.py /feature "Add logging"
./adws/adw_slash_command.py /bug "Fix authentication bug"
```

### 4. Compound Workflows

Multi-phase execution:

```bash
# Plan + Implement in one command
./adws/adw_chore_implement.py "Add error handling to API"

# TDD Planning (breaks large tasks into chunks)
./adws/adw_plan_tdd.py "Build user authentication system"
./adws/adw_plan_tdd.py specs/feature-auth.md --spec-file
```

### 4. Beads Integration

Work with Beads issues:

```bash
# Interactive task picker
./adws/adw_beads_ready.py

# Show ready tasks
bd ready

# Create new task
bd new "Add user registration" --type feature --priority P0

# Update task status
bd update poc-abc --status in_progress
```

## Workflow Patterns

### Pattern 1: Simple Chore

```bash
# 1. Create plan
./adws/adw_slash_command.py /chore $(uuidgen | cut -c1-8) "update README"

# 2. Implement plan
./adws/adw_slash_command.py /implement specs/chore-*.md
```

### Pattern 2: Compound Workflow (Recommended)

```bash
# One command does both planning and implementation
./adws/adw_chore_implement.py "add logging middleware"
```

### Pattern 3: Large Feature with TDD

```bash
# 1. Break down into tasks
./adws/adw_plan_tdd.py "Build authentication system with JWT and OAuth2"
# → Creates specs/plans/plan-{id}.md with 20-30 tasks

# 2. Pick tasks from Beads
./adws/adw_beads_ready.py
# → Select a ready task

# 3. Implement task
./adws/adw_slash_command.py /implement specs/chore-{task-id}.md
```

### Pattern 4: Beads-Driven Development

```bash
# 1. See what's ready to work on
./adws/adw_beads_ready.py

# 2. Select task (e.g., poc-abc)

# 3. Work on it
./adws/adw_slash_command.py /chore poc-abc "Implement the task"

# 4. Mark complete
bd close poc-abc
```

## Security Configuration

Jean Claude implements defense-in-depth security for autonomous agent execution:

### Security Layers

1. **Environment Isolation**: Use Docker or sandboxed environments for production
2. **SDK Tool Permissions**: Only allow necessary tools (`Read`, `Write`, `Edit`, `Bash`, etc.)
3. **Command Allowlists**: Pre-tool-use hooks validate bash commands before execution

### Workflow Types

Security is configurable per workflow type:

#### Readonly Workflow
Inspection only - no file modifications:
```python
PromptRequest(
    prompt="Analyze the codebase",
    workflow_type="readonly",
    enable_security_hooks=True
)
```

**Allowed commands**: `ls`, `cat`, `head`, `tail`, `grep`, `find`, `git status`, `ps`

#### Development Workflow (Default)
Common development tools:
```python
PromptRequest(
    prompt="Add logging to API",
    workflow_type="development",  # default
    enable_security_hooks=True    # default
)
```

**Allowed commands**: All readonly + `cp`, `mkdir`, `touch`, `chmod`, `git`, `uv`, `python`, `pytest`, `npm`, `node`

#### Testing Workflow
Development + test runners:
```python
PromptRequest(
    prompt="Run full test suite",
    workflow_type="testing",
    enable_security_hooks=True
)
```

**Allowed commands**: All development + `coverage`, `tox`

### Custom Allowlists

For specialized workflows, create custom command allowlists:

```python
from jean_claude.core.security import create_custom_allowlist, bash_security_hook

# Create custom allowlist
custom_allowlist = create_custom_allowlist("ls", "cat", "grep", "special-tool")

# Use in hook context
context = {"command_allowlist": custom_allowlist}
result = await bash_security_hook({"command": "special-tool --run"}, context=context)
```

### Disabling Security Hooks

For trusted operations or debugging, hooks can be disabled:

```python
PromptRequest(
    prompt="Emergency fix",
    enable_security_hooks=False  # ⚠️ Use with caution
)
```

**⚠️ Warning**: Only disable security hooks in controlled environments where you trust the agent's actions completely.

## Configuration

### Mode A: Claude Max Subscription (Default)

No configuration needed! Just run the scripts.

```bash
./adws/adw_prompt.py "Hello world"
```

### Mode B: API-Based (For Automation)

For CI/CD, webhooks, or headless workflows:

```bash
# Create .env file
cp .env.sample .env

# Add your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Now scripts work in automation
./adws/adw_prompt.py "Deploy to production"
```

## Available Slash Commands

### Planning Commands

| Command | Purpose | Output |
|---------|---------|--------|
| `/chore` | Plan small tasks | `specs/chore-{id}.md` |
| `/feature` | Plan new features | `specs/feature-{id}.md` |
| `/bug` | Plan bug fixes | `specs/bug-{id}.md` |
| `/plan-tdd` | Break down large tasks | `specs/plans/plan-{id}.md` |
| `/patch` | Quick fixes | `specs/patch-{id}.md` |

### Implementation Commands

| Command | Purpose | Input |
|---------|---------|-------|
| `/implement` | Execute a plan | Plan file path |
| `/test` | Write tests | Spec or plan |
| `/document` | Write docs | Feature spec |
| `/review` | Code review | Branch or files |

### Git & Workflow Commands

| Command | Purpose | Output |
|---------|---------|--------|
| `/generate_branch_name` | Create branch name | Branch name string |
| `/pull_request` | Generate PR description | PR markdown |
| `/install_worktree` | Setup worktree | Instructions |
| `/cleanup_worktrees` | Remove worktrees | Cleanup commands |

### Classification Commands

| Command | Purpose | Output |
|---------|---------|--------|
| `/classify_issue` | Route issues | Slash command |
| `/classify_adw` | Extract workflow info | JSON structure |

### Utility Commands

| Command | Purpose | Output |
|---------|---------|--------|
| `/prime` | Load project context | Context summary |
| `/start` | Start dev servers | Run commands |

## Observability

All agent executions are saved for debugging and analysis:

```
agents/{adw_id}/{agent_name}/
├── cc_raw_output.jsonl          # Raw streaming output
├── cc_raw_output.json            # Parsed JSON array
├── cc_final_object.json          # Final result object
├── custom_summary_output.json   # High-level summary
└── prompts/
    └── {command}.txt             # Executed prompt
```

### Inspecting Outputs

```bash
# See summary
cat agents/{adw_id}/oneoff/custom_summary_output.json | jq

# See full output
cat agents/{adw_id}/oneoff/cc_raw_output.json | jq

# See final result
cat agents/{adw_id}/oneoff/cc_final_object.json | jq

# See what prompt was executed
cat agents/{adw_id}/oneoff/prompts/chore.txt
```

## State Management

Workflows maintain state in `agents/{adw_id}/adw_state.json`:

```json
{
  "adw_id": "abc12345",
  "issue_number": "poc-xyz",
  "branch_name": "feat/poc-xyz-add-auth",
  "plan_file": "specs/feature-abc12345.md",
  "issue_class": "/feature",
  "worktree_path": "trees/abc12345",
  "model_set": "base",
  "all_adws": ["abc12345", "def67890"]
}
```

State is used for:
- Resuming workflows
- Tracking lineage
- Worktree isolation
- Port allocation

## Beads Issue Tracking

### Why Beads?

- **Offline-first**: No internet required
- **SQLite-based**: Simple, portable database
- **Dependency tracking**: Automatic blocker detection
- **Priority management**: P0, P1, P2, P3
- **Status workflow**: open → in_progress → blocked → closed

### Common Beads Commands

```bash
# Create tasks
bd new "Task title" --type feature --priority P0
bd new "Bug description" --type bug

# See what's ready
bd ready

# Update status
bd update poc-abc --status in_progress
bd block poc-abc poc-xyz  # Block abc on xyz

# View task
bd show poc-abc

# Close task
bd close poc-abc

# List all tasks
bd list
```

### Beads + ADW Integration

The ADW system automatically:
- Fetches Beads issues via `beads_integration.fetch_beads_issue()`
- Converts them to GitHubIssue format for compatibility
- Updates status after workflow completion
- Tracks dependencies and blockers

## Advanced Usage

### Custom Models

```bash
# Use Opus for complex planning
./adws/adw_plan_tdd.py "Design distributed system" --model opus

# Use Haiku for simple tasks
./adws/adw_prompt.py "List files" --model haiku
```

### Working Directory Override

```bash
# Execute in different directory
./adws/adw_prompt.py "Analyze code" --working-dir /path/to/other/project
```

### Disable Retry Logic

```bash
# For testing or debugging
./adws/adw_prompt.py "Test prompt" --no-retry
```

### Custom ADW IDs

```bash
# Use specific ID for tracking
./adws/adw_slash_command.py /chore my-custom-id "Task description"
```

## Troubleshooting

### Claude Code Not Found

```bash
# Check installation
claude --version

# Set custom path if needed
export CLAUDE_CODE_PATH=/path/to/claude
```

### Permission Errors

```bash
# Make scripts executable
chmod +x adws/*.py
```

### Import Errors

```bash
# Install dependencies
uv sync

# Or manually
uv add pydantic python-dotenv click rich
```

### Beads Not Found

```bash
# Install beads
pip install beads-project  # Or however you installed it

# Verify
bd --version
```

### Output Files Not Created

Check that `agents/` directory is being created:

```bash
# Should auto-create, but can manually create
mkdir -p agents
```

## Best Practices

### 1. Use Compound Workflows

```bash
# ✅ Good - one command
./adws/adw_chore_implement.py "add logging"

# ❌ Less efficient - two separate commands
./adws/adw_slash_command.py /chore abc123 "add logging"
./adws/adw_slash_command.py /implement specs/chore-abc123.md
```

### 2. Break Down Large Tasks

```bash
# For features > 200 lines or > 5 files, use TDD planning
./adws/adw_plan_tdd.py "Build authentication system"
```

### 3. Use Beads for Task Management

```bash
# Track all work in Beads, not just in specs/
bd new "Feature XYZ" --type feature --priority P0
```

### 4. Choose Right Model

- **Haiku**: Quick questions, simple tasks (fast, cheap)
- **Sonnet**: Most tasks, balanced (default)
- **Opus**: Complex architecture, critical decisions (slow, expensive)

### 5. Review Agent Outputs

```bash
# Always check the custom_summary_output.json
cat agents/{adw_id}/oneoff/custom_summary_output.json | jq
```

## Extension Points

### Adding Custom Slash Commands

1. Create `.claude/commands/my-command.md`
2. Define variables, instructions, format
3. Execute: `./adws/adw_slash_command.py /my-command "args"`

### Adding Custom Workflows

1. Study existing scripts (e.g., `adw_chore_implement.py`)
2. Import from `adw_modules.agent` and `adw_modules.state`
3. Use `execute_template()` for slash commands
4. Save state with `ADWState.save()`

### Adding Custom Agents

Create specialized agent functions in `adw_modules/workflow_ops.py`:

```python
def my_custom_operation(adw_id: str, logger) -> AgentPromptResponse:
    request = AgentTemplateRequest(
        agent_name="my_agent",
        slash_command="/my-command",
        args=["arg1", "arg2"],
        adw_id=adw_id,
        model="sonnet"
    )
    return execute_template(request)
```

## Further Reading

- Beads Documentation: https://github.com/yourusername/beads (replace with actual link)
- Claude Code Documentation: https://docs.claude.com/en/docs/claude-code
- ADW Bootstrap Skill: `~/.claude/skills/adw-bootstrap/`

## Support

For issues or questions:
1. Check `agents/{adw_id}/` outputs for debugging
2. Review this CLAUDE.md for patterns
3. Inspect the slash command templates in `.claude/commands/`
4. Read module source code in `adws/adw_modules/`
