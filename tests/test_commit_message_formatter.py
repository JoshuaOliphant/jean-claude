"""Tests for CommitMessageFormatter class."""

import pytest

from jean_claude.core.commit_message_formatter import CommitMessageFormatter


class TestCommitMessageFormatter:
    """Test CommitMessageFormatter class."""

    def test_basic_feat_commit(self):
        """Test generating a basic feat commit message."""
        formatter = CommitMessageFormatter(
            commit_type="feat",
            scope="auth",
            summary="add login functionality",
            body_items=["Implement JWT authentication", "Add password hashing"],
            beads_task_id="task-123.1",
            feature_number=1
        )

        message = formatter.format()

        # Check header
        assert message.startswith("feat(auth): add login functionality")

        # Check body items are present
        assert "- Implement JWT authentication" in message
        assert "- Add password hashing" in message

        # Check trailers
        assert "Beads-Task-Id: task-123.1" in message
        assert "Feature-Number: 1" in message

    def test_fix_commit_with_scope(self):
        """Test generating a fix commit message with scope."""
        formatter = CommitMessageFormatter(
            commit_type="fix",
            scope="api",
            summary="resolve timeout in user endpoint",
            body_items=["Increase connection timeout to 30s"],
            beads_task_id="task-456.2",
            feature_number=3
        )

        message = formatter.format()

        assert message.startswith("fix(api): resolve timeout in user endpoint")
        assert "- Increase connection timeout to 30s" in message
        assert "Beads-Task-Id: task-456.2" in message
        assert "Feature-Number: 3" in message

    def test_commit_without_scope(self):
        """Test generating a commit message without scope."""
        formatter = CommitMessageFormatter(
            commit_type="docs",
            scope=None,
            summary="update README with installation instructions",
            body_items=["Add pip install command", "Add usage examples"],
            beads_task_id="task-789.1",
            feature_number=5
        )

        message = formatter.format()

        # Should not have parentheses when scope is None
        assert message.startswith("docs: update README with installation instructions")
        assert "- Add pip install command" in message
        assert "- Add usage examples" in message

    def test_commit_with_empty_body_items(self):
        """Test generating a commit message with no body items."""
        formatter = CommitMessageFormatter(
            commit_type="refactor",
            scope="database",
            summary="simplify query builder",
            body_items=[],
            beads_task_id="task-111.1",
            feature_number=2
        )

        message = formatter.format()

        assert message.startswith("refactor(database): simplify query builder")
        # Trailers should still be present
        assert "Beads-Task-Id: task-111.1" in message
        assert "Feature-Number: 2" in message

    def test_all_valid_commit_types(self):
        """Test all valid conventional commit types."""
        valid_types = ["feat", "fix", "refactor", "test", "docs"]

        for commit_type in valid_types:
            formatter = CommitMessageFormatter(
                commit_type=commit_type,
                scope="test",
                summary="test message",
                body_items=["Test item"],
                beads_task_id="test.1",
                feature_number=1
            )
            message = formatter.format()
            assert message.startswith(f"{commit_type}(test): test message")

    def test_invalid_commit_type(self):
        """Test that invalid commit types raise ValueError."""
        with pytest.raises(ValueError, match="Invalid commit_type"):
            CommitMessageFormatter(
                commit_type="invalid",
                scope="test",
                summary="test message",
                body_items=[],
                beads_task_id="test.1",
                feature_number=1
            )

    def test_empty_summary_raises_error(self):
        """Test that empty summary raises ValueError."""
        with pytest.raises(ValueError, match="summary cannot be empty"):
            CommitMessageFormatter(
                commit_type="feat",
                scope="test",
                summary="",
                body_items=[],
                beads_task_id="test.1",
                feature_number=1
            )

    def test_multiple_body_items(self):
        """Test commit with multiple body items."""
        body_items = [
            "Add user registration endpoint",
            "Add email verification",
            "Add password reset functionality",
            "Update user model schema"
        ]

        formatter = CommitMessageFormatter(
            commit_type="feat",
            scope="users",
            summary="implement complete user management",
            body_items=body_items,
            beads_task_id="task-999.5",
            feature_number=7
        )

        message = formatter.format()

        # All body items should be present as bullet points
        for item in body_items:
            assert f"- {item}" in message

    def test_message_structure(self):
        """Test that the commit message has proper structure."""
        formatter = CommitMessageFormatter(
            commit_type="feat",
            scope="core",
            summary="add new feature",
            body_items=["First change", "Second change"],
            beads_task_id="task-abc.1",
            feature_number=4
        )

        message = formatter.format()
        lines = message.split("\n")

        # First line should be the header
        assert lines[0] == "feat(core): add new feature"

        # Should have blank line after header if body exists
        assert lines[1] == ""

        # Body items should be present
        assert "- First change" in message
        assert "- Second change" in message

        # Trailers should be at the end
        assert message.strip().endswith("Feature-Number: 4")

    def test_scope_with_special_characters(self):
        """Test scope with hyphens and underscores."""
        formatter = CommitMessageFormatter(
            commit_type="feat",
            scope="user-auth",
            summary="add OAuth support",
            body_items=["Integrate OAuth provider"],
            beads_task_id="task-123.1",
            feature_number=1
        )

        message = formatter.format()
        assert message.startswith("feat(user-auth): add OAuth support")

    def test_test_commit_type(self):
        """Test generating a test commit message."""
        formatter = CommitMessageFormatter(
            commit_type="test",
            scope="api",
            summary="add integration tests for auth endpoints",
            body_items=["Test login endpoint", "Test logout endpoint", "Test token refresh"],
            beads_task_id="task-test.1",
            feature_number=6
        )

        message = formatter.format()

        assert message.startswith("test(api): add integration tests for auth endpoints")
        assert "- Test login endpoint" in message
        assert "- Test logout endpoint" in message
        assert "- Test token refresh" in message

    def test_beads_task_id_format(self):
        """Test various beads task ID formats."""
        task_ids = ["task-123.1", "feature-456.2", "bug-789.3", "simple.4"]

        for task_id in task_ids:
            formatter = CommitMessageFormatter(
                commit_type="feat",
                scope="test",
                summary="test message",
                body_items=[],
                beads_task_id=task_id,
                feature_number=1
            )
            message = formatter.format()
            assert f"Beads-Task-Id: {task_id}" in message

    def test_feature_number_must_be_positive(self):
        """Test that feature number must be positive."""
        with pytest.raises(ValueError, match="feature_number must be positive"):
            CommitMessageFormatter(
                commit_type="feat",
                scope="test",
                summary="test message",
                body_items=[],
                beads_task_id="test.1",
                feature_number=0
            )

        with pytest.raises(ValueError, match="feature_number must be positive"):
            CommitMessageFormatter(
                commit_type="feat",
                scope="test",
                summary="test message",
                body_items=[],
                beads_task_id="test.1",
                feature_number=-1
            )

    def test_complete_realistic_commit(self):
        """Test a complete realistic commit message."""
        formatter = CommitMessageFormatter(
            commit_type="feat",
            scope="commit-workflow",
            summary="create CommitMessageFormatter class",
            body_items=[
                "Accept commit_type, scope, summary, body_items parameters",
                "Generate conventional commit format",
                "Include Beads-Task-Id and Feature-Number trailers",
                "Validate commit_type against allowed values",
                "Handle optional scope parameter"
            ],
            beads_task_id="beads-jean_claude-2sz.8.1",
            feature_number=1
        )

        message = formatter.format()

        # Verify structure
        assert message.startswith("feat(commit-workflow): create CommitMessageFormatter class")
        assert "\n\n" in message  # Blank line after header
        assert "- Accept commit_type, scope, summary, body_items parameters" in message
        assert "- Generate conventional commit format" in message
        assert "Beads-Task-Id: beads-jean_claude-2sz.8.1" in message
        assert "Feature-Number: 1" in message

        # Verify no trailing whitespace on lines
        for line in message.split("\n"):
            assert line == line.rstrip()
