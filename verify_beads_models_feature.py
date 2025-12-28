#!/usr/bin/env python3
"""Verify that the beads-data-models feature is complete."""

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus
from datetime import datetime

def verify_beads_task():
    """Verify BeadsTask dataclass exists with required fields."""
    # Test 1: Create task with all required fields
    task = BeadsTask(
        id='test-1',
        title='Test Task',
        description='A test description',
        status=BeadsTaskStatus.TODO
    )

    # Verify required fields exist
    assert hasattr(task, 'id'), "BeadsTask missing 'id' field"
    assert hasattr(task, 'title'), "BeadsTask missing 'title' field"
    assert hasattr(task, 'description'), "BeadsTask missing 'description' field"
    assert hasattr(task, 'status'), "BeadsTask missing 'status' field"
    assert hasattr(task, 'acceptance_criteria'), "BeadsTask missing 'acceptance_criteria' field"
    assert hasattr(task, 'created_at'), "BeadsTask missing 'created_at' field"
    assert hasattr(task, 'updated_at'), "BeadsTask missing 'updated_at' field"

    # Verify field values
    assert task.id == 'test-1', "id field not set correctly"
    assert task.title == 'Test Task', "title field not set correctly"
    assert task.status == BeadsTaskStatus.TODO, "status field not set correctly"
    assert isinstance(task.created_at, datetime), "created_at should be datetime"
    assert isinstance(task.updated_at, datetime), "updated_at should be datetime"

    print("✓ BeadsTask dataclass verified")

def verify_beads_task_status():
    """Verify BeadsTaskStatus enum exists with required states."""
    # Verify enum exists
    assert hasattr(BeadsTaskStatus, 'TODO'), "BeadsTaskStatus missing 'TODO' state"
    assert hasattr(BeadsTaskStatus, 'IN_PROGRESS'), "BeadsTaskStatus missing 'IN_PROGRESS' state"
    assert hasattr(BeadsTaskStatus, 'CLOSED'), "BeadsTaskStatus missing 'CLOSED' state"

    # Verify enum values
    assert BeadsTaskStatus.TODO.value == 'todo', "TODO enum value incorrect"
    assert BeadsTaskStatus.IN_PROGRESS.value == 'in_progress', "IN_PROGRESS enum value incorrect"
    assert BeadsTaskStatus.CLOSED.value == 'closed', "CLOSED enum value incorrect"

    print("✓ BeadsTaskStatus enum verified")

def verify_tests_exist():
    """Verify test file exists."""
    import os
    test_path = os.path.join(
        os.path.dirname(__file__),
        'tests', 'core', 'test_beads_models.py'
    )
    assert os.path.exists(test_path), f"Test file not found at {test_path}"
    print(f"✓ Test file exists at {test_path}")

if __name__ == '__main__':
    print("Verifying beads-data-models feature...\n")

    try:
        verify_beads_task()
        verify_beads_task_status()
        verify_tests_exist()

        print("\n✅ All verifications passed!")
        print("✅ Feature 'beads-data-models' is complete!")

    except AssertionError as e:
        print(f"\n❌ Verification failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)
