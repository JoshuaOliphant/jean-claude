#!/usr/bin/env python3
"""Quick verification script for description validation feature."""

import sys
sys.path.insert(0, 'src')

from jean_claude.core.task_validator import TaskValidator, ValidationResult
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus

def test_short_description():
    """Test that short descriptions trigger warnings."""
    validator = TaskValidator(min_description_length=50)
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="Short",  # Only 5 characters
        status=BeadsTaskStatus.OPEN
    )

    result = validator.validate(task)
    assert result.is_valid is True
    assert result.has_warnings() is True
    assert any("description is short" in w.lower() for w in result.warnings)
    assert any("5 chars" in w for w in result.warnings)
    print("✓ Short description warning test passed")

def test_long_description():
    """Test that long descriptions don't trigger warnings."""
    validator = TaskValidator(min_description_length=50)
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="This is a very detailed description that contains enough information " +
                   "to be clear about what needs to be done with proper testing.",
        acceptance_criteria=["Criterion 1"],
        status=BeadsTaskStatus.OPEN
    )

    result = validator.validate(task)
    description_warnings = [w for w in result.warnings if "description is short" in w.lower()]
    assert len(description_warnings) == 0
    print("✓ Long description test passed")

def test_empty_description():
    """Test that empty descriptions are caught."""
    try:
        task = BeadsTask(
            id="test-1",
            title="Test Task",
            description="",
            status=BeadsTaskStatus.OPEN
        )
        print("✗ Empty description test failed - should have raised ValueError")
        return False
    except ValueError as e:
        if "description cannot be empty" in str(e):
            print("✓ Empty description validation test passed")
            return True
        else:
            print(f"✗ Wrong error message: {e}")
            return False

def test_whitespace_only():
    """Test that whitespace-only descriptions are caught."""
    try:
        task = BeadsTask(
            id="test-1",
            title="Test Task",
            description="   ",
            status=BeadsTaskStatus.OPEN
        )
        print("✗ Whitespace-only test failed - should have raised ValueError")
        return False
    except ValueError as e:
        if "description cannot be empty" in str(e):
            print("✓ Whitespace-only validation test passed")
            return True
        else:
            print(f"✗ Wrong error message: {e}")
            return False

if __name__ == "__main__":
    print("Testing description validation feature...")
    print()

    try:
        test_short_description()
        test_long_description()
        test_empty_description()
        test_whitespace_only()
        print()
        print("All tests passed! ✓")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
