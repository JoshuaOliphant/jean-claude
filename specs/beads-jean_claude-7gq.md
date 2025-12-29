# Add logging to silent hook failures

## Description

## Problem
Three hook functions silently swallow ALL exceptions with no logging, making debugging impossible.

## Files to Modify
1. src/jean_claude/orchestration/post_tool_use_hook.py (lines 127-130)
2. src/jean_claude/orchestration/user_prompt_submit_hook.py (lines 102-105)
3. src/jean_claude/orchestration/subagent_stop_hook.py (lines 90-93)

## Current Pattern (All 3 Files)
```python
except Exception:
    # Gracefully handle any errors
    return None  # SILENT FAILURE!
```

## Fix (All 3 Files)
```python
except Exception as e:
    logger.error(
        f'Hook execution failed: {e}',
        exc_info=True,
        extra={'hook': __name__}
    )
    return None  # Still graceful, but logged
```

## Acceptance Criteria
- [ ] Import logging in all 3 files
- [ ] All exception handlers add logging
- [ ] Use exc_info=True for stack traces
- [ ] Tests pass: uv run pytest tests/orchestration/ -v
- [ ] Add test cases that verify logging calls on errors

## Test Requirements
For each hook file, add test:
```python
def test_hook_logs_exception_on_error(caplog):
    # Trigger error condition
    # Assert error was logged with exc_info
```

## Dependencies
None - can work in parallel with other tasks

## Agent Notes
🔴 CRITICAL - Debugging blocker
📬 Send message when all 3 hooks updated
🧪 MUST add logging verification tests
⚡ Can work on all 3 files simultaneously

## Time Estimate
Agent: ~1 hour (3 files + 3 test updates)

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-7gq
- **Status**: open
- **Created**: 2025-12-28 17:11:53
- **Updated**: 2025-12-28 17:11:53
