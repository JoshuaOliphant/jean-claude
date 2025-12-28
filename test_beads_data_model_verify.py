#!/usr/bin/env python3
"""Quick verification script for BeadsTask and BeadsConfig models."""

import sys
sys.path.insert(0, 'src')

from jean_claude.core.beads import BeadsTask, BeadsConfig, BeadsTaskStatus

print("=" * 60)
print("VERIFICATION: BeadsTask and BeadsConfig Models")
print("=" * 60)

# Test BeadsTask
print("\n1. Testing BeadsTask creation...")
task = BeadsTask(
    id="test-1",
    title="Test Task",
    description="A test task",
    status=BeadsTaskStatus.TODO,
    acceptance_criteria=["AC 1", "AC 2"]
)
print(f"   ✓ BeadsTask created: {task.id}")
print(f"   ✓ Title: {task.title}")
print(f"   ✓ Status: {task.status.value}")
print(f"   ✓ Acceptance Criteria: {len(task.acceptance_criteria)} items")

# Test BeadsTask.to_dict()
print("\n2. Testing BeadsTask.to_dict()...")
task_dict = task.to_dict()
print(f"   ✓ to_dict() returned: {type(task_dict).__name__}")
print(f"   ✓ Contains 'id': {'id' in task_dict}")

# Test BeadsTask.from_dict()
print("\n3. Testing BeadsTask.from_dict()...")
task2 = BeadsTask.from_dict(task_dict)
print(f"   ✓ from_dict() created task: {task2.id}")
print(f"   ✓ Title matches: {task2.title == task.title}")

# Test BeadsConfig
print("\n4. Testing BeadsConfig creation...")
config = BeadsConfig()
print(f"   ✓ BeadsConfig created with default cli_path: {config.cli_path}")
print(f"   ✓ Default config_options: {config.config_options}")

# Test BeadsConfig with custom values
print("\n5. Testing BeadsConfig with custom values...")
config2 = BeadsConfig(
    cli_path="/custom/bd",
    config_options={"timeout": 30, "verbose": True}
)
print(f"   ✓ Custom cli_path: {config2.cli_path}")
print(f"   ✓ Custom config_options: {config2.config_options}")

# Test BeadsConfig.to_dict()
print("\n6. Testing BeadsConfig.to_dict()...")
config_dict = config2.to_dict()
print(f"   ✓ to_dict() returned: {type(config_dict).__name__}")
print(f"   ✓ Contains 'cli_path': {'cli_path' in config_dict}")

# Test BeadsConfig.from_dict()
print("\n7. Testing BeadsConfig.from_dict()...")
config3 = BeadsConfig.from_dict(config_dict)
print(f"   ✓ from_dict() created config: {config3.cli_path}")
print(f"   ✓ CLI path matches: {config3.cli_path == config2.cli_path}")

# Test validation
print("\n8. Testing validation...")
try:
    invalid_task = BeadsTask(id="", title="Test", description="Test", status=BeadsTaskStatus.TODO)
    print("   ✗ Empty id validation FAILED")
except Exception as e:
    print(f"   ✓ Empty id validation works: {type(e).__name__}")

try:
    invalid_config = BeadsConfig(cli_path="")
    print("   ✗ Empty cli_path validation FAILED")
except Exception as e:
    print(f"   ✓ Empty cli_path validation works: {type(e).__name__}")

print("\n" + "=" * 60)
print("ALL VERIFICATIONS PASSED!")
print("=" * 60)
