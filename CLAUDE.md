# Jean Claude - AI Developer Workflows

Programmatic Claude Code orchestration with Beads issue tracking.

## Quick Reference

| Task | Command |
|------|---------|
| Run tests | `uv run pytest tests/` |
| Find work | `bd ready` |
| Create task | `bd create "Title" --type task --priority 2` |
| Close task | `bd close <id>` |
| Two-agent workflow | `jc workflow "description"` |
| Sync issues | `bd sync` |

For beads context: `bd prime`

## Architecture

**Two-layer design**: Agentic Layer (`adws/`, `.claude/commands/`) operates on Application Layer (`src/jean_claude/`).

```
src/jean_claude/
├── core/           # agent.py, sdk_executor.py, state.py, security.py
├── orchestration/  # two_agent.py, auto_continue.py
├── cli/            # Click commands (main.py, commands/)
└── integrations/   # Git, VCS plugins
```

## Development Patterns

1. **TDD**: Write tests before implementation
2. **ABOUTME**: All files start with 2-line `# ABOUTME:` comment
3. **Fixtures**: Use `tests/conftest.py` fixtures, never nested `with patch()` blocks
4. **AsyncMock**: Use for async functions (not `Mock`)
5. **Click CLI**: All commands use Click framework
6. **Pydantic Models**: All data types use Pydantic v2

## Test Guidelines (CRITICAL FOR AGENTS)

### What NOT to Test (CRITICAL)

**DO NOT write tests for external tools or libraries. We only test OUR code.**

- ❌ **Beads CLI** (`bd` commands) - External tool, not our code
- ❌ **Beads models/data structures** - Their implementation, not ours
- ❌ **Any external API behavior** - We mock these, not test them
- ✅ **Our CLI commands** - `jc work`, `jc prompt`, etc.
- ✅ **Our integration points** - How we CALL external tools (mocked)
- ✅ **Our business logic** - Workflows, state management, etc.

**Beads is a moving target under active development. Testing it is wasted effort.**

### BEFORE writing any test, you MUST:

1. **Ask: Is this OUR code?** If testing an external tool → STOP
2. **Search for existing tests**: `grep -r "def test_.*{keyword}" tests/`
3. **Check for existing fixtures**: Read `tests/conftest.py` and `tests/core/conftest.py`
4. **Reuse existing patterns**: Look at similar test files for patterns

### Fixture Usage (Required)

```python
# GOOD - Use shared fixtures
def test_something(sample_beads_task, mock_subprocess_success):
    result = my_function(sample_beads_task)
    assert result.success

# BAD - Inline creation (creates duplicates)
def test_something():
    task = BeadsTask(id="test", title="Test", ...)  # DON'T DO THIS
```

### Mock Patterns (Required)

```python
# GOOD - Use @patch decorators
@patch('module.function_c')
@patch('module.function_b')
@patch('module.function_a')
def test_thing(mock_a, mock_b, mock_c):
    pass

# BAD - Nested with patch() blocks
def test_thing():
    with patch('a'):
        with patch('b'):
            with patch('c'):  # DON'T NEST LIKE THIS
                pass
```

### Mock Patching Rule (CRITICAL)

**Always patch where an object is USED, not where it's DEFINED.**

```python
# If edit_and_revalidate.py has:
# from jean_claude.core.beads import fetch_beads_task

# CORRECT - patch in the importing module
@patch('jean_claude.core.edit_and_revalidate.fetch_beads_task')
def test_something(mock_fetch):
    pass

# WRONG - patching in the source module won't work
@patch('jean_claude.core.beads.fetch_beads_task')  # DON'T DO THIS
def test_something(mock_fetch):
    pass
```

### Available Fixtures

**Root fixtures (tests/conftest.py)**:
| Fixture | Purpose |
|---------|---------|
| `cli_runner` | Click CLI testing |
| `mock_beads_task` | Standard BeadsTask |
| `mock_beads_task_factory` | Factory for custom BeadsTask |
| `work_command_mocks` | All mocks for work command |
| `mock_task_validator` | TaskValidator mock for validation tests |

**Core fixtures (tests/core/conftest.py)**:
| Fixture | Purpose |
|---------|---------|
| `sample_beads_task` | Fully-populated BeadsTask |
| `minimal_beads_task` | BeadsTask with only required fields |
| `beads_task_factory` | Factory for custom BeadsTask |
| `mock_subprocess_success` | Subprocess mock returning success |
| `mock_subprocess_failure` | Subprocess mock returning failure |
| `valid_beads_json` / `invalid_beads_json` | JSON response fixtures |

