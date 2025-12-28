#!/usr/bin/env python3
"""Inline test to verify TaskValidator works."""

import sys
sys.path.insert(0, 'src')

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus
from jean_claude.core.task_validator import TaskValidator, ValidationResult

# Test 1: ValidationResult basics
print("Test 1: ValidationResult")
result = ValidationResult()
print(f"  is_valid: {result.is_valid}")
print(f"  has_warnings: {result.has_warnings()}")
print(f"  message: {result.get_message()}")

# Test 2: TaskValidator with short description
print("\nTest 2: Short description")
validator = TaskValidator()
task = BeadsTask(
    id="test-1",
    title="Test",
    description="Short",
    status=BeadsTaskStatus.OPEN
)
result = validator.validate(task)
print(f"  Warnings: {len(result.warnings)}")
for w in result.warnings:
    print(f"    - {w}")

# Test 3: TaskValidator with good task
print("\nTest 3: Good task")
task = BeadsTask(
    id="test-2",
    title="Good Task",
    description="This is a detailed description that includes testing requirements and is long enough",
    acceptance_criteria=["AC 1", "AC 2"],
    status=BeadsTaskStatus.OPEN
)
result = validator.validate(task)
print(f"  Warnings: {len(result.warnings)}")
print(f"  Valid: {result.is_valid}")

print("\n✓ All inline tests completed successfully!")
