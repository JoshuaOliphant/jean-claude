# ABOUTME: Tests for MailboxDirectoryManager that ensures INBOX/OUTBOX directories exist
# ABOUTME: Consolidated test suite for mailbox directory management logic

"""Tests for MailboxDirectoryManager.

Following the project's testing patterns for directory management with
consolidated test coverage and proper fixture usage.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from jean_claude.core.mailbox_directory_manager import MailboxDirectoryManager


class TestMailboxDirectoryManager:
    """Test MailboxDirectoryManager functionality - consolidated testing."""

    def test_mailbox_directory_manager_creation(self, tmp_path):
        """Test creating MailboxDirectoryManager with workflow directory."""
        # Arrange
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        # Act
        manager = MailboxDirectoryManager(workflow_dir)

        # Assert
        assert manager.workflow_dir == workflow_dir
        assert manager.inbox_dir == workflow_dir / "INBOX"
        assert manager.outbox_dir == workflow_dir / "OUTBOX"

    def test_mailbox_directory_manager_creation_with_string_path(self, tmp_path):
        """Test creating MailboxDirectoryManager with string workflow directory."""
        # Arrange
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()

        # Act
        manager = MailboxDirectoryManager(str(workflow_dir))

        # Assert
        assert manager.workflow_dir == workflow_dir  # Should convert to Path
        assert manager.inbox_dir == workflow_dir / "INBOX"
        assert manager.outbox_dir == workflow_dir / "OUTBOX"

    def test_ensure_directories_creates_inbox_and_outbox(self, tmp_path):
        """Test that ensure_directories creates INBOX and OUTBOX directories."""
        # Arrange
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        manager = MailboxDirectoryManager(workflow_dir)

        # Verify directories don't exist initially
        assert not (workflow_dir / "INBOX").exists()
        assert not (workflow_dir / "OUTBOX").exists()

        # Act
        manager.ensure_directories()

        # Assert
        assert (workflow_dir / "INBOX").exists()
        assert (workflow_dir / "OUTBOX").exists()
        assert (workflow_dir / "INBOX").is_dir()
        assert (workflow_dir / "OUTBOX").is_dir()

    def test_ensure_directories_is_idempotent(self, tmp_path):
        """Test that ensure_directories can be called multiple times safely."""
        # Arrange
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        manager = MailboxDirectoryManager(workflow_dir)

        # Act - Call multiple times
        manager.ensure_directories()
        manager.ensure_directories()
        manager.ensure_directories()

        # Assert - Directories should still exist and be directories
        assert (workflow_dir / "INBOX").exists()
        assert (workflow_dir / "OUTBOX").exists()
        assert (workflow_dir / "INBOX").is_dir()
        assert (workflow_dir / "OUTBOX").is_dir()

    def test_ensure_directories_creates_workflow_dir_if_not_exists(self, tmp_path):
        """Test that ensure_directories creates workflow directory if it doesn't exist."""
        # Arrange
        workflow_dir = tmp_path / "nonexistent-workflow"
        assert not workflow_dir.exists()
        manager = MailboxDirectoryManager(workflow_dir)

        # Act
        manager.ensure_directories()

        # Assert
        assert workflow_dir.exists()
        assert workflow_dir.is_dir()
        assert (workflow_dir / "INBOX").exists()
        assert (workflow_dir / "OUTBOX").exists()

    def test_ensure_directories_preserves_existing_files(self, tmp_path):
        """Test that ensure_directories preserves existing files in INBOX/OUTBOX."""
        # Arrange
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        inbox_dir = workflow_dir / "INBOX"
        outbox_dir = workflow_dir / "OUTBOX"
        inbox_dir.mkdir()
        outbox_dir.mkdir()

        # Create some test files
        (inbox_dir / "message1.txt").write_text("test message 1")
        (outbox_dir / "message2.txt").write_text("test message 2")

        manager = MailboxDirectoryManager(workflow_dir)

        # Act
        manager.ensure_directories()

        # Assert
        assert (inbox_dir / "message1.txt").exists()
        assert (outbox_dir / "message2.txt").exists()
        assert (inbox_dir / "message1.txt").read_text() == "test message 1"
        assert (outbox_dir / "message2.txt").read_text() == "test message 2"

    def test_get_inbox_path_returns_correct_path(self, tmp_path):
        """Test that get_inbox_path returns the INBOX directory path."""
        # Arrange
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        manager = MailboxDirectoryManager(workflow_dir)

        # Act
        inbox_path = manager.get_inbox_path()

        # Assert
        assert inbox_path == workflow_dir / "INBOX"
        assert isinstance(inbox_path, Path)

    def test_get_outbox_path_returns_correct_path(self, tmp_path):
        """Test that get_outbox_path returns the OUTBOX directory path."""
        # Arrange
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        manager = MailboxDirectoryManager(workflow_dir)

        # Act
        outbox_path = manager.get_outbox_path()

        # Assert
        assert outbox_path == workflow_dir / "OUTBOX"
        assert isinstance(outbox_path, Path)

    def test_mailbox_directory_manager_with_invalid_workflow_dir_raises_error(self, tmp_path):
        """Test that invalid workflow directory raises appropriate error."""
        # Arrange - Create a file instead of directory
        invalid_path = tmp_path / "not_a_directory.txt"
        invalid_path.write_text("this is a file")

        # Act & Assert
        with pytest.raises((ValueError, TypeError, OSError)):
            manager = MailboxDirectoryManager(invalid_path)
            manager.ensure_directories()

    def test_str_representation(self, tmp_path):
        """Test string representation of MailboxDirectoryManager."""
        # Arrange
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        manager = MailboxDirectoryManager(workflow_dir)

        # Act
        str_repr = str(manager)

        # Assert
        assert "MailboxDirectoryManager" in str_repr
        assert str(workflow_dir) in str_repr

    def test_repr_representation(self, tmp_path):
        """Test repr representation of MailboxDirectoryManager."""
        # Arrange
        workflow_dir = tmp_path / "test-workflow"
        workflow_dir.mkdir()
        manager = MailboxDirectoryManager(workflow_dir)

        # Act
        repr_str = repr(manager)

        # Assert
        assert "MailboxDirectoryManager" in repr_str
        assert str(workflow_dir) in repr_str

    def test_manager_integration_workflow(self, tmp_path):
        """Test complete workflow from creation to directory management."""
        # Arrange
        workflow_id = "integration-test-workflow"
        workflow_dir = tmp_path / workflow_id

        # Act - Full workflow
        manager = MailboxDirectoryManager(workflow_dir)
        manager.ensure_directories()

        inbox_path = manager.get_inbox_path()
        outbox_path = manager.get_outbox_path()

        # Create test files
        test_inbox_file = inbox_path / "test_message.txt"
        test_outbox_file = outbox_path / "test_response.txt"
        test_inbox_file.write_text("incoming message")
        test_outbox_file.write_text("outgoing response")

        # Assert - Everything should work end-to-end
        assert workflow_dir.exists()
        assert inbox_path.exists() and inbox_path.is_dir()
        assert outbox_path.exists() and outbox_path.is_dir()
        assert test_inbox_file.exists()
        assert test_outbox_file.exists()
        assert test_inbox_file.read_text() == "incoming message"
        assert test_outbox_file.read_text() == "outgoing response"

        # Act - Call ensure_directories again to test idempotency
        manager.ensure_directories()

        # Assert - Files should still exist
        assert test_inbox_file.read_text() == "incoming message"
        assert test_outbox_file.read_text() == "outgoing response"


