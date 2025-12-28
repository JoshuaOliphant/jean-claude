#!/usr/bin/env python
"""Quick verification script for beads module."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.core.beads import (
    BeadsTask,
    fetch_beads_task,
    update_beads_status,
    close_beads_task,
    generate_spec_from_beads
)


def test_imports():
    """Test that all required functions and classes can be imported."""
    print("✓ All imports successful")
    return True


def test_beads_task_model():
    """Test that BeadsTask model can be instantiated."""
    task = BeadsTask(
        id="test-123",
        title="Test Task",
        description="A test task",
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        status="in_progress"
    )

    assert task.id == "test-123"
    assert task.title == "Test Task"
    assert task.description == "A test task"
    assert len(task.acceptance_criteria) == 2
    assert task.status == "in_progress"
    assert task.created_at is not None
    assert task.updated_at is not None

    print("✓ BeadsTask model instantiation works")
    return True


def test_function_signatures():
    """Test that all required functions exist with correct signatures."""
    import inspect

    # Test fetch_beads_task signature
    sig = inspect.signature(fetch_beads_task)
    assert 'task_id' in sig.parameters
    print("✓ fetch_beads_task signature correct")

    # Test update_beads_status signature
    sig = inspect.signature(update_beads_status)
    assert 'task_id' in sig.parameters
    assert 'status' in sig.parameters
    print("✓ update_beads_status signature correct")

    # Test close_beads_task signature
    sig = inspect.signature(close_beads_task)
    assert 'task_id' in sig.parameters
    print("✓ close_beads_task signature correct")

    return True


def test_generate_spec():
    """Test spec generation from BeadsTask."""
    task = BeadsTask(
        id="test-123",
        title="Test Task",
        description="A test task for spec generation",
        acceptance_criteria=["Must work", "Must be tested"],
        status="in_progress"
    )

    spec = generate_spec_from_beads(task)

    assert "# Test Task" in spec
    assert "## Description" in spec
    assert "A test task for spec generation" in spec
    assert "## Acceptance Criteria" in spec
    assert "- Must work" in spec
    assert "- Must be tested" in spec

    print("✓ generate_spec_from_beads works correctly")
    return True


if __name__ == "__main__":
    try:
        test_imports()
        test_beads_task_model()
        test_function_signatures()
        test_generate_spec()
        print("\n✅ All beads module verification tests PASSED!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
