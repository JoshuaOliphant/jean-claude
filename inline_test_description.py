#!/usr/bin/env python3
"""Quick inline test to verify description validation works."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jean_claude.core.task_validator import TaskValidator, ValidationResult
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus

print("Testing description validation feature...")
print()

# Test 1: Short description triggers warning
print("Test 1: Short description triggers warning")
try:
    validator = TaskValidator(min_description_length=50)
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="Short",
        status=BeadsTaskStatus.OPEN
    )
    result = validator.validate(task)

    assert result.is_valid is True, "Result should be valid (warnings don't invalidate)"
    assert result.has_warnings() is True, "Should have warnings"

    desc_warnings = [w for w in result.warnings if "description is short" in w.lower()]
    assert len(desc_warnings) == 1, f"Should have 1 description warning, got {len(desc_warnings)}"
    assert "5 chars" in desc_warnings[0], f"Warning should mention 5 chars: {desc_warnings[0]}"

    print("  ✓ PASS")
except Exception as e:
    print(f"  ✗ FAIL: {e}")
    sys.exit(1)

# Test 2: Long description doesn't trigger warning
print("Test 2: Long description doesn't trigger warning")
try:
    validator = TaskValidator(min_description_length=50)
    task = BeadsTask(
        id="test-2",
        title="Test Task",
        description="This is a very detailed description that contains enough information " +
                   "to be clear about what needs to be done with test requirements.",
        acceptance_criteria=["AC 1"],
        status=BeadsTaskStatus.OPEN
    )
    result = validator.validate(task)

    desc_warnings = [w for w in result.warnings if "description is short" in w.lower()]
    assert len(desc_warnings) == 0, f"Should have no description warnings, got {len(desc_warnings)}"

    print("  ✓ PASS")
except Exception as e:
    print(f"  ✗ FAIL: {e}")
    sys.exit(1)

# Test 3: Empty description raises error
print("Test 3: Empty description raises ValueError")
try:
    task = BeadsTask(
        id="test-3",
        title="Test Task",
        description="",
        status=BeadsTaskStatus.OPEN
    )
    print("  ✗ FAIL: Should have raised ValueError")
    sys.exit(1)
except ValueError as e:
    if "description cannot be empty" in str(e):
        print("  ✓ PASS")
    else:
        print(f"  ✗ FAIL: Wrong error message: {e}")
        sys.exit(1)

# Test 4: Whitespace-only description raises error
print("Test 4: Whitespace-only description raises ValueError")
try:
    task = BeadsTask(
        id="test-4",
        title="Test Task",
        description="   ",
        status=BeadsTaskStatus.OPEN
    )
    print("  ✗ FAIL: Should have raised ValueError")
    sys.exit(1)
except ValueError as e:
    if "description cannot be empty" in str(e):
        print("  ✓ PASS")
    else:
        print(f"  ✗ FAIL: Wrong error message: {e}")
        sys.exit(1)

# Test 5: Whitespace is stripped when counting
print("Test 5: Whitespace is stripped when counting chars")
try:
    validator = TaskValidator(min_description_length=50)
    task = BeadsTask(
        id="test-5",
        title="Test Task",
        description="   Short   ",  # 5 chars after strip
        status=BeadsTaskStatus.OPEN
    )
    result = validator.validate(task)

    desc_warnings = [w for w in result.warnings if "description is short" in w.lower()]
    assert len(desc_warnings) == 1, f"Should have 1 description warning"
    assert "5 chars" in desc_warnings[0], f"Should count 5 chars after strip: {desc_warnings[0]}"

    print("  ✓ PASS")
except Exception as e:
    print(f"  ✗ FAIL: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("All tests passed! ✓")
print("=" * 60)
print()
print("The description length validation feature is working correctly:")
print("  - Counts characters in task description")
print("  - Adds warning if fewer than 50 characters (configurable)")
print("  - Handles empty descriptions (raises ValueError)")
print("  - Handles whitespace-only text (raises ValueError)")
print()
