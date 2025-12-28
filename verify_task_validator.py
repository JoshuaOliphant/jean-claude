#!/usr/bin/env python3
"""Quick verification script for TaskValidator feature."""

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus
from jean_claude.core.task_validator import TaskValidator, ValidationResult


def test_validation_result():
    """Test ValidationResult basic functionality."""
    print("Testing ValidationResult...")

    # Test defaults
    result = ValidationResult()
    assert result.is_valid is True
    assert result.warnings == []
    assert result.errors == []
    print("✓ Default initialization works")

    # Test with values
    result = ValidationResult(
        is_valid=False,
        warnings=["Warning 1"],
        errors=["Error 1"]
    )
    assert result.has_warnings() is True
    assert result.has_errors() is True
    print("✓ ValidationResult with values works")

    # Test get_message
    message = result.get_message()
    assert "WARNINGS:" in message
    assert "ERRORS:" in message
    print("✓ get_message() works")

    print("ValidationResult: All tests passed!\n")


def test_task_validator():
    """Test TaskValidator basic functionality."""
    print("Testing TaskValidator...")

    # Test initialization
    validator = TaskValidator()
    assert validator.min_description_length == 50
    print("✓ TaskValidator initialization works")

    # Test with a short description
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="Short",
        status=BeadsTaskStatus.OPEN
    )

    result = validator.validate(task)
    assert result.has_warnings() is True
    assert len(result.warnings) == 3  # Short desc + no AC + no tests
    print(f"✓ Short description validation works (found {len(result.warnings)} warnings)")

    # Test with a good task
    task = BeadsTask(
        id="test-2",
        title="Good Task",
        description="This is a detailed task description that contains enough information " +
                   "and mentions that we need to test the implementation thoroughly.",
        acceptance_criteria=["Feature works", "All tests pass"],
        status=BeadsTaskStatus.OPEN
    )

    result = validator.validate(task)
    assert result.has_warnings() is False
    assert result.is_valid is True
    print("✓ Well-formed task validation works (no warnings)")

    print("TaskValidator: All tests passed!\n")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("TASK VALIDATOR FEATURE VERIFICATION")
    print("=" * 60 + "\n")

    try:
        test_validation_result()
        test_task_validator()

        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
