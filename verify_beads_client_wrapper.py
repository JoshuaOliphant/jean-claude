#!/usr/bin/env python
"""Verify BeadsClient wrapper implementation."""

import json
from jean_claude.core.beads import BeadsClient, BeadsTask, BeadsTaskStatus

def main():
    print("="*60)
    print("BEADS CLIENT WRAPPER VERIFICATION")
    print("="*60)

    client = BeadsClient()

    # Test 1: Verify client instantiation
    print("\n✓ Test 1: BeadsClient instantiation")
    assert isinstance(client, BeadsClient)
    print("  - Client instantiated successfully")

    # Test 2: Verify all required methods exist
    print("\n✓ Test 2: Required methods exist")
    assert hasattr(client, 'fetch_task')
    assert hasattr(client, 'update_status')
    assert hasattr(client, 'parse_task_json')
    assert callable(client.fetch_task)
    assert callable(client.update_status)
    assert callable(client.parse_task_json)
    print("  - fetch_task() ✓")
    print("  - update_status() ✓")
    print("  - parse_task_json() ✓")

    # Test 3: Test parse_task_json with valid JSON
    print("\n✓ Test 3: parse_task_json() with valid JSON")
    test_json = json.dumps({
        "id": "test-123",
        "title": "Test Task",
        "description": "This is a test task",
        "acceptance_criteria": ["AC 1", "AC 2"],
        "status": "open"
    })

    task = client.parse_task_json(test_json)
    assert isinstance(task, BeadsTask)
    assert task.id == "test-123"
    assert task.title == "Test Task"
    assert task.description == "This is a test task"
    assert len(task.acceptance_criteria) == 2
    assert task.status == BeadsTaskStatus.TODO
    print(f"  - Parsed task: {task.id}")
    print(f"  - Title: {task.title}")
    print(f"  - Status: {task.status.value}")

    # Test 4: Test parse_task_json with JSON array
    print("\n✓ Test 4: parse_task_json() with JSON array")
    test_json_array = json.dumps([{
        "id": "test-456",
        "title": "Array Test",
        "description": "Test with array",
        "status": "in_progress"
    }])

    task2 = client.parse_task_json(test_json_array)
    assert isinstance(task2, BeadsTask)
    assert task2.id == "test-456"
    assert task2.status == BeadsTaskStatus.IN_PROGRESS
    print(f"  - Parsed task from array: {task2.id}")
    print(f"  - Status: {task2.status.value}")

    # Test 5: Test error handling
    print("\n✓ Test 5: Error handling")
    try:
        client.parse_task_json("")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "json_str cannot be empty" in str(e)
        print("  - Empty string validation ✓")

    try:
        client.parse_task_json("[]")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "JSON array is empty" in str(e)
        print("  - Empty array validation ✓")

    try:
        client.parse_task_json("not valid json")
        assert False, "Should have raised JSONDecodeError"
    except json.JSONDecodeError:
        print("  - Invalid JSON validation ✓")

    print("\n" + "="*60)
    print("✅ ALL VERIFICATION CHECKS PASSED!")
    print("="*60)
    print("\nBeadsClient wrapper implementation is complete:")
    print("  1. fetch_task(task_id) - calls 'bd show --json'")
    print("  2. update_status(task_id, status) - updates task status")
    print("  3. parse_task_json(json_str) - converts JSON to BeadsTask model")
    print("="*60)

if __name__ == "__main__":
    main()
