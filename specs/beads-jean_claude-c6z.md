# Fix over-broad exception catching in auto_continue.py

## Description

## Problem
orchestration/auto_continue.py:365-368 catches ALL exceptions (including KeyboardInterrupt!), hiding critical bugs and preventing proper error handling.

## Files to Modify
- src/jean_claude/orchestration/auto_continue.py (lines 365-368)

## Current Code
```python
except Exception as e:  # TOO BROAD!
    state.mark_feature_failed(str(e))
    console.print(f'✗ Exception during feature execution: {e}')
    break
```

## Fix
```python
except (ClaudeSDKError, ProcessError, ValidationError, RuntimeError) as e:
    state.mark_feature_failed(str(e))
    logger.error(f'Feature failed: {e}', exc_info=True)
    console.print(f'✗ Feature execution failed: {e}')
    break
except KeyboardInterrupt:
    logger.info('User interrupted execution')
    raise
except Exception as e:
    logger.critical(f'Unexpected error in auto_continue: {e}', exc_info=True)
    state.mark_feature_failed(f'Unexpected error: {e}')
    raise  # Re-raise unexpected errors for debugging
```

## Acceptance Criteria
- [ ] Import logging module
- [ ] Specific exception types caught first
- [ ] KeyboardInterrupt handled separately
- [ ] Unexpected exceptions re-raised with logging
- [ ] Tests pass: uv run pytest tests/orchestration/test_auto_continue.py -v
- [ ] Add test for KeyboardInterrupt handling

## Dependencies
None - can start immediately

## Agent Notes
🔴 CRITICAL - Affects production stability
📬 Use mailbox if questions about which exceptions to catch
🧪 Add test case for unexpected exception propagation

## Time Estimate
Agent: ~45 minutes (includes test addition)

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-c6z
- **Status**: open
- **Created**: 2025-12-28 17:11:32
- **Updated**: 2025-12-28 17:11:32
