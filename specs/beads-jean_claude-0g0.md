# Remove private function imports from orchestration modules

## Description

## Problem
Two orchestration modules import _execute_prompt_sdk_async (PRIVATE function) from core/agent.py. This creates tight coupling and will break if the private function changes.

## Files to Modify
1. src/jean_claude/orchestration/auto_continue.py (line 39)
2. src/jean_claude/orchestration/two_agent.py (line 41)

## Current Problematic Imports
```python
from jean_claude.core.agent import _execute_prompt_sdk_async  # PRIVATE!
```

## Fix
The public API already exists in sdk_executor.py!

```python
# BEFORE:
from jean_claude.core.agent import _execute_prompt_sdk_async

# AFTER:
from jean_claude.core.sdk_executor import execute_prompt_async
```

## Update Function Calls
Search for all uses of _execute_prompt_sdk_async and replace with execute_prompt_async.

Note: The function signatures are identical, so this should be a straightforward find-replace.

## Acceptance Criteria
- [ ] auto_continue.py imports execute_prompt_async from sdk_executor
- [ ] two_agent.py imports execute_prompt_async from sdk_executor
- [ ] All calls to _execute_prompt_sdk_async replaced
- [ ] No imports of private functions (search for "import _")
- [ ] Tests pass: uv run pytest tests/orchestration/ -v
- [ ] No ruff errors

## Verification
Run grep to ensure no private imports remain:
```bash
grep -r 'import _' src/jean_claude/orchestration/
# Should return NOTHING
```

## Dependencies
None - can start immediately

## Agent Notes
🔴 CRITICAL - Breaking dependency
📬 Message when both files updated
✅ Simple find-replace task
⚡ Should take ~30 minutes

## Time Estimate
Agent: ~30 minutes

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-0g0
- **Status**: open
- **Created**: 2025-12-28 17:16:19
- **Updated**: 2025-12-28 17:16:19
