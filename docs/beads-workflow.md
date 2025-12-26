# ABOUTME: Beads issue tracking integration for Jean Claude
# ABOUTME: Documents bd commands, workflows, and ADW integration

# Beads Workflow Guide

## Why Beads?

- **Offline-first**: No internet required
- **SQLite-based**: Simple, portable database
- **Dependency tracking**: Automatic blocker detection
- **Priority management**: P0, P1, P2, P3
- **Status workflow**: open -> in_progress -> blocked -> closed

## Quick Reference

```bash
# See what's ready to work on
bd ready

# Create new task
bd create "Task title" --type task --priority 2

# Update status
bd update <id> --status in_progress

# View task details
bd show <id>

# Close completed task
bd close <id>

# List all tasks
bd list

# Sync with git (run at session end)
bd sync

# Get workflow context
bd prime
```

## Task Types

| Type | Use For |
|------|---------|
| `task` | General work items |
| `feature` | New functionality |
| `bug` | Defect fixes |
| `chore` | Maintenance, refactoring |

## Priority Levels

| Priority | Meaning |
|----------|---------|
| P0 | Critical - do immediately |
| P1 | High - do soon |
| P2 | Medium - normal queue |
| P3 | Low - when time permits |

## Status Workflow

```
open -> in_progress -> closed
           |
           v
        blocked -> in_progress -> closed
```

## ADW Integration

The ADW system automatically integrates with Beads:

### Fetching Tasks

```python
# In adw_modules/beads_integration.py
from jean_claude.core.beads import fetch_beads_task

task = fetch_beads_task("task.123")
```

### Status Updates

```python
from jean_claude.core.beads import update_beads_status

update_beads_status("task.123", "in_progress")
```

### Workflow Pattern

```bash
# 1. Find ready work
bd ready

# 2. Start working (status auto-updates)
jc work task.123

# 3. Or use ADW scripts directly
./adws/adw_beads_ready.py  # Interactive picker

# 4. Mark complete
bd close task.123
```

## Dependency Management

```bash
# Block a task on another
bd block task.123 task.456  # 123 blocked by 456

# Unblock
bd unblock task.123 task.456

# View blockers
bd show task.123  # Shows blocking tasks
```

## Integration with Specs

When working on a beads task, specs are generated at:
- `specs/task-{project}-{id}.md`
- `specs/feature-{project}-{id}.md`
- `specs/bug-{project}-{id}.md`

## Hooks Setup

For automatic context injection:

```bash
bd hooks install
```

This adds beads context to Claude sessions automatically via `bd prime`.
