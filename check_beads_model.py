#!/usr/bin/env python3
"""Quick check that BeadsTask model works as expected."""

from datetime import datetime
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus
import json

def test_basic_creation():
    """Test creating a BeadsTask."""
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="A test task",
        acceptance_criteria=["AC 1", "AC 2"],
        status=BeadsTaskStatus.TODO
    )

    print(f"✓ Created task: {task.id}")
    print(f"  Title: {task.title}")
    print(f"  Status: {task.status}")
    print(f"  Acceptance Criteria: {len(task.acceptance_criteria)} items")
    print(f"  Created at: {task.created_at}")
    print(f"  Updated at: {task.updated_at}")
    return True

def test_from_json():
    """Test from_json class method."""
    task_data = {
        "id": "jean_claude-2sz.3",
        "title": "Implement jc work Command",
        "description": "Create a new 'jc work' command",
        "acceptance_criteria": [
            "Command fetches task from Beads",
            "Command generates spec from task"
        ],
        "status": "todo"
    }

    json_str = json.dumps(task_data)
    task = BeadsTask.from_json(json_str)

    print(f"\n✓ Parsed from JSON: {task.id}")
    print(f"  Title: {task.title}")
    print(f"  Status: {task.status}")
    return True

def test_from_json_array():
    """Test from_json with array (bd show --json format)."""
    task_data = [{
        "id": "test-2",
        "title": "Array Test",
        "description": "Testing array format",
        "status": "in_progress"
    }]

    json_str = json.dumps(task_data)
    task = BeadsTask.from_json(json_str)

    print(f"\n✓ Parsed from JSON array: {task.id}")
    print(f"  Status: {task.status}")
    return True

def test_from_dict():
    """Test from_dict method."""
    task_dict = {
        "id": "test-3",
        "title": "Dict Test",
        "description": "Testing dict conversion",
        "status": BeadsTaskStatus.CLOSED
    }

    task = BeadsTask.from_dict(task_dict)
    print(f"\n✓ Created from dict: {task.id}")
    print(f"  Status: {task.status}")
    return True

def test_to_dict():
    """Test to_dict method."""
    task = BeadsTask(
        id="test-4",
        title="To Dict Test",
        description="Testing to_dict",
        status=BeadsTaskStatus.IN_PROGRESS
    )

    task_dict = task.to_dict()
    print(f"\n✓ Converted to dict: {task_dict['id']}")
    print(f"  Keys: {list(task_dict.keys())}")
    return True

def main():
    """Run all checks."""
    print("Checking BeadsTask data model implementation...\n")

    try:
        test_basic_creation()
        test_from_json()
        test_from_json_array()
        test_from_dict()
        test_to_dict()

        print("\n" + "="*60)
        print("✓ All checks passed!")
        print("="*60)
        return 0
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
