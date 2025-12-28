#!/usr/bin/env python3
"""Quick verification script for beads_task_id field."""

import sys
from jean_claude.core.state import WorkflowState

def test_default_value():
    """Test beads_task_id defaults to None."""
    state = WorkflowState(
        workflow_id="test-123",
        workflow_name="Test Workflow",
        workflow_type="feature",
    )
    assert state.beads_task_id is None, "Default value should be None"
    print("✓ Test 1 passed: beads_task_id defaults to None")

def test_explicit_value():
    """Test beads_task_id can be set explicitly."""
    state = WorkflowState(
        workflow_id="test-123",
        workflow_name="Test Workflow",
        workflow_type="feature",
        beads_task_id="jean_claude-2sz.2",
    )
    assert state.beads_task_id == "jean_claude-2sz.2", "Explicit value should be set"
    print("✓ Test 2 passed: beads_task_id can be set explicitly")

def test_serialization():
    """Test beads_task_id serializes correctly."""
    state = WorkflowState(
        workflow_id="test-123",
        workflow_name="Test Workflow",
        workflow_type="feature",
        beads_task_id="jean_claude-abc.123",
    )

    # Convert to dict
    data = state.model_dump()
    assert "beads_task_id" in data, "beads_task_id should be in dict"
    assert data["beads_task_id"] == "jean_claude-abc.123", "Value should match"
    print("✓ Test 3 passed: beads_task_id serializes correctly")

def test_backward_compatibility():
    """Test that beads_task_id field has a default and doesn't break old code."""
    # This simulates loading old state that doesn't have beads_task_id
    data = {
        "workflow_id": "old-123",
        "workflow_name": "Old Workflow",
        "workflow_type": "chore",
        "phases": {},
        "inputs": {},
        "outputs": {},
        "created_at": "2024-12-21T10:00:00",
        "updated_at": "2024-12-21T10:00:00",
        "process_id": None,
        # Note: beads_task_id is NOT in this old data
    }

    state = WorkflowState.model_validate(data)
    assert state.beads_task_id is None, "Should default to None for backward compatibility"
    print("✓ Test 4 passed: backward compatibility works")

if __name__ == "__main__":
    try:
        test_default_value()
        test_explicit_value()
        test_serialization()
        test_backward_compatibility()
        print("\n✅ All verification tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