class TestMailboxDirectoryManagerErrorHandling:
    """Test error handling scenarios for MailboxDirectoryManager."""

    def test_creation_with_none_raises_error(self):
        """Test that creating MailboxDirectoryManager with None raises error."""
        with pytest.raises((TypeError, ValueError)):
            MailboxDirectoryManager(None)

    def test_creation_with_empty_string_raises_error(self):
        """Test that creating MailboxDirectoryManager with empty string raises error."""
        with pytest.raises((TypeError, ValueError)):
            MailboxDirectoryManager("")

    @patch('pathlib.Path.mkdir')
    def test_ensure_directories_handles_permission_error(self, mock_mkdir, tmp_path):
        """Test that ensure_directories handles permission errors gracefully."""
        # Arrange
        workflow_dir = tmp_path / "test-workflow"
        manager = MailboxDirectoryManager(workflow_dir)
        mock_mkdir.side_effect = PermissionError("Permission denied")

        # Act & Assert
        with pytest.raises(PermissionError):
            manager.ensure_directories()

    @patch('pathlib.Path.mkdir')
    def test_ensure_directories_handles_os_error(self, mock_mkdir, tmp_path):
        """Test that ensure_directories handles OS errors gracefully."""
        # Arrange
        workflow_dir = tmp_path / "test-workflow"
        manager = MailboxDirectoryManager(workflow_dir)
        mock_mkdir.side_effect = OSError("Disk full")

        # Act & Assert
        with pytest.raises(OSError):
            manager.ensure_directories()