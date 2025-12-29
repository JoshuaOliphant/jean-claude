# Extract duplicate workflow iteration pattern

## Description

## Problem
Same 20-line workflow iteration pattern duplicated in THREE files:
1. status.py:59-87
2. logs.py (similar pattern)
3. dashboard/app.py:47-72

## Files to Modify
1. Add to: src/jean_claude/core/workflow_utils.py (add get_all_workflows function)
2. Modify: src/jean_claude/cli/commands/status.py
3. Modify: src/jean_claude/cli/commands/logs.py  
4. Modify: src/jean_claude/dashboard/app.py

## Implementation
### Add to workflow_utils.py
```python
def get_all_workflows(project_root: Path) -> list[WorkflowState]:
    """Load all workflow states from agents directory.
    
    Returns list of WorkflowState objects, ignoring invalid/corrupted states.
    """
    from jean_claude.core.state import WorkflowState
    
    agents_dir = project_root / 'agents'
    if not agents_dir.exists():
        return []
    
    workflows = []
    for workflow_dir in agents_dir.iterdir():
        if not workflow_dir.is_dir():
            continue
        
        state_file = workflow_dir / 'state.json'
        if not state_file.exists():
            continue
        
        try:
            state = WorkflowState.load_from_file(state_file)
            workflows.append(state)
        except Exception:
            # Skip corrupted state files
            continue
    
    return workflows
```

### Update all 3 files to use utility
Replace iteration logic with:
```python
from jean_claude.core.workflow_utils import get_all_workflows

workflows = get_all_workflows(project_root)
```

## Acceptance Criteria
- [ ] get_all_workflows() added to workflow_utils.py
- [ ] status.py simplified to use utility
- [ ] logs.py simplified to use utility
- [ ] dashboard/app.py simplified to use utility
- [ ] ~60 lines of duplicate code removed
- [ ] Tests pass: uv run pytest -v
- [ ] Add tests for get_all_workflows()

## Test Requirements
Add to tests/test_workflow_utils.py:
```python
def test_get_all_workflows_empty_directory(tmp_path):
def test_get_all_workflows_valid_states(tmp_path):
def test_get_all_workflows_skips_corrupted_files(tmp_path):
def test_get_all_workflows_skips_non_directories(tmp_path):
```

## Dependencies
⚠️ DEPENDS ON: jean_claude-yih (Extract find_most_recent_workflow)
  - Both functions belong in workflow_utils.py
  - Can work simultaneously if coordinating

## Agent Notes
🟠 HIGH PRIORITY
📬 Coordinate with agent working on jean_claude-yih via mailbox
📬 Send message if workflow_utils.py doesn't exist yet
🧪 Comprehensive tests for edge cases
✅ 60+ lines of duplication removed

## Time Estimate
Agent: ~2 hours

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-do0
- **Status**: in_progress
- **Created**: 2025-12-28 17:15:21
- **Updated**: 2025-12-28 18:49:03
