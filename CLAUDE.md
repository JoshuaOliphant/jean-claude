# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

| Task | Command |
|------|---------|
| Run all tests | `uv run pytest` |
| Run single test | `uv run pytest tests/test_work_command.py` |
| Run with coverage | `uv run pytest --cov=jean_claude` |
| Lint code | `uv run ruff check .` |
| Format code | `uv run ruff format .` |
| Type check | `uv run mypy src/` |
| Run CLI locally | `uv run jc <command>` |
| Initialize project | `jc init` |
| Update existing project | `jc migrate` |

## Architecture Overview

Jean Claude is a **two-layer orchestration framework** that transforms any Python project into an AI-driven development environment:

### Layer 1: Agentic Layer
`.claude/commands/` - Slash commands for Claude Code that orchestrate workflows

### Layer 2: Application Layer
`src/jean_claude/` - The CLI tool itself with five subsystems:

```
src/jean_claude/
├── cli/                 # Click-based command interface
│   ├── main.py          # Root @click.group() at line 14
│   ├── commands/        # 16 command modules (work, workflow, prompt, init, migrate, etc.)
│   └── streaming.py     # SSE-based real-time output
│
├── core/                # Core business logic (46 modules)
│   ├── agent.py         # ExecutionResult, PromptRequest models
│   ├── sdk_executor.py  # Claude Agent SDK wrapper
│   ├── state.py         # WorkflowState persistence (JSON files)
│   ├── beads.py         # Beads task model + integration
│   ├── security.py      # Bash command validation hooks
│   ├── events.py        # Event logging to SQLite
│   ├── message.py       # Agent-to-agent mailbox communication
│   └── mailbox_*.py     # Mailbox infrastructure (paths, api, storage, etc.)
│
├── orchestration/       # Multi-agent workflow engine
│   ├── two_agent.py     # Opus plans → Sonnet implements pattern
│   ├── auto_continue.py # Autonomous continuation loops
│   ├── post_tool_use_hook.py      # Agent SDK tool hook integration
│   ├── subagent_stop_hook.py      # Subagent completion handling
│   └── user_prompt_submit_hook.py # User prompt preprocessing
│
├── tools/               # MCP tool implementations
│   └── mailbox_tools.py # ask_user, notify_user, escalate_to_human
│
├── skills/              # Claude Code skills (installed by jc init)
│   └── jean-claude-cli/ # Comprehensive CLI documentation skill
│
└── dashboard/           # FastAPI monitoring UI
    ├── app.py           # Web server with SSE streaming
    └── templates/       # HTML templates
```

### Key Architectural Patterns

**Two-Agent Pattern** (core innovation):
- **Initializer Agent** (Opus): Analyzes scope once, creates feature list as JSON
- **Coder Agent** (Sonnet): Loops through features, implements one per iteration
- **Shared State**: `agents/{workflow_id}/state.json` is the single source of truth
- **Context Reset**: Coder agent gets fresh context per feature to avoid bloat

**Workflow State Machine**:
```python
WorkflowState (state.py):
  - Features: List[Feature] with status tracking (not_started → in_progress → completed)
  - Phases: Dict[str, WorkflowPhase] (planning → implementing → verifying → complete)
  - Session tracking: session_ids, costs, duration
  - Beads integration: task_id, title for external issue tracking
```

**Event-Driven Telemetry**:
- All operations logged to `.jc/events.db` (SQLite)
- Real-time streaming via FastAPI + SSE (sse-starlette)
- EventLogger pattern for structured logging

**Beads Integration**:
- External issue tracker (similar to Jira/Linear)
- Auto-generates specs from tasks in `specs/beads-{task_id}.md`
- `jc work <task-id>` executes full workflow from Beads task
- Model: `BeadsTask` in `core/beads.py` with status/priority enums

**Mailbox Communication**:
- Agents communicate via INBOX/OUTBOX message files
- `Message` model with priority levels and response tracking
- Enables async agent-to-agent messaging

## Development Standards

### Code Organization

1. **ABOUTME Comments**: Every file starts with 2-line comment:
   ```python
   # ABOUTME: Brief description of file purpose
   # ABOUTME: Key responsibility or pattern used
   ```

