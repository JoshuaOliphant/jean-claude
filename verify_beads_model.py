#!/usr/bin/env python
"""Verify that the BeadsTask model implementation works correctly."""

import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, "/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/src")

try:
    from jean_claude.core.beads import BeadsTask

    print("✓ BeadsTask imported successfully")

    # Test 1: Create a basic task
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="A test task",
        status="not_started"
    )
    print(f"✓ Basic task creation works: {task.id}")

    # Test 2: Create task with all fields
    task2 = BeadsTask(
        id="test-2",
        title="Full Task",
        description="A complete test task",
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        status="in_progress",
        created_at=datetime(2025, 1, 1, 12, 0, 0),
        updated_at=datetime(2025, 1, 2, 14, 30, 0)
    )
    print(f"✓ Full task creation works: {task2.id} with {len(task2.acceptance_criteria)} criteria")

    # Test 3: Validate timestamps are auto-generated
    task3 = BeadsTask(
        id="test-3",
        title="Auto Timestamps",
        description="Testing auto timestamps",
        status="done"
    )
    assert task3.created_at is not None
    assert task3.updated_at is not None
    print(f"✓ Auto-generated timestamps work: created={task3.created_at}, updated={task3.updated_at}")

    # Test 4: Test from_json
    import json
    task_data = {
        "id": "json-test",
        "title": "JSON Task",
        "description": "Testing JSON parsing",
        "status": "done",
        "acceptance_criteria": ["AC 1", "AC 2"]
    }
    task4 = BeadsTask.from_json(json.dumps(task_data))
    print(f"✓ from_json works: {task4.id}")

    # Test 5: Test from_json with array (bd show --json format)
    array_data = [{
        "id": "array-test",
        "title": "Array Task",
        "description": "Testing array format",
        "status": "in_progress"
    }]
    task5 = BeadsTask.from_json(json.dumps(array_data))
    print(f"✓ from_json with array works: {task5.id}")

    # Test 6: Test validation
    try:
        bad_task = BeadsTask(
            id="",  # Empty id should fail
            title="Bad Task",
            description="Should fail",
            status="done"
        )
        print("✗ Validation should have failed for empty id")
        sys.exit(1)
    except Exception as e:
        print(f"✓ Validation works: empty id rejected")

    # Test 7: Test serialization
    task_dict = task2.model_dump()
    assert 'id' in task_dict
    assert 'title' in task_dict
    assert 'created_at' in task_dict
    assert 'updated_at' in task_dict
    print(f"✓ Serialization works: {len(task_dict)} fields")

    # Test 8: Test JSON serialization
    task_json = task2.model_dump_json()
    parsed = json.loads(task_json)
    assert 'id' in parsed
    assert 'created_at' in parsed
    print(f"✓ JSON serialization works")

    print("\n" + "="*60)
    print("✅ ALL VERIFICATION TESTS PASSED!")
    print("="*60)
    sys.exit(0)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
