# Link WorkflowState to Beads Tasks

**Beads Task**: jean_claude-2sz.2
**Priority**: P0
**Type**: task

## Overview

Extend WorkflowState to track which Beads task is being implemented. This creates the connection between human-defined work (Beads) and agent implementation (features).

## Changes to WorkflowState

Add the following fields to WorkflowState in `src/jean_claude/core/state.py`:

1. `beads_task_id: Optional[str] = None` - The Beads task ID being implemented
2. `beads_task_title: Optional[str] = None` - Human-readable title of the Beads task
3. `phase: Literal['planning', 'implementing', 'verifying', 'complete'] = 'planning'` - Current workflow phase

## Implementation Requirements

### Field Additions
- All new fields must have defaults for backward compatibility
- Existing workflows without Beads task IDs should continue to work
- Phase should track the current state of the workflow

### Phase Semantics
- `planning`: Initial state, planning features
- `implementing`: Actively implementing features
- `verifying`: Running verification tests
- `complete`: All features done and verified

### Serialization
- Update `save()` and `load()` methods to handle new fields
- Ensure JSON serialization works correctly with Literal types

### Test Requirements
- Test WorkflowState with all new fields
- Test backward compatibility (load old state without new fields)
- Test phase transitions
- Test save/load roundtrip with Beads fields
- Test that beads_task_id=None works correctly

## Files to Modify

1. `src/jean_claude/core/state.py` - Add new fields to WorkflowState
2. `tests/test_state.py` - Add tests for new fields (create if doesn't exist)

## Acceptance Criteria

- [ ] beads_task_id and beads_task_title fields added to WorkflowState
- [ ] phase field with planning/implementing/verifying/complete states
- [ ] Backward compatible - existing workflows without Beads still work
- [ ] Tests for new fields and phase transitions
