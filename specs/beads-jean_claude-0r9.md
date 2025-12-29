# Remove Click framework tests from test suite

## Description

## Problem
Multiple test files test Click's framework behavior instead of our business logic. Per CLAUDE.md lines 41-52, we should NOT test external libraries.

## Files to Modify
- tests/test_work_command.py (lines 28-68)
- tests/test_status_command.py (help/arg tests)
- tests/test_logs_command.py (help/arg tests)
- tests/test_dashboard.py (help tests if any)

## Tests to Remove
1. --help output validation tests
2. Required argument validation tests
3. Click option parsing tests

## Keep These Tests
✅ Tests of OUR command logic
✅ Tests of business workflows
✅ Tests of our validation functions

## Acceptance Criteria
- [ ] All Click framework tests removed
- [ ] Only our business logic tests remain
- [ ] Test suite still passes: uv run pytest -v
- [ ] Test count reduced but coverage maintained

## Agent Notes
⚡ QUICK WIN - ~1 hour
✅ No dependencies
📬 Mailbox: Send count of tests removed
🧪 Run full test suite after removal

## Time Estimate
Agent: ~30 minutes

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-0r9
- **Status**: open
- **Created**: 2025-12-28 17:11:07
- **Updated**: 2025-12-28 17:11:07
