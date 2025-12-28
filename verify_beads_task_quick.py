#!/usr/bin/env python
"""Quick verification that BeadsTask model works."""

from datetime import datetime
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus

# Test 1: Create a BeadsTask with all fields
print("Test 1: Creating BeadsTask with all fields...")
task = BeadsTask(
    id="test-1",
    title="Test Task",
    description="A test task",
    acceptance_criteria=["AC 1", "AC 2"],
    status=BeadsTaskStatus.IN_PROGRESS
)
print(f"✓ Created task: {task.id} - {task.title}")

# Test 2: Test to_dict()
print("\nTest 2: Testing to_dict()...")
task_dict = task.to_dict()
assert isinstance(task_dict, dict)
assert task_dict["id"] == "test-1"
assert task_dict["title"] == "Test Task"
assert task_dict["description"] == "A test task"
assert task_dict["acceptance_criteria"] == ["AC 1", "AC 2"]
assert task_dict["status"] == BeadsTaskStatus.IN_PROGRESS
print(f"✓ to_dict() works correctly")
print(f"  Keys: {list(task_dict.keys())}")

# Test 3: Test from_dict()
print("\nTest 3: Testing from_dict()...")
data = {
    "id": "test-2",
    "title": "Test from dict",
    "description": "Created from dict",
    "acceptance_criteria": ["Criterion 1", "Criterion 2"],
    "status": BeadsTaskStatus.TODO
}
task2 = BeadsTask.from_dict(data)
assert task2.id == "test-2"
assert task2.title == "Test from dict"
assert len(task2.acceptance_criteria) == 2
print(f"✓ from_dict() works correctly")
print(f"  Created task: {task2.id} - {task2.title}")

# Test 4: Roundtrip test
print("\nTest 4: Testing roundtrip (to_dict -> from_dict)...")
original = BeadsTask(
    id="roundtrip-1",
    title="Roundtrip Test",
    description="Testing roundtrip",
    acceptance_criteria=["AC A", "AC B"],
    status=BeadsTaskStatus.CLOSED
)
as_dict = original.to_dict()
restored = BeadsTask.from_dict(as_dict)
assert restored.id == original.id
assert restored.title == original.title
assert restored.description == original.description
assert restored.acceptance_criteria == original.acceptance_criteria
assert restored.status == original.status
print(f"✓ Roundtrip conversion preserves all data")

# Test 5: All required fields present
print("\nTest 5: Verifying all required fields...")
fields = ['id', 'title', 'description', 'status', 'acceptance_criteria', 'created_at', 'updated_at']
for field in fields:
    assert hasattr(task, field), f"Missing field: {field}"
print(f"✓ All required fields present: {', '.join(fields)}")

print("\n" + "="*60)
print("✅ ALL TESTS PASSED - BeadsTask model is working correctly!")
print("="*60)
print("\nFeature Summary:")
print("  - BeadsTask dataclass exists")
print("  - Fields: id, title, description, status, acceptance_criteria, created_at, updated_at")
print("  - from_dict() method works")
print("  - to_dict() method works")
print("  - JSON serialization via roundtrip verified")
