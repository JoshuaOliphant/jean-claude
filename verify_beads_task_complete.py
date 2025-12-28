#!/usr/bin/env python
"""Verify BeadsTask data model is complete."""

import sys
sys.path.insert(0, 'src')

from datetime import datetime
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus

def verify_beads_task_model():
    """Verify the BeadsTask model has all required fields."""

    print("=" * 60)
    print("VERIFYING BEADSTASK DATA MODEL")
    print("=" * 60)

    # Test 1: Create BeadsTask with required fields
    print("\n1. Testing BeadsTask creation with required fields...")
    task = BeadsTask(
        id="jean_claude-2sz.3",
        title="Implement jc work Command",
        description="Create a new 'jc work' command that integrates with Beads",
        status=BeadsTaskStatus.TODO
    )

    assert hasattr(task, 'id'), "Missing 'id' field"
    assert hasattr(task, 'title'), "Missing 'title' field"
    assert hasattr(task, 'description'), "Missing 'description' field"
    assert hasattr(task, 'acceptance_criteria'), "Missing 'acceptance_criteria' field"
    assert hasattr(task, 'status'), "Missing 'status' field"
    assert hasattr(task, 'created_at'), "Missing 'created_at' field"
    assert hasattr(task, 'updated_at'), "Missing 'updated_at' field"

    print("✅ All required fields present")

    # Test 2: Verify field values
    print("\n2. Testing field values...")
    assert task.id == "jean_claude-2sz.3", f"Expected id='jean_claude-2sz.3', got {task.id}"
    assert task.title == "Implement jc work Command", f"Expected title='Implement jc work Command', got {task.title}"
    assert task.description == "Create a new 'jc work' command that integrates with Beads", f"Description mismatch"
    assert task.status == BeadsTaskStatus.TODO, f"Expected status=TODO, got {task.status}"
    assert task.acceptance_criteria == [], f"Expected empty acceptance_criteria, got {task.acceptance_criteria}"

    print("✅ Field values correct")

    # Test 3: Create BeadsTask with all fields including timestamps
    print("\n3. Testing BeadsTask with all fields including timestamps...")
    created = datetime(2025, 1, 1, 12, 0, 0)
    updated = datetime(2025, 1, 2, 14, 30, 0)

    task_full = BeadsTask(
        id="test-full",
        title="Full Task",
        description="Task with all fields",
        acceptance_criteria=["AC1", "AC2", "AC3"],
        status=BeadsTaskStatus.IN_PROGRESS,
        created_at=created,
        updated_at=updated
    )

    assert task_full.id == "test-full"
    assert task_full.title == "Full Task"
    assert task_full.description == "Task with all fields"
    assert len(task_full.acceptance_criteria) == 3
    assert task_full.status == BeadsTaskStatus.IN_PROGRESS
    assert task_full.created_at == created
    assert task_full.updated_at == updated

    print("✅ All fields including timestamps work correctly")

    # Test 4: Verify timestamp auto-generation
    print("\n4. Testing automatic timestamp generation...")
    task_auto = BeadsTask(
        id="test-auto",
        title="Auto Timestamps",
        description="Task with auto-generated timestamps",
        status=BeadsTaskStatus.CLOSED
    )

    assert isinstance(task_auto.created_at, datetime), "created_at should be datetime"
    assert isinstance(task_auto.updated_at, datetime), "updated_at should be datetime"

    print("✅ Automatic timestamp generation works")

    # Test 5: Test from_json method
    print("\n5. Testing from_json class method...")
    import json

    task_data = {
        "id": "json-test",
        "title": "JSON Test",
        "description": "Testing from_json",
        "status": "todo",
        "acceptance_criteria": ["Criterion 1", "Criterion 2"]
    }

    json_str = json.dumps(task_data)
    task_from_json = BeadsTask.from_json(json_str)

    assert task_from_json.id == "json-test"
    assert task_from_json.title == "JSON Test"
    assert task_from_json.description == "Testing from_json"
    assert task_from_json.status == BeadsTaskStatus.TODO
    assert len(task_from_json.acceptance_criteria) == 2

    print("✅ from_json method works correctly")

    # Test 6: Test BeadsTaskStatus enum
    print("\n6. Testing BeadsTaskStatus enum...")
    assert BeadsTaskStatus.TODO == 'todo'
    assert BeadsTaskStatus.IN_PROGRESS == 'in_progress'
    assert BeadsTaskStatus.CLOSED == 'closed'

    print("✅ BeadsTaskStatus enum has correct values")

    print("\n" + "=" * 60)
    print("✅ ALL VERIFICATION CHECKS PASSED!")
    print("=" * 60)
    print("\nBeadsTask data model is complete with:")
    print("  - id field")
    print("  - title field")
    print("  - description field")
    print("  - acceptance_criteria field (list)")
    print("  - status field (BeadsTaskStatus enum)")
    print("  - created_at field (datetime)")
    print("  - updated_at field (datetime)")
    print("  - from_json() class method")
    print("  - Automatic timestamp generation")

    return 0

if __name__ == "__main__":
    try:
        sys.exit(verify_beads_task_model())
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
