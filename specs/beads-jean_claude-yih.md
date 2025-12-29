# Extract duplicate find_most_recent_workflow function

## Description

## Problem
find_most_recent_workflow() is defined identically in TWO files with slightly different implementations:
- status.py uses state.json mtime
- logs.py uses events.jsonl mtime

## Files to Modify
1. Create: src/jean_claude/core/workflow_utils.py (NEW FILE)
2. Modify: src/jean_claude/cli/commands/status.py (remove lines 24-56)
3. Modify: src/jean_claude/cli/commands/logs.py (remove lines 82-111)

## Implementation
### workflow_utils.py (NEW)
```python
# ABOUTME: Workflow discovery and management utilities
# ABOUTME: Shared functions for finding and listing workflows

from pathlib import Path

def find_most_recent_workflow(project_root: Path) -> str | None:
    """Find most recent workflow by checking both state.json AND events.jsonl.
    
    Returns workflow_id of most recently modified workflow, or None if none exist.
    """
    agents_dir = project_root / 'agents'
    if not agents_dir.exists():
        return None
    
    candidates = []
    for workflow_dir in agents_dir.iterdir():
        if not workflow_dir.is_dir():
            continue
        
        # Check both state.json and events.jsonl
        state_file = workflow_dir / 'state.json'
        events_file = workflow_dir / 'events.jsonl'
        
        mtime = 0
        if state_file.exists():
            mtime = max(mtime, state_file.stat().st_mtime)
        if events_file.exists():
            mtime = max(mtime, events_file.stat().st_mtime)
        
        if mtime > 0:
            candidates.append((workflow_dir.name, mtime))
    
    if not candidates:
        return None
    
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]
```

### Update imports in status.py and logs.py
```python
from jean_claude.core.workflow_utils import find_most_recent_workflow
```

## Acceptance Criteria
- [ ] workflow_utils.py created with proper ABOUTME comments
- [ ] Unified implementation uses BOTH state.json and events.jsonl
- [ ] Both status.py and logs.py import from new module
- [ ] Duplicate function definitions removed
- [ ] Tests pass: uv run pytest tests/test_status_command.py tests/test_logs_command.py -v
- [ ] Add tests/test_workflow_utils.py

## Test Requirements
Create tests/test_workflow_utils.py:
```python
def test_find_most_recent_workflow_with_state_file(tmp_path):
def test_find_most_recent_workflow_with_events_file(tmp_path):
def test_find_most_recent_workflow_with_both_files(tmp_path):
def test_find_most_recent_workflow_no_workflows(tmp_path):
```

## Dependencies
None - can start immediately

## Agent Notes
🔴 CRITICAL - Code duplication
📬 Message when extraction complete
🧪 Create comprehensive test file
✅ Breaks features into: 1) Create utility 2) Update status.py 3) Update logs.py 4) Add tests

## Time Estimate
Agent: ~1.5 hours

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-yih
- **Status**: open
- **Created**: 2025-12-28 17:14:59
- **Updated**: 2025-12-28 17:14:59
