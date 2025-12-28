#!/usr/bin/env python
"""Validate spec generator implementation."""

from datetime import datetime
from jean_claude.core.beads import BeadsTask, generate_spec_from_beads


def test_basic_spec_generation():
    """Test basic spec generation."""
    print("Test 1: Basic spec generation...")
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="This is a test task",
        acceptance_criteria=["AC 1", "AC 2"],
        status="not_started"
    )

    spec = generate_spec_from_beads(task)
    print(spec)
    print()

    assert "# Test Task" in spec
    assert "## Description" in spec
    assert "This is a test task" in spec
    assert "## Acceptance Criteria" in spec
    assert "- AC 1" in spec
    assert "- AC 2" in spec
    print("✅ Test 1 passed!\n")


def test_without_acceptance_criteria():
    """Test spec generation without acceptance criteria."""
    print("Test 2: Spec without acceptance criteria...")
    task = BeadsTask(
        id="test-2",
        title="No AC Task",
        description="Task without criteria",
        status="done"
    )

    spec = generate_spec_from_beads(task)
    print(spec)
    print()

    assert "# No AC Task" in spec
    assert "## Description" in spec
    assert "Task without criteria" in spec
    print("✅ Test 2 passed!\n")


def test_none_task_raises_error():
    """Test that None task raises error."""
    print("Test 3: None task raises ValueError...")
    try:
        generate_spec_from_beads(None)
        print("❌ Test 3 failed - should have raised ValueError")
        return False
    except ValueError as e:
        assert "task cannot be None" in str(e)
        print(f"✅ Test 3 passed - got expected error: {e}\n")
        return True


def test_spec_ends_with_newline():
    """Test that spec ends with newline."""
    print("Test 4: Spec ends with newline...")
    task = BeadsTask(
        id="test-4",
        title="Newline Test",
        description="Test",
        status="not_started"
    )

    spec = generate_spec_from_beads(task)
    assert spec.endswith("\n"), "Spec should end with newline"
    print("✅ Test 4 passed!\n")


def test_unicode_characters():
    """Test unicode character preservation."""
    print("Test 5: Unicode characters...")
    task = BeadsTask(
        id="test-5",
        title="Task with émojis 🚀",
        description="Café naïve 日本語",
        acceptance_criteria=["✓ Check"],
        status="not_started"
    )

    spec = generate_spec_from_beads(task)
    print(spec)
    print()

    assert "émojis" in spec
    assert "🚀" in spec
    assert "Café" in spec
    assert "日本語" in spec
    assert "✓" in spec
    print("✅ Test 5 passed!\n")


if __name__ == "__main__":
    print("="*60)
    print("VALIDATING SPEC GENERATOR IMPLEMENTATION")
    print("="*60)
    print()

    try:
        test_basic_spec_generation()
        test_without_acceptance_criteria()
        test_none_task_raises_error()
        test_spec_ends_with_newline()
        test_unicode_characters()

        print("="*60)
        print("✅ ALL VALIDATION TESTS PASSED!")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ Validation failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
