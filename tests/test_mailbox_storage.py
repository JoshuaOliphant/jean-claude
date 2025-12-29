"""Tests for mailbox_storage module."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from jean_claude.core.mailbox_storage import resolve_mailbox_path
from jean_claude.core.message_writer import MessageBox
from jean_claude.core.mailbox_paths import MailboxPaths


class TestResolveMailboxPath:
    """Test cases for resolve_mailbox_path function."""

    def test_resolve_inbox_path(self, tmp_path):
        """Test resolving INBOX mailbox to inbox_path."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Act
        result = resolve_mailbox_path(MessageBox.INBOX, paths)

        # Assert
        assert result == paths.inbox_path
        assert result.name == "inbox.jsonl"

    def test_resolve_outbox_path(self, tmp_path):
        """Test resolving OUTBOX mailbox to outbox_path."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Act
        result = resolve_mailbox_path(MessageBox.OUTBOX, paths)

        # Assert
        assert result == paths.outbox_path
        assert result.name == "outbox.jsonl"

    def test_resolve_mailbox_path_returns_path_object(self, tmp_path):
        """Test that resolve_mailbox_path returns a Path object."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Act
        result = resolve_mailbox_path(MessageBox.INBOX, paths)

        # Assert
        assert isinstance(result, Path)

    def test_resolve_mailbox_path_with_invalid_type_raises_valueerror(self, tmp_path):
        """Test that passing an invalid mailbox type raises ValueError."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            resolve_mailbox_path("inbox", paths)  # String instead of enum

        assert "mailbox must be a MessageBox enum value" in str(exc_info.value)

    def test_resolve_mailbox_path_with_none_raises_valueerror(self, tmp_path):
        """Test that passing None as mailbox raises ValueError."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            resolve_mailbox_path(None, paths)

        assert "mailbox must be a MessageBox enum value" in str(exc_info.value)

    def test_resolve_mailbox_path_with_none_paths_raises_typeerror(self):
        """Test that passing None as paths raises TypeError."""
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            resolve_mailbox_path(MessageBox.INBOX, None)

        assert "paths cannot be None" in str(exc_info.value)

    def test_resolve_mailbox_path_with_integer_raises_valueerror(self, tmp_path):
        """Test that passing an integer as mailbox raises ValueError."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            resolve_mailbox_path(123, paths)

        assert "mailbox must be a MessageBox enum value" in str(exc_info.value)

    def test_resolve_mailbox_path_consistency(self, tmp_path):
        """Test that resolve_mailbox_path returns consistent results."""
        # Arrange
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Act - Call multiple times
        result1 = resolve_mailbox_path(MessageBox.INBOX, paths)
        result2 = resolve_mailbox_path(MessageBox.INBOX, paths)
        result3 = resolve_mailbox_path(MessageBox.OUTBOX, paths)
        result4 = resolve_mailbox_path(MessageBox.OUTBOX, paths)

        # Assert - Same inputs should give same outputs
        assert result1 == result2
        assert result3 == result4
        assert result1 != result3  # Different mailboxes should give different paths

    def test_resolve_mailbox_path_works_with_different_workflows(self, tmp_path):
        """Test that function works correctly with different workflow IDs."""
        # Arrange
        paths1 = MailboxPaths(workflow_id="workflow-1", base_dir=tmp_path)
        paths2 = MailboxPaths(workflow_id="workflow-2", base_dir=tmp_path)

        # Act
        inbox1 = resolve_mailbox_path(MessageBox.INBOX, paths1)
        inbox2 = resolve_mailbox_path(MessageBox.INBOX, paths2)

        # Assert - Different workflows should have different paths
        assert inbox1 != inbox2
        assert "workflow-1" in str(inbox1)
        assert "workflow-2" in str(inbox2)

    def test_resolve_mailbox_path_validates_paths_type(self, tmp_path):
        """Test that function validates paths is a MailboxPaths object."""
        # Act & Assert - Pass a dict instead of MailboxPaths
        with pytest.raises(TypeError) as exc_info:
            resolve_mailbox_path(MessageBox.INBOX, {"workflow_id": "test"})

        # Could raise TypeError or AttributeError depending on implementation
        assert exc_info.type in (TypeError, AttributeError)
