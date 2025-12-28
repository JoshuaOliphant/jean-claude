#!/usr/bin/env python3
"""Quick test to verify CommitMessageFormatter works."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.core.commit_message_formatter import CommitMessageFormatter


def test_basic_formatting():
    """Test basic commit message formatting."""
    formatter = CommitMessageFormatter(
        commit_type="feat",
        scope="auth",
        summary="add login functionality",
        body_items=["Implement JWT authentication", "Add password hashing"],
        beads_task_id="task-123.1",
        feature_number=1
    )

    message = formatter.format()
    print("Generated message:")
    print(message)
    print("\n" + "="*60 + "\n")

    # Check key parts
    assert message.startswith("feat(auth): add login functionality")
    assert "- Implement JWT authentication" in message
    assert "- Add password hashing" in message
    assert "Beads-Task-Id: task-123.1" in message
    assert "Feature-Number: 1" in message

    print("✅ Basic formatting test passed!")


def test_invalid_commit_type():
    """Test that invalid commit type raises ValueError."""
    try:
        CommitMessageFormatter(
            commit_type="invalid",
            scope="test",
            summary="test message",
            body_items=[],
            beads_task_id="test.1",
            feature_number=1
        )
        print("❌ Should have raised ValueError for invalid commit type")
        sys.exit(1)
    except ValueError as e:
        assert "Invalid commit_type" in str(e)
        print("✅ Invalid commit type validation passed!")


def test_empty_summary():
    """Test that empty summary raises ValueError."""
    try:
        CommitMessageFormatter(
            commit_type="feat",
            scope="test",
            summary="",
            body_items=[],
            beads_task_id="test.1",
            feature_number=1
        )
        print("❌ Should have raised ValueError for empty summary")
        sys.exit(1)
    except ValueError as e:
        assert "summary cannot be empty" in str(e)
        print("✅ Empty summary validation passed!")


def test_negative_feature_number():
    """Test that negative feature number raises ValueError."""
    try:
        CommitMessageFormatter(
            commit_type="feat",
            scope="test",
            summary="test message",
            body_items=[],
            beads_task_id="test.1",
            feature_number=-1
        )
        print("❌ Should have raised ValueError for negative feature number")
        sys.exit(1)
    except ValueError as e:
        assert "feature_number must be positive" in str(e)
        print("✅ Negative feature number validation passed!")


if __name__ == "__main__":
    test_basic_formatting()
    test_invalid_commit_type()
    test_empty_summary()
    test_negative_feature_number()
    print("\n" + "="*60)
    print("🎉 All quick tests passed!")
    print("="*60)
