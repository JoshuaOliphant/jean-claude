#!/usr/bin/env python
"""Verify CommitMessageFormatter implementation."""

import sys
import traceback

def main():
    """Verify the commit message formatter works correctly."""
    try:
        # Import the class
        from jean_claude.core.commit_message_formatter import CommitMessageFormatter
        print("✅ Successfully imported CommitMessageFormatter")

        # Test 1: Basic formatting
        print("\nTest 1: Basic formatting")
        formatter = CommitMessageFormatter(
            commit_type="feat",
            scope="auth",
            summary="add login functionality",
            body_items=["Implement JWT authentication", "Add password hashing"],
            beads_task_id="task-123.1",
            feature_number=1
        )
        message = formatter.format()

        assert message.startswith("feat(auth): add login functionality"), "Header mismatch"
        assert "- Implement JWT authentication" in message, "Body item 1 missing"
        assert "- Add password hashing" in message, "Body item 2 missing"
        assert "Beads-Task-Id: task-123.1" in message, "Task ID missing"
        assert "Feature-Number: 1" in message, "Feature number missing"
        print("✅ Basic formatting test passed")

        # Test 2: Invalid commit type
        print("\nTest 2: Invalid commit type")
        try:
            CommitMessageFormatter(
                commit_type="invalid",
                scope="test",
                summary="test",
                body_items=[],
                beads_task_id="test.1",
                feature_number=1
            )
            print("❌ Should have raised ValueError for invalid commit type")
            return 1
        except ValueError as e:
            assert "Invalid commit_type" in str(e), f"Wrong error message: {e}"
            print("✅ Invalid commit type validation passed")

        # Test 3: Empty summary
        print("\nTest 3: Empty summary")
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
            return 1
        except ValueError as e:
            assert "summary cannot be empty" in str(e), f"Wrong error message: {e}"
            print("✅ Empty summary validation passed")

        # Test 4: Negative feature number
        print("\nTest 4: Negative feature number")
        try:
            CommitMessageFormatter(
                commit_type="feat",
                scope="test",
                summary="test",
                body_items=[],
                beads_task_id="test.1",
                feature_number=-1
            )
            print("❌ Should have raised ValueError for negative feature number")
            return 1
        except ValueError as e:
            assert "feature_number must be positive" in str(e), f"Wrong error message: {e}"
            print("✅ Negative feature number validation passed")

        # Test 5: No scope
        print("\nTest 5: Commit without scope")
        formatter = CommitMessageFormatter(
            commit_type="docs",
            scope=None,
            summary="update README",
            body_items=["Add installation instructions"],
            beads_task_id="test.1",
            feature_number=1
        )
        message = formatter.format()
        assert message.startswith("docs: update README"), "Header without scope is wrong"
        assert "(" not in message.split("\n")[0], "Should not have parentheses without scope"
        print("✅ No scope test passed")

        # Test 6: All valid types
        print("\nTest 6: All valid commit types")
        valid_types = ["feat", "fix", "refactor", "test", "docs"]
        for commit_type in valid_types:
            formatter = CommitMessageFormatter(
                commit_type=commit_type,
                scope="test",
                summary="test message",
                body_items=[],
                beads_task_id="test.1",
                feature_number=1
            )
            message = formatter.format()
            assert message.startswith(f"{commit_type}(test): test message"), f"Type {commit_type} failed"
        print("✅ All valid commit types passed")

        print("\n" + "="*60)
        print("🎉 ALL VERIFICATION TESTS PASSED!")
        print("="*60)
        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