2. **Pydantic v2**: All data models use Pydantic for validation and serialization

3. **Click Framework**: All CLI commands use Click decorators, never argparse

4. **Async/Sync Boundary**:
   - SDK execution is async (`execute_prompt_async` in `sdk_executor.py`)
   - CLI commands are sync (Click limitation)
   - Use `anyio.run()` to bridge sync→async

### Testing Philosophy

**Core Principle**: Test OUR code, not external dependencies.

**What to Mock**:
- ✅ Beads CLI (`bd` commands) - external tool
- ✅ Claude Agent SDK responses
- ✅ Subprocess calls (`subprocess.run`)
- ✅ File system operations (when appropriate)

**What NOT to Mock**:
- ❌ Pydantic validation - test real models
- ❌ Click command parsing - trust the framework
- ❌ Our own business logic - test real implementations

### Critical Mock Patching Rule

**Always patch where an object is USED, not where it's DEFINED.**

```python
# If edit_and_revalidate.py imports:
# from jean_claude.core.beads import fetch_beads_task

# ✅ CORRECT - patch in the importing module
@patch('jean_claude.core.edit_and_revalidate.fetch_beads_task')
def test_something(mock_fetch):
    pass

# ❌ WRONG - patching in source module won't work
@patch('jean_claude.core.beads.fetch_beads_task')
def test_something(mock_fetch):
    pass
```

### Test Organization

**File Mapping**:
- `src/jean_claude/core/foo.py` → `tests/core/test_foo.py`
- `src/jean_claude/cli/commands/bar.py` → `tests/test_bar.py`

**Fixture Hierarchy**:
- `tests/conftest.py` - Root fixtures (cli_runner, mock_beads_task, work_command_mocks)
- `tests/core/conftest.py` - Core module fixtures (sample_beads_task, subprocess mocks)
- `tests/orchestration/conftest.py` - Workflow fixtures (workflow_state, execution_result)
- `tests/templates/conftest.py` - Template path fixtures

**Key Fixtures** (see conftest.py files for complete list):
- `cli_runner` - Click CLI testing
- `mock_beads_task` / `sample_beads_task` - BeadsTask instances
- `work_command_mocks` - All mocks for work command
- `sample_workflow_state` - Pre-configured WorkflowState
- `mock_subprocess_success/failure` - Subprocess mocks

**Search Before Creating**:
```bash
# Find existing tests for a topic
grep -r "def test_.*beads" tests/

# Check for existing fixtures
grep -r "def.*fixture" tests/conftest.py tests/core/conftest.py
```

### Mock Patterns

```python
# ✅ GOOD - Use @patch decorators (bottom-up order)
@patch('module.function_c')
@patch('module.function_b')
@patch('module.function_a')
def test_thing(mock_a, mock_b, mock_c):
    pass

# ❌ BAD - Nested with patch() blocks
def test_thing():
    with patch('a'):
        with patch('b'):
            pass  # DON'T NEST

# ✅ GOOD - Use AsyncMock for async functions
@patch('module.async_function', new_callable=AsyncMock)
def test_async(mock_async):
    pass

# ❌ BAD - Regular Mock for async functions
@patch('module.async_function')  # Will cause errors
def test_async(mock_async):
    pass
```

### Test Consolidation

**Prefer one comprehensive test over many narrow tests.**

```python
# ✅ GOOD - Comprehensive test
@pytest.mark.parametrize("priority", [MessagePriority.LOW, MessagePriority.NORMAL, MessagePriority.URGENT])
def test_read_messages_all_priorities(priority):
    # Single test covering all priority levels
    pass

# ❌ BAD - Separate test per priority
def test_read_low_priority(): pass
def test_read_normal_priority(): pass
def test_read_urgent_priority(): pass
```

**Don't test framework behavior**:
- Click flag parsing - trust Click
- Pydantic field defaults - trust Pydantic
- pytest fixture mechanics - trust pytest

## Key Entry Points

