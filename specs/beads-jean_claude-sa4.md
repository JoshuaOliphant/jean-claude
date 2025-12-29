# Consolidate duplicate test fixtures into conftest.py

## Description

## Problem
Per CLAUDE.md lines 61-72, tests should use shared fixtures from conftest.py. Multiple test files create inline fixtures that duplicate existing ones.

## Duplicate Fixtures Found

### BeadsTask Duplicates
1. tests/test_spec_generation.py:20-30 → basic_task (duplicates mock_beads_task)
2. tests/test_task_validator.py:103-106 → inline BeadsTask creation
3. tests/test_task_validator.py:186+ → another inline BeadsTask

### Message Duplicates
1. tests/core/test_message_writer.py:81-100 → inline Message (duplicates message_factory)
2. tests/core/test_message_writer.py:176-253 → multiple inline Messages

### WorkflowState Duplicates
1. tests/test_status_command.py:38-47 → mock_workflow_state_data (duplicates mock_workflow_state)

## Files to Modify
- tests/test_spec_generation.py (remove basic_task, use mock_beads_task)
- tests/test_task_validator.py (use beads_task_factory instead)
- tests/core/test_message_writer.py (use message_factory instead)
- tests/test_status_command.py (use mock_workflow_state instead)

## Implementation

### Replace inline fixtures with shared ones:

```python
# BEFORE (test_spec_generation.py):
@pytest.fixture
def basic_task():
    return BeadsTask(...)

def test_something(basic_task):
    ...

# AFTER:
def test_something(mock_beads_task):  # Use shared fixture\!
    ...
```

### Use factories for variations:
```python
# BEFORE:
def test_invalid_task():
    task = BeadsTask(id='', title='Test')  # Inline creation\!
    
# AFTER:
def test_invalid_task(beads_task_factory):
    task = beads_task_factory(id='', title='Test')  # Use factory\!
```

## Shared Fixtures Available (from conftest.py)
- mock_beads_task / beads_task_factory → Use for BeadsTask
- sample_message / message_factory → Use for Message
- mock_workflow_state / workflow_state_factory → Use for WorkflowState

## Acceptance Criteria
- [ ] All inline BeadsTask() constructors removed
- [ ] All inline Message() constructors removed
- [ ] All duplicate fixtures removed
- [ ] Tests use shared fixtures from conftest.py
- [ ] Tests pass: uv run pytest -v
- [ ] 13+ fixture definitions reduced to 3 shared ones

## Verification
```bash
# Should find NO inline BeadsTask constructors in tests:
grep 'BeadsTask(' tests/*.py tests/**/*.py | grep -v conftest.py | grep -v 'import'
```

## Dependencies
None - can work in parallel

## Agent Notes
🟡 MEDIUM PRIORITY
📬 Message with count of duplicates removed
✅ Break by file: 1) test_spec_generation 2) test_task_validator 3) test_message_writer 4) test_status_command
🧪 Run tests after each file to ensure fixtures work
⚡ Per CLAUDE.md: This is REQUIRED for test maintainability

## Time Estimate
Agent: ~2 hours

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-sa4
- **Status**: open
- **Created**: 2025-12-28 17:17:15
- **Updated**: 2025-12-28 17:17:15
