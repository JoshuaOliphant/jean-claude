# Implement jc status Command

**Beads Task**: jean_claude-2sz.4
**Priority**: P1
**Type**: task

## Overview

Create a CLI command to check the status of running or completed workflows. This enables both humans and Claude to quickly check workflow progress.

## Command Interface

```bash
jc status                    # Show current/most recent workflow
jc status <workflow-id>      # Show specific workflow
jc status --json             # Machine-readable output for scripting
jc status --all              # List all workflows with summary
```

## Output Format (human-readable)

```
Workflow: jean_claude-abc123
Task: Add user authentication [P0, feature]
Phase: implementing
Progress: ████████░░░░ 4/7 features (57%)

Features:
  ✓ Create User model              2m 14s
  ✓ Add password hashing           1m 03s
  ✓ Implement registration         3m 45s
  → Implement login endpoint       1m 22s (in progress)
  ○ Add JWT middleware             pending
  ○ Protect routes                 pending
  ○ Add refresh tokens             pending

Duration: 8m 23s | Cost: $0.42
```

## Implementation Requirements

### 1. CLI Command (src/jean_claude/cli/commands/status.py)

Create new Click command with:
- Optional `workflow_id` argument (defaults to most recent)
- `--json` flag for machine-readable output
- `--all` flag to list all workflows
- `--verbose` flag for detailed feature info

### 2. Status Data Sources

Read data from:
- `agents/{workflow_id}/state.json` - WorkflowState with features
- `agents/{workflow_id}/events.jsonl` - Event log for timing
- `.jc/events.db` - SQLite event store (optional fallback)

### 3. Status Display

Implement rich console output:
- Progress bar with percentage
- Feature list with status icons (✓, →, ○, ✗)
- Duration per feature (from events)
- Total duration and cost

### 4. JSON Output

For `--json` flag, output structured data:
```json
{
  "workflow_id": "...",
  "phase": "implementing",
  "features": [...],
  "completed": 4,
  "total": 7,
  "duration_ms": 503000,
  "cost_usd": 0.42
}
```

## Files to Create

1. `src/jean_claude/cli/commands/status.py` - CLI command
2. `tests/test_status_command.py` - Tests for status command

## Files to Modify

1. `src/jean_claude/cli/main.py` - Register status command

## Test Requirements

**IMPORTANT: Use pytest fixtures from tests/conftest.py**

When writing tests:
- Use `cli_runner` fixture instead of creating `CliRunner()`
- Use `tmp_path` instead of `isolated_filesystem()` when possible
- Use `@patch` decorators instead of nested `with patch()` blocks
- Use `mock_beads_task_factory` for creating test data

Example test pattern:
```python
def test_status_shows_workflow(cli_runner, tmp_path):
    # Setup test state file
    state_dir = tmp_path / "agents" / "test-workflow"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text('{"workflow_id": "test-workflow", ...}')

    with cli_runner.isolated_filesystem(temp_dir=tmp_path):
        result = cli_runner.invoke(status, [])

    assert result.exit_code == 0
    assert "test-workflow" in result.output
```

## Acceptance Criteria

- [ ] jc status shows current workflow
- [ ] jc status <id> shows specific workflow
- [ ] --json flag outputs machine-readable format
- [ ] --all flag lists all workflows
- [ ] Shows feature progress with status icons
- [ ] Shows duration and cost metrics
- [ ] Works for both running and completed workflows
- [ ] Tests use fixtures from conftest.py (no nested patches)
