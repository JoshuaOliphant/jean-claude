#!/usr/bin/env python3
"""Verify BeadsTask model works correctly."""

import sys
sys.path.insert(0, '/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/src')

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus

# Test 1: Check that TODO status exists
print("Test 1: Checking BeadsTaskStatus.TODO exists...")
assert hasattr(BeadsTaskStatus, 'TODO'), "BeadsTaskStatus.TODO does not exist"
assert BeadsTaskStatus.TODO.value == 'todo', f"Expected 'todo', got '{BeadsTaskStatus.TODO.value}'"
print("✓ BeadsTaskStatus.TODO exists with value 'todo'")

# Test 2: Create a BeadsTask with TODO status
print("\nTest 2: Creating BeadsTask with TODO status...")
task = BeadsTask(
    id="test-1",
    title="Test Task",
    description="A test task",
    acceptance_criteria=["AC 1", "AC 2"],
    status=BeadsTaskStatus.TODO
)
print(f"✓ Created task: {task.id} - {task.title}")

# Test 3: Test to_dict method
print("\nTest 3: Testing to_dict() method...")
task_dict = task.to_dict()
assert isinstance(task_dict, dict), "to_dict() should return a dict"
assert 'id' in task_dict, "to_dict() missing 'id' field"
assert 'title' in task_dict, "to_dict() missing 'title' field"
assert 'description' in task_dict, "to_dict() missing 'description' field"
assert 'status' in task_dict, "to_dict() missing 'status' field"
print(f"✓ to_dict() works correctly: {list(task_dict.keys())}")

# Test 4: Test from_dict method
print("\nTest 4: Testing from_dict() method...")
data = {
    "id": "test-2",
    "title": "Test Task 2",
    "description": "Another test task",
    "acceptance_criteria": ["Criterion 1"],
    "status": BeadsTaskStatus.TODO
}
task2 = BeadsTask.from_dict(data)
assert task2.id == "test-2", "from_dict() failed to set id"
assert task2.status == BeadsTaskStatus.TODO, "from_dict() failed to set status"
print(f"✓ from_dict() works correctly: {task2.id} - {task2.title}")

# Test 5: Roundtrip conversion
print("\nTest 5: Testing roundtrip conversion...")
original_task = BeadsTask(
    id="roundtrip-1",
    title="Roundtrip Test",
    description="Testing roundtrip conversion",
    acceptance_criteria=["AC 1", "AC 2", "AC 3"],
    status=BeadsTaskStatus.IN_PROGRESS
)
task_dict = original_task.to_dict()
restored_task = BeadsTask.from_dict(task_dict)

assert restored_task.id == original_task.id, "Roundtrip failed: id mismatch"
assert restored_task.title == original_task.title, "Roundtrip failed: title mismatch"
assert restored_task.status == original_task.status, "Roundtrip failed: status mismatch"
print("✓ Roundtrip conversion works correctly")

print("\n" + "="*60)
print("All verification tests passed! ✓")
print("="*60)
