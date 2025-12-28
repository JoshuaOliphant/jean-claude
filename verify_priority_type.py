#!/usr/bin/env python
"""Quick verification script for priority and type validation feature."""

import sys

# Test 1: Import the enums
print("Test 1: Importing enums...")
try:
    from jean_claude.core.beads import BeadsTaskPriority, BeadsTaskType, BeadsTask, BeadsTaskStatus
    print("✓ Enums imported successfully")
except Exception as e:
    print(f"✗ Failed to import enums: {e}")
    sys.exit(1)

# Test 2: Check enum values
print("\nTest 2: Checking enum values...")
try:
    assert BeadsTaskPriority.LOW == "low"
    assert BeadsTaskPriority.MEDIUM == "medium"
    assert BeadsTaskPriority.HIGH == "high"
    assert BeadsTaskPriority.CRITICAL == "critical"

    assert BeadsTaskType.BUG == "bug"
    assert BeadsTaskType.FEATURE == "feature"
    assert BeadsTaskType.CHORE == "chore"
    assert BeadsTaskType.DOCS == "docs"
    print("✓ Enum values are correct")
except AssertionError as e:
    print(f"✗ Enum values are incorrect: {e}")
    sys.exit(1)

# Test 3: Create task with priority and type
print("\nTest 3: Creating task with priority and type...")
try:
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="A detailed task description for testing",
        status=BeadsTaskStatus.OPEN,
        priority=BeadsTaskPriority.HIGH,
        task_type=BeadsTaskType.FEATURE
    )
    assert task.priority == BeadsTaskPriority.HIGH
    assert task.task_type == BeadsTaskType.FEATURE
    print("✓ Task created with priority and type")
except Exception as e:
    print(f"✗ Failed to create task: {e}")
    sys.exit(1)

# Test 4: Create task with string values
print("\nTest 4: Creating task with string priority and type...")
try:
    task = BeadsTask(
        id="test-2",
        title="Test Task 2",
        description="Another detailed task description",
        status=BeadsTaskStatus.OPEN,
        priority="low",
        task_type="bug"
    )
    assert task.priority == BeadsTaskPriority.LOW
    assert task.task_type == BeadsTaskType.BUG
    print("✓ Task created with string values")
except Exception as e:
    print(f"✗ Failed to create task with strings: {e}")
    sys.exit(1)

# Test 5: Create task without priority/type (should be None)
print("\nTest 5: Creating task without priority/type...")
try:
    task = BeadsTask(
        id="test-3",
        title="Test Task 3",
        description="Task without priority or type",
        status=BeadsTaskStatus.OPEN
    )
    assert task.priority is None
    assert task.task_type is None
    print("✓ Task created without priority/type (defaults to None)")
except Exception as e:
    print(f"✗ Failed to create task: {e}")
    sys.exit(1)

# Test 6: Test invalid priority
print("\nTest 6: Testing invalid priority...")
try:
    task = BeadsTask(
        id="test-4",
        title="Test Task 4",
        description="Task with invalid priority",
        status=BeadsTaskStatus.OPEN,
        priority="invalid"
    )
    print("✗ Should have raised ValueError for invalid priority")
    sys.exit(1)
except ValueError as e:
    if "Invalid priority" in str(e):
        print(f"✓ Invalid priority rejected: {e}")
    else:
        print(f"✗ Wrong error message: {e}")
        sys.exit(1)

# Test 7: Test invalid type
print("\nTest 7: Testing invalid type...")
try:
    task = BeadsTask(
        id="test-5",
        title="Test Task 5",
        description="Task with invalid type",
        status=BeadsTaskStatus.OPEN,
        task_type="invalid"
    )
    print("✗ Should have raised ValueError for invalid type")
    sys.exit(1)
except ValueError as e:
    if "Invalid task_type" in str(e):
        print(f"✓ Invalid type rejected: {e}")
    else:
        print(f"✗ Wrong error message: {e}")
        sys.exit(1)

# Test 8: Import and test TaskValidator
print("\nTest 8: Testing TaskValidator...")
try:
    from jean_claude.core.task_validator import TaskValidator

    validator = TaskValidator()

    # Test task without priority/type
    task = BeadsTask(
        id="test-6",
        title="Test Task",
        description="A detailed task description with test mentions",
        acceptance_criteria=["Criterion 1"],
        status=BeadsTaskStatus.OPEN
    )

    result = validator.validate(task)
    priority_warnings = [w for w in result.warnings if "priority" in w.lower()]
    type_warnings = [w for w in result.warnings if "type" in w.lower() and "task type" in w.lower()]

    assert len(priority_warnings) == 1, f"Expected 1 priority warning, got {len(priority_warnings)}"
    assert len(type_warnings) == 1, f"Expected 1 type warning, got {len(type_warnings)}"
    print("✓ TaskValidator detects missing priority and type")
except Exception as e:
    print(f"✗ TaskValidator test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 9: Test TaskValidator with priority and type
print("\nTest 9: Testing TaskValidator with priority and type...")
try:
    task = BeadsTask(
        id="test-7",
        title="Test Task",
        description="A detailed task description with test mentions",
        acceptance_criteria=["Criterion 1"],
        status=BeadsTaskStatus.OPEN,
        priority=BeadsTaskPriority.MEDIUM,
        task_type=BeadsTaskType.FEATURE
    )

    result = validator.validate(task)
    priority_warnings = [w for w in result.warnings if "priority" in w.lower()]
    type_warnings = [w for w in result.warnings if "type" in w.lower() and "task type" in w.lower()]

    assert len(priority_warnings) == 0, f"Expected 0 priority warnings, got {len(priority_warnings)}"
    assert len(type_warnings) == 0, f"Expected 0 type warnings, got {len(type_warnings)}"
    print("✓ TaskValidator accepts valid priority and type")
except Exception as e:
    print(f"✗ TaskValidator test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("All verification tests passed! ✓")
print("="*60)
