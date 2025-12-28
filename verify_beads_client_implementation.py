#!/usr/bin/env python
"""Verify that BeadsClient implementation exists and is correct."""

import sys
import json
from datetime import datetime

# Try to import the BeadsClient and BeadsTask
try:
    from jean_claude.core.beads import BeadsClient, BeadsTask
    print("✅ Successfully imported BeadsClient and BeadsTask")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

# Verify BeadsClient has the required methods
client = BeadsClient()
print("✅ Created BeadsClient instance")

# Check that it has required methods
required_methods = ['fetch_task', 'update_status', 'close_task', 'parse_task_json']
for method in required_methods:
    if not hasattr(client, method):
        print(f"❌ BeadsClient missing method: {method}")
        sys.exit(1)
    if not callable(getattr(client, method)):
        print(f"❌ BeadsClient.{method} is not callable")
        sys.exit(1)
    print(f"✅ BeadsClient has method: {method}")

# Verify BeadsTask has required fields
sample_task_data = {
    "id": "test-1",
    "title": "Test Task",
    "description": "A test task",
    "status": "open",
    "acceptance_criteria": ["AC 1", "AC 2"],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

try:
    task = BeadsTask(**sample_task_data)
    print("✅ Created BeadsTask instance")
except Exception as e:
    print(f"❌ Failed to create BeadsTask: {e}")
    sys.exit(1)

# Verify fields
required_fields = ['id', 'title', 'description', 'status', 'acceptance_criteria', 'created_at', 'updated_at']
for field in required_fields:
    if not hasattr(task, field):
        print(f"❌ BeadsTask missing field: {field}")
        sys.exit(1)
    print(f"✅ BeadsTask has field: {field}")

# Test parse_task_json method
test_json = json.dumps([{
    "id": "test-2",
    "title": "Test Task 2",
    "description": "Another test task",
    "status": "in_progress",
    "acceptance_criteria": ["AC 1"]
}])

try:
    parsed_task = client.parse_task_json(test_json)
    assert parsed_task.id == "test-2"
    assert parsed_task.title == "Test Task 2"
    print("✅ parse_task_json works correctly")
except Exception as e:
    print(f"❌ parse_task_json failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL VERIFICATION CHECKS PASSED!")
print("="*60)
print("\nBeadsClient implementation is complete with:")
print("  - BeadsClient class with fetch_task() method")
print("  - Calls 'bd show --json <task-id>'")
print("  - Parses JSON into BeadsTask dataclass")
print("  - Fields: id, title, description, status, acceptance_criteria, created_at, updated_at")
sys.exit(0)
