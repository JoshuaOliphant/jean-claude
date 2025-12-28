#!/usr/bin/env python3
"""Quick verification script for spec generation feature."""

from datetime import datetime
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, generate_spec_from_beads


def test_basic_spec_generation():
    """Test basic spec generation functionality."""
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
    assert len(spec) > 0, "Spec should not be empty"
    assert "# Test Task Title" in spec, "Should include title"
    assert "## Description" in spec, "Should include description section"
    assert "This is a test task description." in spec, "Should include description content"
    assert "## Acceptance Criteria" in spec, "Should include acceptance criteria section"
    assert "- Criterion 1" in spec, "Should include first criterion"
    assert "- Criterion 2" in spec, "Should include second criterion"
    assert "- Criterion 3" in spec, "Should include third criterion"
    assert "## Task Metadata" in spec, "Should include metadata section"
    assert "test-123" in spec, "Should include task ID"

    print("✓ All basic checks passed!")
    print("\nGenerated spec:")
    print("=" * 80)
    print(spec)
    print("=" * 80)


def test_none_task():
    """Test that None task raises ValueError."""
    try:
        generate_spec_from_beads(None)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "task cannot be None" in str(e)
        print("✓ None task correctly raises ValueError")


if __name__ == "__main__":
    print("Verifying spec generation feature...")
    print()

    test_basic_spec_generation()
    print()
    test_none_task()

    print()
    print("✅ All verification checks passed!")
    print("The generate_spec_from_beads feature is working correctly.")
