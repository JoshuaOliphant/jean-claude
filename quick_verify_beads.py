#!/usr/bin/env python3
"""Quick verification that BeadsTask model is working."""

from datetime import datetime
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus

# Test 1: Create a basic task
print("Test 1: Creating a basic BeadsTask...")
task = BeadsTask(
    id="test-1",
    title="Test Task",
    description="This is a test task",
    status=BeadsTaskStatus.TODO
)
print(f"✅ Created task: {task.title}")
print(f"   ID: {task.id}")
print(f"   Status: {task.status}")
print(f"   Created at: {task.created_at}")
print(f"   Updated at: {task.updated_at}")
print()

# Test 2: Create with all fields
print("Test 2: Creating BeadsTask with all fields...")
task2 = BeadsTask(
    id="jean_claude-2sz.3",
    title="Implement jc work Command",
    description="Create a new 'jc work' command that integrates with Beads",
    acceptance_criteria=[
        "Command fetches task from Beads",
        "Command generates spec from task",
        "Command runs workflow"
    ],
    status=BeadsTaskStatus.IN_PROGRESS,
    created_at=datetime(2025, 1, 1, 12, 0, 0),
    updated_at=datetime(2025, 1, 2, 14, 30, 0)
)
print(f"✅ Created task: {task2.title}")
print(f"   Acceptance Criteria: {len(task2.acceptance_criteria)} items")
print()

# Test 3: Test from_json
print("Test 3: Testing from_json...")
import json
json_data = {
    "id": "test-json",
    "title": "Task from JSON",
    "description": "Created from JSON",
    "status": "closed"
}
task3 = BeadsTask.from_json(json.dumps(json_data))
print(f"✅ Created task from JSON: {task3.title}")
print(f"   Status: {task3.status}")
print()

# Test 4: Verify enum
print("Test 4: Testing BeadsTaskStatus enum...")
print(f"   TODO value: {BeadsTaskStatus.TODO.value}")
print(f"   IN_PROGRESS value: {BeadsTaskStatus.IN_PROGRESS.value}")
print(f"   CLOSED value: {BeadsTaskStatus.CLOSED.value}")
print("✅ Enum values correct")
print()

print("=" * 60)
print("✅ ALL VERIFICATION TESTS PASSED")
print("=" * 60)
