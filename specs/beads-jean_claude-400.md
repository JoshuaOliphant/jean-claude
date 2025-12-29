# Remove barrel exports from core/__init__.py

## Description

## Problem
core/__init__.py exports 18 items from 11 modules, creating a bottleneck. Importing ONE item loads ALL 11 modules, slowing startup and creating unclear dependencies.

## Files to Modify
1. src/jean_claude/core/__init__.py (remove all exports)
2. Update ALL files that import from jean_claude.core

## Current Pattern (SLOW)
```python
from jean_claude.core import BeadsTask  # Loads 11 modules!
```

## Target Pattern (FAST)
```python
from jean_claude.core.beads import BeadsTask  # Loads only beads.py
```

## Implementation Steps

### Step 1: Find all imports
```bash
grep -r 'from jean_claude\.core import' src/ tests/
```

### Step 2: Update each import
For each file found, change:
```python
# BEFORE:
from jean_claude.core import BeadsTask, WorkflowState, Message

# AFTER:
from jean_claude.core.beads import BeadsTask
from jean_claude.core.state import WorkflowState
from jean_claude.core.message import Message
```

### Step 3: Clean core/__init__.py
Remove all __all__ exports, keep only:
```python
# ABOUTME: Core module package marker
# ABOUTME: Use explicit imports instead of barrel exports

"""Core business logic for Jean Claude.

Import directly from submodules:
    from jean_claude.core.beads import BeadsTask
    from jean_claude.core.state import WorkflowState
"""
```

## Mapping Guide
```python
# Current exports → New imports
BeadsTask → from jean_claude.core.beads import BeadsTask
WorkflowState → from jean_claude.core.state import WorkflowState
Message → from jean_claude.core.message import Message
Mailbox → from jean_claude.core.mailbox_api import Mailbox
ExecutionResult → from jean_claude.core.agent import ExecutionResult
PromptRequest → from jean_claude.core.agent import PromptRequest
# ... etc for all 18 exports
```

## Acceptance Criteria
- [ ] core/__init__.py cleaned (remove exports)
- [ ] All imports updated to explicit module imports
- [ ] No 'from jean_claude.core import' statements remain (except in __init__.py itself)
- [ ] Tests pass: uv run pytest -v
- [ ] Startup time improved (measure with time python -c "import jean_claude")
- [ ] No ruff import errors

## Verification
```bash
# Should return nothing:
grep -r 'from jean_claude\.core import [A-Z]' src/ tests/ --exclude='__init__.py'
```

## Dependencies
None - can work in parallel

## Agent Notes
🟠 HIGH PRIORITY - Performance impact
📬 Message with count of files updated
✅ Break into features: 1) Map all imports 2) Update src/ 3) Update tests/ 4) Clean __init__
🎯 Large refactor - expect ~50+ files to update
⚡ Automated with grep + sed possible

## Time Estimate
Agent: ~3-4 hours (many files to update)

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-400
- **Status**: in_progress
- **Created**: 2025-12-28 17:16:44
- **Updated**: 2025-12-28 17:31:18