| Purpose | Location |
|---------|----------|
| CLI root command | `src/jean_claude/cli/main.py:14` |
| Project initialization | `src/jean_claude/cli/commands/init.py` |
| Two-agent workflow | `src/jean_claude/orchestration/two_agent.py` |
| SDK execution | `src/jean_claude/core/sdk_executor.py` |
| State persistence | `src/jean_claude/core/state.py` |
| Event logging | `src/jean_claude/core/events.py` |
| Beads integration | `src/jean_claude/core/beads.py` |
| Mailbox tools | `src/jean_claude/tools/mailbox_tools.py` |
| CLI skill content | `src/jean_claude/skills/jean-claude-cli/SKILL.md` |

## Configuration

Project configuration in `.jc-project.yaml`:
```yaml
directories:
  specs: specs/       # Workflow specifications
  agents: agents/     # Agent working directories (state.json here)
  trees: trees/       # Git worktrees (gitignored)
  source: src/
  tests: tests/

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

## Output Locations

- **Agent state**: `agents/{workflow_id}/state.json` - WorkflowState persistence
- **Event logs**: `agents/{workflow_id}/events.jsonl` - JSONL event log per workflow
- **SQLite events**: `.jc/events.db` - Centralized event store
- **Temporary files**: `.jc/temp/` - Verification scripts (check_*.py, demo_*.py)
- **Reports**: `.jc/reports/` - Status and completion reports
- **Specs**: `specs/` and `specs/plans/` - Workflow specifications
- **Worktrees**: `trees/` (gitignored) - Isolated git worktrees
- **Skills**: `.claude/skills/jean-claude-cli/` - Bundled CLI documentation skill
- **Slash commands**: `.claude/commands/` - Custom slash commands (/prime, /cleanup)

## Project Initialization

### `jc init` (New Projects)
One-command setup that creates:
- `.jc-project.yaml` - Project configuration with auto-detected settings
- `.claude/skills/jean-claude-cli/` - 358-line comprehensive CLI skill
- `.claude/commands/` - Slash commands (/prime, /cleanup)
- `specs/`, `agents/`, `.jc/` directories
- `CLAUDE.md` section (appends to existing file)
- `.gitignore` entries for generated directories

### `jc migrate` (Existing Projects)
Updates existing Jean Claude installations to the latest version:
- Installs missing skill (`.claude/skills/jean-claude-cli/`)
- Updates CLAUDE.md if section is missing
- Adds new slash commands
- Creates missing directories
- Safe operation: never overwrites existing files

### Skill Architecture
The `jean-claude-cli` skill provides comprehensive documentation that:
- Loads only when relevant (semantic triggering)
- Reduces context bloat vs putting everything in CLAUDE.md
- Contains 358 lines covering all commands and workflows
- Source: `src/jean_claude/skills/jean-claude-cli/SKILL.md`

## Coordinator Communication Patterns

### ntfy Response Polling

When escalating questions to La Boeuf via ntfy.sh, **always use sleep intervals to poll for responses** rather than blocking indefinitely.

**Pattern**:
```python
from jean_claude.tools.mailbox_tools import escalate_to_human, poll_ntfy_responses
import time

# 1. Send escalation (project name auto-detected from current directory)
escalate_to_human(
    title="Question from Coordinator",
    message=f"Workflow: {workflow_id}\n\nQuestion: {question}",
    priority=5,
    project_name="my-project"  # Optional: defaults to Path.cwd().name
)
# Notification appears as: "[my-project] Question from Coordinator"

# 2. Poll with sleep intervals (not blocking wait)
max_attempts = 30  # 30 attempts × 10 seconds = 5 minutes
for attempt in range(max_attempts):
    time.sleep(10)  # Poll every 10 seconds

    responses = poll_ntfy_responses()
    matching = [r for r in responses if r['workflow_id'] == workflow_id]

    if matching:
        response = matching[0]['response']
        break
else:
    # No response after 5 minutes
    response = None
