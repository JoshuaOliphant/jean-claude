#!/usr/bin/env python3
"""Quick verification script for BeadsTask implementation."""

import sys
sys.path.insert(0, 'src')

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, BeadsConfig

# Test 1: Create a BeadsTask
print("Test 1: Creating BeadsTask...")
task = BeadsTask(
    id='test-1',
    title='Test Task',
    description='A test task',
    status=BeadsTaskStatus.TODO
)
print(f"✓ BeadsTask created: {task.id}")

# Test 2: Test from_dict
print("\nTest 2: Testing from_dict...")
task_dict = {
    'id': 'test-2',
    'title': 'Dict Task',
    'description': 'From dict',
    'status': BeadsTaskStatus.IN_PROGRESS
}
task2 = BeadsTask.from_dict(task_dict)
print(f"✓ BeadsTask from_dict: {task2.id}")

# Test 3: Test to_dict
print("\nTest 3: Testing to_dict...")
task_dict_out = task.to_dict()
print(f"✓ BeadsTask to_dict: {list(task_dict_out.keys())}")

# Test 4: Create BeadsConfig
print("\nTest 4: Creating BeadsConfig...")
config = BeadsConfig()
print(f"✓ BeadsConfig created: cli_path={config.cli_path}")

print("\n✓ All verification tests passed!")
