#!/usr/bin/env python
"""Validate spec generation implementation manually."""

from datetime import datetime
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, generate_spec_from_beads


def test_basic_functionality():
    """Test basic spec generation."""
    print("Testing basic spec generation...")

    task = BeadsTask(
        id="test-123",
        title="Test Task Title",
        description="This is a test task description.",
        acceptance_criteria=["Criterion 1", "Criterion 2", "Criterion 3"],
        status=BeadsTaskStatus.TODO,
        created_at=datetime(2025, 1, 1, 12, 0, 0),
        updated_at=datetime(2025, 1, 2, 12, 0, 0)
    )

    spec = generate_spec_from_beads(task)

    # Verify basic structure
    assert isinstance(spec, str), "Spec should be a string"
    assert len(spec.strip()) > 0, "Spec should not be empty"
    assert "# Test Task Title" in spec, "Should include title"
    assert "## Description" in spec, "Should include Description section"
    assert "This is a test task description." in spec, "Should include description content"
    assert "## Acceptance Criteria" in spec, "Should include Acceptance Criteria section"
    assert "- Criterion 1" in spec, "Should include first criterion"
    assert "- Criterion 2" in spec, "Should include second criterion"
    assert "- Criterion 3" in spec, "Should include third criterion"

    print("✅ Basic spec generation works correctly")
    print("\nGenerated spec:")
    print("=" * 60)
    print(spec)
    print("=" * 60)


def test_without_criteria():
    """Test spec generation without acceptance criteria."""
    print("\nTesting spec generation without acceptance criteria...")

    task = BeadsTask(
        id="test-456",
        title="Simple Task",
        description="A task without acceptance criteria.",
        acceptance_criteria=[],
        status=BeadsTaskStatus.IN_PROGRESS
    )

    spec = generate_spec_from_beads(task)

    assert "# Simple Task" in spec, "Should include title"
    assert "## Description" in spec, "Should include Description section"
    assert "A task without acceptance criteria." in spec, "Should include description"

    print("✅ Spec generation without criteria works correctly")


def test_none_input():
    """Test that None input raises ValueError."""
    print("\nTesting None input handling...")

    try:
        generate_spec_from_beads(None)
        print("❌ Should have raised ValueError for None input")
        return False
    except ValueError as e:
        if "task cannot be None" in str(e):
            print("✅ Correctly raises ValueError for None input")
        else:
            print(f"❌ Unexpected error message: {e}")
            return False

    return True


def test_unicode_support():
    """Test unicode character support."""
    print("\nTesting unicode support...")

    task = BeadsTask(
        id="test-unicode",
        title="Task with émojis 🚀 and ünïcödé",
        description="Description with unicode: café, naïve, 日本語",
        acceptance_criteria=["✓ Handle unicode", "✗ Don't fail"],
        status=BeadsTaskStatus.TODO
    )

    spec = generate_spec_from_beads(task)

    assert "Task with émojis 🚀 and ünïcödé" in spec, "Should handle unicode in title"
    assert "café" in spec, "Should handle accented characters"
    assert "naïve" in spec, "Should handle accented characters"
    assert "日本語" in spec, "Should handle CJK characters"
    assert "✓ Handle unicode" in spec, "Should handle unicode in criteria"

    print("✅ Unicode support works correctly")


def test_integration_workflow():
    """Test complete workflow: dict -> BeadsTask -> spec."""
    print("\nTesting integration workflow...")

    # Simulate what would come from 'bd show --json'
    task_dict = {
        "id": "workflow-123",
        "title": "Implement Feature X",
        "description": "Add new feature to the application",
        "acceptance_criteria": [
            "Feature works as expected",
            "Tests pass",
            "Documentation updated"
        ],
        "status": "in_progress"
    }

    # Create task from dict
    task = BeadsTask.from_dict(task_dict)

    # Generate spec
    spec = generate_spec_from_beads(task)

    # Verify spec is valid and complete
    assert "# Implement Feature X" in spec, "Should include title"
    assert "## Description" in spec, "Should include Description section"
    assert "Add new feature to the application" in spec, "Should include description"
    assert "## Acceptance Criteria" in spec, "Should include AC section"
    assert "- Feature works as expected" in spec, "Should include first AC"
    assert "- Tests pass" in spec, "Should include second AC"
    assert "- Documentation updated" in spec, "Should include third AC"

    print("✅ Integration workflow works correctly")


if __name__ == "__main__":
    print("="*60)
    print("VALIDATING SPEC GENERATION IMPLEMENTATION")
    print("="*60)

    try:
        test_basic_functionality()
        test_without_criteria()
        test_none_input()
        test_unicode_support()
        test_integration_workflow()

        print("\n" + "="*60)
        print("✅ ALL VALIDATIONS PASSED!")
        print("="*60)
        print("\nThe generate_spec_from_beads() function is working correctly.")
        print("The test suite in tests/test_spec_generation.py should pass.")

    except AssertionError as e:
        print("\n" + "="*60)
        print("❌ VALIDATION FAILED!")
        print("="*60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    except Exception as e:
        print("\n" + "="*60)
        print("❌ UNEXPECTED ERROR!")
        print("="*60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