```

**Why**: La Boeuf may be away from phone or need time to think. Polling with sleep intervals:
- Allows time for human response without blocking
- Shows respect for asynchronous nature of mobile communication
- Provides clear timeout behavior
- Enables progress updates during wait

**Response Format**: Messages from phone must include workflow ID:
```
{workflow-id}: {response text}
```

Example: `mobile-test-001: Yes, proceed with migration`

### Multi-Project Support

When running Jean Claude across multiple projects simultaneously:

1. **All projects share the same ntfy topics** (escalation + response)
2. **Each workflow gets a unique 8-character UUID** (e.g., `a3b4c5d6`)
3. **Project names appear in notification titles** for easy identification
4. **Each coordinator filters responses by workflow_id**

**Example scenario** - 3 projects running:
```
Project A (jean-claude):      Workflow a3b4c5d6
Project B (my-api-server):    Workflow f8e2a1b9
Project C (website):          Workflow 2c7d9e4a
```

**You receive 3 notifications:**
- `[jean-claude] Architecture Decision Needed`
- `[my-api-server] Should I add rate limiting?`
- `[website] Use SQLite or Postgres?`

**Respond to each:**
```
a3b4c5d6: Use the pattern from existing code
f8e2a1b9: Yes, add rate limiting
2c7d9e4a: Use Postgres
```

**What happens:** All 3 responses go to shared `oliphantjc_responses` topic, but each coordinator only processes messages matching its workflow_id.

## Documentation

For deeper architectural understanding:

- [Architecture Overview](docs/ARCHITECTURE.md) - Complete system architecture
- [Testing Patterns](docs/testing.md) - Fixtures, TDD, async mocks
- [Two-Agent Workflow](docs/two-agent-workflow.md) - Opus/Sonnet orchestration pattern
- [Auto-Continue](docs/auto-continue-workflow.md) - Autonomous continuation loops
- [Coordinator Pattern](docs/coordinator-pattern.md) - Agent-to-human communication with ntfy.sh
- [Beads Workflow](docs/beads-workflow.md) - External issue tracker integration
- [Event Store Architecture](docs/event-store-architecture.md) - SQLite event logging
- [Security Hooks](docs/security-hooks-implementation.md) - Bash command validation
- [Streaming](docs/streaming-implementation-summary.md) - Real-time SSE output
- [Agent SDK Hooks](docs/agent_sdk_hooks.md) - Claude Agent SDK hook integration
- [Claude Code Hooks](docs/claude_code_hooks.md) - Claude Code configuration hooks
- [Claude Code Skills](docs/claude_code_skills.md) - How skills work in Claude Code
- [Autonomous Agent Patterns](docs/autonomous-agent-patterns.md) - Agent autonomy design

## Common Pitfalls

1. **AsyncMock vs Mock**: Use `AsyncMock` for async functions, `Mock` for sync
2. **Patch Location**: Patch where used, not where defined
3. **Fixture Duplication**: Check conftest.py files before creating new fixtures
4. **Testing External Tools**: Don't test Beads/SDK - mock them and test our integration
5. **Nested Mocking**: Use @patch decorators, not nested `with patch()` blocks
6. **Test File Location**: Follow the established directory structure (core/, orchestration/, etc.)
7. **Skill vs CLAUDE.md**: Generic Jean Claude docs go in the skill; project-specific docs in CLAUDE.md
8. **Parallel Test Execution**: Tests run with `-n 4` (4 workers); avoid shared state between tests

## Jean Claude AI Workflows

This project uses [Jean Claude](https://github.com/JoshuaOliphant/jean-claude) for AI-powered development workflows.

### Quick Start

```bash
bd ready                      # Find available Beads tasks
jc work <task-id>            # Execute a Beads task
jc workflow "description"    # Ad-hoc workflow without Beads
jc status                    # Check workflow status
```

### Workflow Artifacts

Jean Claude stores workflow data in:
- `specs/` - Workflow specifications and feature plans
- `agents/{workflow-id}/state.json` - Workflow state and progress
- `.jc/events.db` - Event history for monitoring

### Getting Help

For comprehensive Jean Claude documentation, ask me (Claude):
- "How do I use jc workflow?"
- "What's the two-agent pattern?"
- "How does Beads integration work?"

The `jean-claude-cli` skill (installed by `jc init`) provides detailed command guides.

### Configuration

Project settings: `.jc-project.yaml`

