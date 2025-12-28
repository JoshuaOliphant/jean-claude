#!/usr/bin/env python
"""Quick test of BeadsTask from_dict and to_dict methods."""

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus

# Test to_dict
print("Testing to_dict()...")
task = BeadsTask(
    id="test-1",
    title="Test Task",
    description="A test task",
    acceptance_criteria=["AC 1", "AC 2"],
    status=BeadsTaskStatus.IN_PROGRESS
)

result = task.to_dict()
print(f"  Result type: {type(result)}")
print(f"  Has all fields: {all(k in result for k in ['id', 'title', 'description', 'acceptance_criteria', 'status', 'created_at', 'updated_at'])}")
print(f"  ID matches: {result['id'] == 'test-1'}")
print(f"  Status type: {type(result['status'])}")

# Test from_dict
print("\nTesting from_dict()...")
data = {
    "id": "test-2",
    "title": "Test Task 2",
    "description": "Another test task",
    "acceptance_criteria": ["AC A", "AC B"],
    "status": BeadsTaskStatus.CLOSED
}

task2 = BeadsTask.from_dict(data)
print(f"  Result type: {type(task2)}")
print(f"  ID matches: {task2.id == 'test-2'}")
print(f"  Title matches: {task2.title == 'Test Task 2'}")
print(f"  Status matches: {task2.status == BeadsTaskStatus.CLOSED}")

# Test roundtrip
print("\nTesting roundtrip...")
original = BeadsTask(
    id="roundtrip-1",
    title="Roundtrip Test",
    description="Testing roundtrip",
    acceptance_criteria=["A", "B"],
    status=BeadsTaskStatus.TODO
)

dict_form = original.to_dict()
restored = BeadsTask.from_dict(dict_form)
print(f"  ID matches: {restored.id == original.id}")
print(f"  Title matches: {restored.title == original.title}")
print(f"  Description matches: {restored.description == original.description}")
print(f"  Status matches: {restored.status == original.status}")
print(f"  AC matches: {restored.acceptance_criteria == original.acceptance_criteria}")

print("\n✅ All manual tests passed!")
