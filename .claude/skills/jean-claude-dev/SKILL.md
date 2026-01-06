---
name: jean-claude-dev
description: Development guide for working on the Jean Claude project itself. Use this skill when making changes to Jean Claude's source code, tests, documentation, or architecture. This skill provides project-specific testing patterns, common pitfalls, active experiments, and retrospective insights. Do NOT use this skill when users are simply using the jc CLI - this is for Jean Claude contributors and maintainers only.
---

# Jean Claude Development Guide

## Overview

This skill provides guidance for developing Jean Claude itself - the AI-driven workflow orchestration framework. It captures institutional knowledge, testing patterns, common pitfalls, and active experiments that evolve as the project grows.

**When to use this skill:**
- Making changes to `src/jean_claude/` source code
- Writing or updating tests in `tests/`
- Modifying architecture or core patterns
- Working on new features or experiments
- Conducting retrospectives after development sessions

**Do NOT use when:**
- Users are simply using `jc` CLI commands
- Working on user-facing documentation only
- Answering general questions about Jean Claude usage

## Current Architecture Focus

**Active Areas** (as of 2026-01-04):
- Agent note-taking system (branch: `claude/agent-note-taking-system-Ly16E`)
- Event-sourced architecture with SQLite event store
- Mailbox communication between agents and coordinator
- Dashboard memory leak fixes (SSE streaming)
- Version 0.9.0 release cycle

**Core Architectural Patterns:**
1. **Two-Agent Workflow** - Opus (planning) + Sonnet (implementation)
2. **Event Sourcing** - SQLite as single source of truth
3. **Coordinator Pattern** - Agent-to-human escalation via ntfy.sh
4. **Git Worktree Isolation** - Separate filesystems per workflow
5. **Mailbox Communication** - Async agent-to-agent messaging

**Critical Files:**
- `src/jean_claude/orchestration/two_agent.py` - Two-agent pattern implementation
- `src/jean_claude/core/state.py` - WorkflowState persistence
- `src/jean_claude/core/event_store.py` - Event logging to SQLite
- `src/jean_claude/core/sdk_executor.py` - Claude Agent SDK wrapper
- `src/jean_claude/tools/mailbox_tools.py` - Agent communication tools

## Testing Patterns

### Core Principle: Test OUR Code, Not External Dependencies

**What to Mock:**
- ✅ Beads CLI (`bd` commands) - external tool
- ✅ Claude Agent SDK responses
- ✅ Subprocess calls (`subprocess.run`)
- ✅ File system operations (when appropriate)

**What NOT to Mock:**
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

### Fixture Hierarchy

**Three-tier structure:**
1. `tests/conftest.py` - Root fixtures (cli_runner, mock_beads_task, work_command_mocks)
2. `tests/core/conftest.py` - Core module fixtures (sample_beads_task, subprocess mocks)
3. `tests/orchestration/conftest.py` - Workflow fixtures (workflow_state, execution_result)

**Before creating a new fixture:**
```bash
# Search existing fixtures
grep -r "@pytest.fixture" tests/conftest.py tests/*/conftest.py
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

### Test Organization

**File Mapping:**
- `src/jean_claude/core/foo.py` → `tests/core/test_foo.py`
- `src/jean_claude/cli/commands/bar.py` → `tests/test_bar.py`

**Test Consolidation:**
Prefer comprehensive tests over many narrow tests:

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

### Running Tests

```bash
# All tests (parallel, 4 workers)
uv run pytest

# Specific module
uv run pytest tests/core/test_state.py

# Filter by name
uv run pytest -k "mailbox"

# With coverage
uv run pytest --cov=jean_claude

