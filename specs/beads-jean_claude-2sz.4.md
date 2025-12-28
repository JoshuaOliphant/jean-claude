# Implement jc status command

## Description

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

## Context
- Read from WorkflowState files in agents/{id}/
- Query events.db for timing/metrics
- Should work even while workflow is running

## Acceptance Criteria

- jc status shows current workflow
- jc status <id> shows specific workflow
- json flag outputs machine-readable format
- Shows feature progress with status icons
- Shows duration and cost metrics
- Works for both running and completed workflows
