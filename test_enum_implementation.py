#!/usr/bin/env python3
"""Quick test to verify BeadsTaskStatus enum implementation."""

import sys
from enum import Enum

try:
    from jean_claude.core.beads import BeadsTask, BeadsTaskStatus

    # Test 1: Verify BeadsTaskStatus is an Enum
    print("Test 1: Checking if BeadsTaskStatus is an Enum...")
    assert issubclass(BeadsTaskStatus, Enum), "BeadsTaskStatus is not an Enum"
    print("✓ BeadsTaskStatus is an Enum")

    # Test 2: Verify enum has correct values
    print("\nTest 2: Checking enum values...")
    assert hasattr(BeadsTaskStatus, 'TODO'), "Missing TODO"
    assert hasattr(BeadsTaskStatus, 'IN_PROGRESS'), "Missing IN_PROGRESS"
    assert hasattr(BeadsTaskStatus, 'CLOSED'), "Missing CLOSED"
    assert BeadsTaskStatus.TODO.value == 'todo', f"TODO value wrong: {BeadsTaskStatus.TODO.value}"
    assert BeadsTaskStatus.IN_PROGRESS.value == 'in_progress', f"IN_PROGRESS value wrong: {BeadsTaskStatus.IN_PROGRESS.value}"
    assert BeadsTaskStatus.CLOSED.value == 'closed', f"CLOSED value wrong: {BeadsTaskStatus.CLOSED.value}"
    print("✓ All enum values are correct")

    # Test 3: Verify only 3 values exist
    print("\nTest 3: Checking enum has exactly 3 values...")
    statuses = list(BeadsTaskStatus)
    assert len(statuses) == 3, f"Expected 3 statuses, got {len(statuses)}"
    print("✓ Enum has exactly 3 values")

    # Test 4: Create a BeadsTask with enum status
    print("\nTest 4: Creating BeadsTask with enum status...")
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="A test task",
        status=BeadsTaskStatus.TODO
    )
    assert task.status == BeadsTaskStatus.TODO, f"Status mismatch: {task.status}"
    print("✓ BeadsTask created successfully with enum status")

    # Test 5: Verify status is of correct type
    print("\nTest 5: Checking status field type...")
    assert isinstance(task.status, BeadsTaskStatus), f"Status is not BeadsTaskStatus: {type(task.status)}"
    print("✓ Status field is of type BeadsTaskStatus")

    # Test 6: Create task with different statuses
    print("\nTest 6: Creating tasks with all status values...")
    task_todo = BeadsTask(
        id="task-1",
        title="TODO Task",
        description="A TODO task",
        status=BeadsTaskStatus.TODO
    )
    task_in_progress = BeadsTask(
        id="task-2",
        title="In Progress Task",
        description="An in-progress task",
        status=BeadsTaskStatus.IN_PROGRESS
    )
    task_closed = BeadsTask(
        id="task-3",
        title="Closed Task",
        description="A closed task",
        status=BeadsTaskStatus.CLOSED
    )
    assert task_todo.status == BeadsTaskStatus.TODO
    assert task_in_progress.status == BeadsTaskStatus.IN_PROGRESS
    assert task_closed.status == BeadsTaskStatus.CLOSED
    print("✓ All status values work correctly")

    print("\n" + "="*50)
    print("✅ All tests passed successfully!")
    print("="*50)
    sys.exit(0)

except Exception as e:
    print(f"\n❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
