# Implement jc work Command

**Beads Task**: jean_claude-2sz.3
**Priority**: P0
**Type**: task

## Overview

Create the main entry point for Beads-driven workflows. This command takes a Beads task ID, fetches the task details, and orchestrates the agent to autonomously implement it.

## Command Interface

```bash
jc work <beads-id>              # Autonomous execution
jc work <beads-id> --show-plan  # Show proposed features before implementing
jc work <beads-id> --dry-run    # Plan only, don't implement
jc work <beads-id> --model opus # Use Opus for both agents
```

## Implementation Requirements

### 1. CLI Command (src/jean_claude/cli/commands/work.py)

Create new Click command with:
- `beads_id` argument (required)
- `--show-plan` flag to pause after planning for approval
- `--dry-run` flag to plan without implementing
- `--model` option to override agent models (default: sonnet)
- `--auto-confirm` flag to skip confirmation prompts

### 2. Beads Integration (src/jean_claude/core/beads.py)

Create utilities for Beads interaction:
- `fetch_beads_task(task_id: str) -> BeadsTask` - Run `bd show --json` and parse
- `update_beads_status(task_id: str, status: str)` - Run `bd update --status`
- `close_beads_task(task_id: str)` - Run `bd close`
- `BeadsTask` Pydantic model with id, title, description, acceptance_criteria, status

### 3. Spec Generation

Create `generate_spec_from_beads(task: BeadsTask) -> str`:
- Format task as markdown spec compatible with `jc workflow`
- Include title, description, acceptance criteria
- Structure for agent consumption

### 4. Workflow Integration

The work command should:
1. Fetch Beads task details
2. Generate spec file at `specs/beads-{task_id}.md`
3. Update Beads status to `in_progress`
4. Set WorkflowState.beads_task_id and beads_task_title
5. Update WorkflowState.phase through transitions
6. Call existing `jc workflow` machinery
7. Close Beads task on success

### 5. Event Integration

Emit events using EventLogger:
- `workflow.started` when work begins
- `workflow.phase_changed` on phase transitions
- `workflow.completed` when finished

## Files to Create

1. `src/jean_claude/cli/commands/work.py` - CLI command
2. `src/jean_claude/core/beads.py` - Beads integration utilities
3. `tests/test_beads.py` - Tests for Beads integration
4. `tests/test_work_command.py` - Tests for work command

## Files to Modify

1. `src/jean_claude/cli/main.py` - Register work command

## Test Requirements

- Test BeadsTask model creation and validation
- Test fetch_beads_task with mocked subprocess
- Test generate_spec_from_beads output format
- Test work command argument parsing
- Test --dry-run doesn't execute implementation
- Test --show-plan pauses for confirmation
- Test Beads status updates at lifecycle points
- Test WorkflowState gets beads_task_id populated

## Acceptance Criteria

- [ ] jc work <beads-id> command implemented
- [ ] --show-plan flag pauses after planning for approval
- [ ] --dry-run flag plans without implementing
- [ ] --model flag to override agent models
- [ ] Auto-generate spec file from Beads task details
- [ ] Store beads_task_id and beads_task_title in WorkflowState
- [ ] Update phase field through planning/implementing/verifying/complete
- [ ] Events emitted for workflow/feature transitions
- [ ] Beads task status updated (in_progress -> closed on success)
- [ ] Tests for CLI command and Beads integration
