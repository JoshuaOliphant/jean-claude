#!/usr/bin/env python3
"""Verify beads-data-model feature is complete."""

import sys
from datetime import datetime

try:
    # Import the BeadsTask model
    from jean_claude.core.beads import BeadsTask, BeadsTaskStatus

    print("✓ BeadsTask model imported successfully")

    # Test 1: Create a BeadsTask with all fields
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="A test task description",
        acceptance_criteria=["AC 1", "AC 2"],
        status=BeadsTaskStatus.TODO
    )
    print("✓ BeadsTask created with all fields")

    # Test 2: Verify all required fields are present
    assert hasattr(task, 'id'), "Missing 'id' field"
    assert hasattr(task, 'title'), "Missing 'title' field"
    assert hasattr(task, 'description'), "Missing 'description' field"
    assert hasattr(task, 'status'), "Missing 'status' field"
    assert hasattr(task, 'acceptance_criteria'), "Missing 'acceptance_criteria' field"
    print("✓ All required fields present")

    # Test 3: Test to_dict() method
    task_dict = task.to_dict()
    assert isinstance(task_dict, dict), "to_dict() should return a dictionary"
    assert 'id' in task_dict, "to_dict() missing 'id' field"
    assert 'title' in task_dict, "to_dict() missing 'title' field"
    assert 'description' in task_dict, "to_dict() missing 'description' field"
    assert 'status' in task_dict, "to_dict() missing 'status' field"
    assert 'acceptance_criteria' in task_dict, "to_dict() missing 'acceptance_criteria' field"
    print("✓ to_dict() method works correctly")
    print(f"  Sample dict: {task_dict}")

    # Test 4: Test from_dict() method
    new_task = BeadsTask.from_dict({
        "id": "test-2",
        "title": "Another Test",
        "description": "Another test description",
        "acceptance_criteria": ["AC A", "AC B", "AC C"],
        "status": "in_progress"
    })
    assert new_task.id == "test-2", "from_dict() failed to set id"
    assert new_task.title == "Another Test", "from_dict() failed to set title"
    assert new_task.status == BeadsTaskStatus.IN_PROGRESS, "from_dict() failed to set status"
    assert len(new_task.acceptance_criteria) == 3, "from_dict() failed to set acceptance_criteria"
    print("✓ from_dict() method works correctly")

    # Test 5: Test serialization roundtrip
    original = BeadsTask(
        id="roundtrip-test",
        title="Roundtrip Test",
        description="Testing roundtrip serialization",
        acceptance_criteria=["Test 1", "Test 2"],
        status=BeadsTaskStatus.CLOSED
    )

    # Convert to dict and back
    as_dict = original.to_dict()
    restored = BeadsTask.from_dict(as_dict)

    assert restored.id == original.id, "Roundtrip failed for id"
    assert restored.title == original.title, "Roundtrip failed for title"
    assert restored.description == original.description, "Roundtrip failed for description"
    assert restored.status == original.status, "Roundtrip failed for status"
    assert restored.acceptance_criteria == original.acceptance_criteria, "Roundtrip failed for acceptance_criteria"
    print("✓ Serialization roundtrip works correctly")

    # Test 6: Verify BeadsTaskStatus enum values
    assert hasattr(BeadsTaskStatus, 'TODO'), "Missing TODO status"
    assert hasattr(BeadsTaskStatus, 'IN_PROGRESS'), "Missing IN_PROGRESS status"
    assert hasattr(BeadsTaskStatus, 'CLOSED'), "Missing CLOSED status"
    assert BeadsTaskStatus.TODO.value == 'todo', "TODO value mismatch"
    assert BeadsTaskStatus.IN_PROGRESS.value == 'in_progress', "IN_PROGRESS value mismatch"
    assert BeadsTaskStatus.CLOSED.value == 'closed', "CLOSED value mismatch"
    print("✓ BeadsTaskStatus enum is correct")

    print("\n" + "="*60)
    print("✅ ALL CHECKS PASSED - beads-data-model feature is complete!")
    print("="*60)
    sys.exit(0)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
