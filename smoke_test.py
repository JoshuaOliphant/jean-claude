#!/usr/bin/env python3
"""Smoke test for BeadsTask model and BeadsTaskStatus enum."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus

print("Testing BeadsTaskStatus enum...")
print(f"  TODO: {BeadsTaskStatus.TODO.value}")
print(f"  IN_PROGRESS: {BeadsTaskStatus.IN_PROGRESS.value}")
print(f"  CLOSED: {BeadsTaskStatus.CLOSED.value}")

print("\nTesting BeadsTask creation with enum...")
task = BeadsTask(
    id="test-1",
    title="Test Task",
    description="A test task",
    status=BeadsTaskStatus.TODO
)
print(f"  Created task: {task.id}")
print(f"  Status type: {type(task.status)}")
print(f"  Status value: {task.status}")
print(f"  Status matches enum: {task.status == BeadsTaskStatus.TODO}")

print("\n✅ Smoke test passed!")
