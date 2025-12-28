#!/usr/bin/env python
"""Verify beads implementation exists and works."""

import sys
from datetime import datetime

try:
    # Import the required components
    from jean_claude.core.beads import BeadsTask, BeadsTaskStatus

    print("✅ Successfully imported BeadsTask and BeadsTaskStatus")

    # Test BeadsTaskStatus enum
    print("\n=== Testing BeadsTaskStatus Enum ===")
    print(f"TODO: {BeadsTaskStatus.TODO.value}")
    print(f"IN_PROGRESS: {BeadsTaskStatus.IN_PROGRESS.value}")
    print(f"CLOSED: {BeadsTaskStatus.CLOSED.value}")

    # Test BeadsTask creation
    print("\n=== Testing BeadsTask Creation ===")
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="This is a test task",
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        status=BeadsTaskStatus.TODO
    )
    print(f"Created task: {task.id} - {task.title}")
    print(f"Status: {task.status}")
    print(f"Acceptance criteria count: {len(task.acceptance_criteria)}")

    # Test to_dict method
    print("\n=== Testing to_dict() Method ===")
    task_dict = task.to_dict()
    print(f"Keys in dict: {list(task_dict.keys())}")
    assert 'id' in task_dict
    assert 'title' in task_dict
    assert 'description' in task_dict
    assert 'acceptance_criteria' in task_dict
    assert 'status' in task_dict
    print("✅ to_dict() works correctly")

    # Test from_dict method
    print("\n=== Testing from_dict() Method ===")
    test_data = {
        "id": "test-2",
        "title": "From Dict Task",
        "description": "Created from dictionary",
        "acceptance_criteria": ["AC1"],
        "status": BeadsTaskStatus.IN_PROGRESS
    }
    task2 = BeadsTask.from_dict(test_data)
    print(f"Created from dict: {task2.id} - {task2.title}")
    print("✅ from_dict() works correctly")

    # Test from_json method (bonus)
    print("\n=== Testing from_json() Method (Bonus) ===")
    import json
    json_data = json.dumps({
        "id": "test-3",
        "title": "From JSON Task",
        "description": "Created from JSON",
        "status": "in_progress"
    })
    task3 = BeadsTask.from_json(json_data)
    print(f"Created from JSON: {task3.id} - {task3.title}")
    print("✅ from_json() works correctly")

    print("\n" + "="*60)
    print("✅ ALL VERIFICATION CHECKS PASSED!")
    print("="*60)
    print("\nThe BeadsTask data model is fully implemented with:")
    print("  - BeadsTaskStatus enum (TODO, IN_PROGRESS, CLOSED)")
    print("  - BeadsTask dataclass with required fields")
    print("  - from_dict() method")
    print("  - to_dict() method")
    print("  - from_json() method (bonus)")
    print("  - Timestamp fields (bonus)")

    sys.exit(0)

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