# Single-threaded (for debugging)
uv run pytest -n 0
```

## Common Pitfalls

### 1. AsyncMock vs Mock
**Problem:** Using regular `Mock` for async functions causes errors.
**Solution:** Always use `new_callable=AsyncMock` for async functions.

### 2. Patch Location
**Problem:** Patching where defined instead of where used.
**Solution:** Patch in the module that imports the function, not the source module.

### 3. Fixture Duplication
**Problem:** Creating fixtures that already exist in conftest.py files.
**Solution:** Search all conftest.py files before creating new fixtures.

### 4. Testing External Tools
**Problem:** Testing Beads/SDK behavior instead of our integration.
**Solution:** Mock external tools and test only our wrapper code.

### 5. Nested Mocking
**Problem:** Using nested `with patch()` blocks instead of decorators.
**Solution:** Use `@patch` decorators in bottom-up order.

### 6. Parallel Test State
**Problem:** Tests failing intermittently due to shared state.
**Solution:** Avoid shared state; use temporary directories and unique identifiers.

### 7. ABOUTME Comments
**Problem:** Forgetting to add ABOUTME comments to new files.
**Solution:** Every file needs 2-line ABOUTME comment at the top.

## Active Experiments

### Agent Note-Taking System
**Status:** In development (branch: `claude/agent-note-taking-system-Ly16E`)
**Purpose:** Allow agents to take notes during execution that other agents can read
**Key Files:**
- `src/jean_claude/core/notes.py`
- `src/jean_claude/core/notes_api.py`
- `src/jean_claude/tools/notes_tools.py`

**Design Questions:**
- How should notes be categorized? (OBSERVATION, LEARNING, DECISION)
- Should notes persist across workflows or be workflow-specific?
- How do we prevent note bloat?

### Dashboard Memory Optimization
**Status:** Recently fixed (v0.9.0)
**Problem:** SSE streaming endpoint had memory leaks
**Solution:** Proper cleanup of background tasks and event listeners
**Lesson:** Always test long-running streams for memory leaks

### Skill-Based Documentation
**Status:** Experimenting (this skill!)
**Purpose:** Capture project-specific knowledge in skills vs CLAUDE.md
**Hypothesis:** Living skills updated via `/retrospective` will maintain better context than static docs

## Retrospective Insights

### Session: 2026-01-04 - Dashboard Memory Leak Fix
**What we learned:**
- SSE streaming requires careful cleanup of background tasks
- Memory leaks manifest slowly in long-running processes
- Dashboard testing should include stress tests

**Code patterns discovered:**
```python
# ✅ GOOD - Proper SSE cleanup
async def event_stream():
    try:
        async for event in event_source:
            yield event
    finally:
        await event_source.cleanup()
```

### Session: Testing Pattern Consolidation
**What we learned:**
- Mock patching location matters more than we thought
- Fixture hierarchy prevents duplication but requires discovery
- Comprehensive tests > many narrow tests

**Changes made:**
- Added fixture search guidance to CLAUDE.md
- Consolidated duplicate test fixtures
- Documented patch location rule

## Development Workflows

### Adding a New CLI Command

1. **Create command module:** `src/jean_claude/cli/commands/my_command.py`
2. **Define Click command:**
   ```python
   import click

   @click.command()
   @click.argument('arg_name')
   def my_command(arg_name: str):
       """Brief description."""
       pass
   ```
3. **Register in main.py:** Add to `cli.add_command(my_command)`
4. **Write tests:** `tests/test_my_command.py` using `cli_runner` fixture
5. **Update CLAUDE.md:** Add to Quick Reference table

### Adding a New Agent Tool

1. **Define tool in:** `src/jean_claude/tools/my_tools.py`
2. **Follow MCP tool pattern:**
   ```python
   @server.tool()
   def my_tool(param: str) -> str:
       """Tool description."""
       return result
   ```
3. **Register in SDK executor:** Update `get_mcp_servers()` in `sdk_executor.py`
4. **Write tests:** Mock the tool execution, test integration
5. **Update skill:** Add tool documentation to `jean-claude-cli` skill

### Updating Event Store Schema

1. **Review:** `src/jean_claude/core/event_store.py`
2. **Add new event type:** Update `EventType` enum
3. **Update schema:** Modify `initialize_event_store()` if needed
4. **Migration:** Consider if existing events need migration
5. **Test:** Add tests in `tests/core/test_event_store.py`

### Working with Beads Integration

1. **Beads models:** `src/jean_claude/core/beads.py`
2. **Mock in tests:** Use `mock_beads_task` or `sample_beads_task` fixtures
3. **Spec generation:** Specs auto-created in `specs/beads-{task_id}.md`
4. **State linking:** WorkflowState includes `beads_task_id` field

## Resources

This skill includes:

### references/
- `testing_patterns.md` - Detailed testing examples and fixture catalog
- `retrospectives/` - Session-by-session learnings (created via `/retrospective`)

### scripts/
- `retrospective_helper.py` - Analyzes recent commits to suggest skill updates

**Note:** Assets directory not needed for this skill and has been removed.

## Updating This Skill

This skill should evolve as Jean Claude develops. To update:

1. **Use `/retrospective` command** - Reflect on recent work and update skill
2. **Manual updates** - Edit this SKILL.md directly when discovering new patterns
3. **Reference files** - Add detailed examples to `references/` to keep SKILL.md lean
4. **Commit changes** - This skill is part of the project repository

**Meta-learning loop:**
```
Development → Retrospective → Skill Update → Better Development
```
