# Fix dead exception handler in work.py

## Description

## Problem
work.py:391-396 has unreachable dead code. RuntimeError is a subclass of Exception, so the second handler never executes.

## Files to Modify
- src/jean_claude/cli/commands/work.py (lines 391-396)

## Fix
Remove the second Exception handler since it's unreachable:
```python
# BEFORE:
except RuntimeError as e:
    console.print(...)
    raise click.Abort()
except Exception as e:  # DEAD - never reached
    console.print(...)
    raise click.Abort()

# AFTER:
except RuntimeError as e:
    console.print(...)
    raise click.Abort()
```

## Acceptance Criteria
- [ ] Second Exception handler removed
- [ ] Tests pass: uv run pytest tests/test_work_command.py -v
- [ ] No ruff errors: uv run ruff check src/jean_claude/cli/commands/work.py

## Agent Notes
⚡ QUICK WIN - 15 minutes
✅ No dependencies - can start immediately
📬 Use mailbox to report completion: jc send-message 'Quick win completed: dead code removed'

## Time Estimate
Agent execution: ~10 minutes (including tests)

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-kon
- **Status**: open
- **Created**: 2025-12-28 17:09:46
- **Updated**: 2025-12-28 17:09:46
