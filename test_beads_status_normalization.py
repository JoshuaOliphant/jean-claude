#!/usr/bin/env python3
"""Test BeadsTask status normalization."""

import sys
sys.path.insert(0, '/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/src')

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus

print("Testing BeadsTask status normalization...")
print("="*60)

# Test 1: Create with TODO enum
print("\n1. Creating task with BeadsTaskStatus.TODO enum...")
task1 = BeadsTask(
    id="test-1",
    title="Test Task",
    description="A test task",
    status=BeadsTaskStatus.TODO
)
assert task1.status == BeadsTaskStatus.TODO
print(f"✓ Status: {task1.status} (value: {task1.status.value})")

# Test 2: Create with "open" string (should normalize to TODO)
print("\n2. Creating task with 'open' string status...")
task2 = BeadsTask(
    id="test-2",
    title="Test Task 2",
    description="Another test task",
    status="open"
)
assert task2.status == BeadsTaskStatus.TODO
print(f"✓ Status normalized from 'open' to: {task2.status} (value: {task2.status.value})")

# Test 3: Create with "done" string (should normalize to CLOSED)
print("\n3. Creating task with 'done' string status...")
task3 = BeadsTask(
    id="test-3",
    title="Test Task 3",
    description="Test task 3",
    status="done"
)
assert task3.status == BeadsTaskStatus.CLOSED
print(f"✓ Status normalized from 'done' to: {task3.status} (value: {task3.status.value})")

# Test 4: Create with "in_progress" string
print("\n4. Creating task with 'in_progress' string status...")
task4 = BeadsTask(
    id="test-4",
    title="Test Task 4",
    description="Test task 4",
    status="in_progress"
)
assert task4.status == BeadsTaskStatus.IN_PROGRESS
print(f"✓ Status: {task4.status} (value: {task4.status.value})")

# Test 5: from_dict with "open" status
print("\n5. Creating task from dict with 'open' status...")
data = {
    "id": "test-5",
    "title": "Test Task 5",
    "description": "Test from dict",
    "status": "open"
}
task5 = BeadsTask.from_dict(data)
assert task5.status == BeadsTaskStatus.TODO
print(f"✓ Status normalized from 'open' to: {task5.status} (value: {task5.status.value})")

print("\n" + "="*60)
print("All status normalization tests passed! ✓")
print("="*60)