**Orchestration fixtures (tests/orchestration/conftest.py)**:
| Fixture | Purpose |
|---------|---------|
| `mock_project_root` | Temp project directory with agents/ |
| `sample_workflow_state` | Pre-configured WorkflowState with features |
| `mock_execution_result` | Successful ExecutionResult |
| `workflow_state_factory` | Factory for custom WorkflowState |

**Template fixtures (tests/templates/conftest.py)**:
| Fixture | Purpose |
|---------|---------|
| `template_path` | Path to beads_spec.md template |
| `templates_dir` | Path to templates directory |

### Test File Organization

- Tests for `src/jean_claude/core/foo.py` → `tests/core/test_foo.py`
- Tests for `src/jean_claude/cli/commands/bar.py` → `tests/test_bar.py`
- **NEVER create duplicate test files** - check if one exists first!

### Naming Conventions

```python
# Test class: Test{ClassName}{Feature}
class TestBeadsTaskValidation:
    # Test method: test_{action}_{condition}_{expected_result}
    def test_validate_empty_id_raises_error(self):
        pass
```

### Test Consolidation Principles

**One comprehensive test beats five narrow tests.**

| Anti-Pattern | Correct Pattern |
|--------------|-----------------|
| Separate tests for each priority (LOW/NORMAL/URGENT) | One parameterized test covering all |
| Separate tests for each keyword (test/verify/validate) | One test with all keywords |
| Testing Click flag parsing (18 tests for flags!) | Trust Click, test 2-3 essential behaviors |
| Duplicate fixtures in each test class | Shared fixtures in conftest.py |
| Testing inbox and outbox separately | One test covering both |

```python
# GOOD - Comprehensive test with multiple assertions
def test_read_messages_preserves_all_fields(self, tmp_path):
    """Test all message fields including priority and awaiting_response."""
    for priority in [MessagePriority.LOW, MessagePriority.NORMAL, MessagePriority.URGENT]:
        for awaiting in [True, False]:
            msg = Message(..., priority=priority, awaiting_response=awaiting)
            write_message(msg, MessageBox.INBOX, paths)

    messages = read_messages(MessageBox.INBOX, paths)
    assert len(messages) == 6
    priorities_found = {m.priority for m in messages}
    assert MessagePriority.LOW in priorities_found
    assert MessagePriority.URGENT in priorities_found

# BAD - Separate tests for each variation
def test_read_urgent_priority(self): ...
def test_read_normal_priority(self): ...
def test_read_low_priority(self): ...
def test_awaiting_response_true(self): ...
def test_awaiting_response_false(self): ...
```

**Don't test framework behavior:**
- ❌ Click flag parsing, option validation
- ❌ Pydantic field defaults, serialization
- ❌ pytest fixture mechanics
- ✅ Our business logic that USES these frameworks

## Key Files

| Purpose | Location |
|---------|----------|
| CLI entry point | `src/jean_claude/cli/main.py:14` |
| SDK executor | `src/jean_claude/core/sdk_executor.py` |
| Two-agent workflow | `src/jean_claude/orchestration/two_agent.py` |
| Security hooks | `src/jean_claude/core/security.py` |
| Test fixtures | `tests/conftest.py` |
| Slash commands | `.claude/commands/*.md` |

## Docs (Progressive Disclosure)

- [Testing Patterns](docs/testing.md) - Fixtures, TDD, async mocks
- [Beads Workflow](docs/beads-workflow.md) - Issue tracking integration
- [Two-Agent Workflow](docs/two-agent-workflow.md) - Opus plans, Sonnet codes
- [Security Hooks](docs/security-hooks-implementation.md) - Bash command validation
- [Auto-Continue](docs/auto-continue-workflow.md) - Autonomous continuation
- [Streaming](docs/streaming-implementation-summary.md) - Real-time output

## ADW Scripts

Executable workflow scripts in `adws/`:
- `adw_prompt.py` - Ad-hoc prompts
- `adw_slash_command.py` - Execute slash commands
- `adw_chore_implement.py` - Plan + implement
- `adw_plan_tdd.py` - TDD task breakdown
- `adw_beads_ready.py` - Interactive task picker

## Output Locations

- Agent outputs: `agents/{adw_id}/{agent_name}/`
- Specs/plans: `specs/` and `specs/plans/`
- Worktrees: `trees/` (gitignored)
