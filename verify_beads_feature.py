#!/usr/bin/env python3
"""Verify beads-data-model feature implementation."""

import sys
from datetime import datetime

# Test imports
try:
    from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, BeadsConfig
    print("✓ Imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test BeadsTask creation
try:
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="A test task",
        status=BeadsTaskStatus.TODO
    )
    print("✓ BeadsTask creation successful")
except Exception as e:
    print(f"✗ BeadsTask creation failed: {e}")
    sys.exit(1)

# Test BeadsTask has all required fields
required_fields = ['id', 'title', 'description', 'status', 'acceptance_criteria', 'created_at', 'updated_at']
for field in required_fields:
    if not hasattr(task, field):
        print(f"✗ BeadsTask missing required field: {field}")
        sys.exit(1)
print(f"✓ BeadsTask has all required fields: {', '.join(required_fields)}")

# Test from_dict() method
try:
    data = {
        "id": "test-2",
        "title": "Dict Test",
        "description": "Testing from_dict",
        "status": BeadsTaskStatus.IN_PROGRESS
    }
    task_from_dict = BeadsTask.from_dict(data)
    assert task_from_dict.id == "test-2"
    assert task_from_dict.title == "Dict Test"
    print("✓ BeadsTask.from_dict() works correctly")
except Exception as e:
    print(f"✗ BeadsTask.from_dict() failed: {e}")
    sys.exit(1)

# Test to_dict() method
try:
    task_dict = task.to_dict()
    assert isinstance(task_dict, dict)
    assert task_dict['id'] == 'test-1'
    print("✓ BeadsTask.to_dict() works correctly")
except Exception as e:
    print(f"✗ BeadsTask.to_dict() failed: {e}")
    sys.exit(1)

# Test BeadsConfig creation
try:
    config = BeadsConfig()
    assert config.cli_path == "bd"
    assert config.config_options == {}
    print("✓ BeadsConfig creation successful")
except Exception as e:
    print(f"✗ BeadsConfig creation failed: {e}")
    sys.exit(1)

# Test BeadsConfig from_dict() and to_dict()
try:
    config_data = {"cli_path": "/custom/bd", "config_options": {"timeout": 30}}
    config_from_dict = BeadsConfig.from_dict(config_data)
    assert config_from_dict.cli_path == "/custom/bd"
    config_dict = config_from_dict.to_dict()
    assert isinstance(config_dict, dict)
    print("✓ BeadsConfig.from_dict() and to_dict() work correctly")
except Exception as e:
    print(f"✗ BeadsConfig methods failed: {e}")
    sys.exit(1)

print("\n✓✓✓ All verification checks passed! ✓✓✓")
print("\nFeature requirements met:")
print("  - BeadsTask data model with required fields: ✓")
print("  - from_dict() class method: ✓")
print("  - to_dict() instance method: ✓")
print("  - BeadsConfig model: ✓")
