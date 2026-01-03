# ABOUTME: Test error handling for EventStore operations including invalid data,
# ABOUTME: database connection failures, and transaction conflicts

"""Test comprehensive error handling for EventStore operations.

This module tests error handling for:
- Invalid event data validation
- Database connection failures
- Transaction conflicts
- Proper exception types and error messages
"""

import pytest
import sqlite3
from pathlib import Path
from unittest.mock import patch, Mock
from jean_claude.core.event_store import EventStore
from jean_claude.core.event_models import Event, Snapshot


class TestEventDataValidation:
    """Test validation of event data."""

    def test_append_with_none_event(self, tmp_path):
        """Test that appending None event returns False."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        result = event_store.append(None)
        assert result is False

    def test_append_with_invalid_event_type(self, tmp_path):
        """Test that appending non-Event object returns False."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        result = event_store.append("not an event")
        assert result is False

        result = event_store.append({"workflow_id": "test"})
        assert result is False

    def test_get_events_with_none_workflow_id(self, tmp_path):
        """Test that get_events raises ValueError for None workflow_id."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with pytest.raises(ValueError, match="workflow_id cannot be None"):
            event_store.get_events(None)

    def test_get_events_with_empty_workflow_id(self, tmp_path):
        """Test that get_events raises ValueError for empty workflow_id."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with pytest.raises(ValueError, match="workflow_id cannot be empty"):
            event_store.get_events("")

        with pytest.raises(ValueError, match="workflow_id cannot be empty"):
            event_store.get_events("   ")

    def test_get_events_with_empty_event_type(self, tmp_path):
        """Test that get_events raises ValueError for empty event_type."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with pytest.raises(ValueError, match="event_type cannot be empty"):
            event_store.get_events("workflow-123", event_type="")

        with pytest.raises(ValueError, match="event_type cannot be empty"):
            event_store.get_events("workflow-123", event_type="   ")

    def test_get_events_with_invalid_order_by(self, tmp_path):
        """Test that get_events raises ValueError for invalid order_by."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with pytest.raises(ValueError, match="order_by must be 'asc' or 'desc'"):
            event_store.get_events("workflow-123", order_by="invalid")

        with pytest.raises(ValueError, match="order_by must be 'asc' or 'desc'"):
            event_store.get_events("workflow-123", order_by="ascending")


class TestDatabaseConnectionErrors:
    """Test handling of database connection failures."""

    def test_append_handles_database_error(self, tmp_path):
        """Test that append handles database errors gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        event = Event(
            workflow_id="test-workflow",
            event_type="test.event",
            event_data={"key": "value"}
        )

        # Mock get_connection to raise database error
        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = sqlite3.OperationalError("Database locked")

            result = event_store.append(event)
            assert result is False

    def test_get_events_handles_database_error(self, tmp_path):
        """Test that get_events raises error with context on database failure."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = sqlite3.OperationalError("Database corrupted")

            with pytest.raises(sqlite3.Error, match="Failed to query events"):
                event_store.get_events("workflow-123")

    def test_save_snapshot_handles_database_error(self, tmp_path):
        """Test that save_snapshot returns False on database error."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        snapshot = Snapshot(
            workflow_id="test-workflow",
            snapshot_data={"state": "test"},
            event_sequence_number=10
        )

        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = sqlite3.Error("Connection failed")

            result = event_store.save_snapshot(snapshot)
            assert result is False

    def test_get_snapshot_handles_database_error(self, tmp_path):
        """Test that get_snapshot raises error with context on database failure."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = sqlite3.Error("Read error")

            with pytest.raises(sqlite3.Error, match="Failed to retrieve snapshot"):
                event_store.get_snapshot("workflow-123")


class TestTransactionConflicts:
    """Test handling of transaction conflicts and rollback."""

    def test_append_rolls_back_on_commit_failure(self, tmp_path):
        """Test that append rolls back transaction on commit failure."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        event = Event(
            workflow_id="test-workflow",
            event_type="test.event",
            event_data={"key": "value"}
        )

        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_conn = Mock()
            mock_conn.cursor.return_value = Mock()
            mock_conn.commit.side_effect = sqlite3.OperationalError("Commit failed")
            mock_get_conn.return_value = mock_conn

            result = event_store.append(event)
            assert result is False

            # Verify rollback was called
            mock_conn.rollback.assert_called_once()

    def test_append_handles_rollback_failure(self, tmp_path):
        """Test that append handles rollback failures gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        event = Event(
            workflow_id="test-workflow",
            event_type="test.event",
            event_data={"key": "value"}
        )

        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_conn = Mock()
            mock_conn.cursor.return_value = Mock()
            mock_conn.commit.side_effect = sqlite3.Error("Commit failed")
            mock_conn.rollback.side_effect = sqlite3.Error("Rollback also failed")
            mock_get_conn.return_value = mock_conn

            # Should still return False and close connection
            result = event_store.append(event)
            assert result is False

            mock_conn.close.assert_called()

    def test_save_snapshot_rolls_back_on_error(self, tmp_path):
        """Test that save_snapshot rolls back on commit failure."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        snapshot = Snapshot(
            workflow_id="test-workflow",
            snapshot_data={"state": "test"},
            event_sequence_number=10
        )

        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_conn = Mock()
            mock_conn.cursor.return_value = Mock()
            mock_conn.commit.side_effect = sqlite3.IntegrityError("Constraint violation")
            mock_get_conn.return_value = mock_conn

            result = event_store.save_snapshot(snapshot)
            assert result is False

            mock_conn.rollback.assert_called_once()


class TestErrorMessages:
    """Test that error messages are clear and informative."""

    def test_get_events_error_includes_context(self, tmp_path):
        """Test that get_events error message includes database path."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = sqlite3.Error("Test error")

            with pytest.raises(sqlite3.Error) as exc_info:
                event_store.get_events("workflow-123")

            # Error message should include database path
            assert str(db_path) in str(exc_info.value)
            assert "Failed to query events" in str(exc_info.value)

    def test_get_snapshot_error_includes_database_path(self, tmp_path):
        """Test that get_snapshot error includes database path."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = sqlite3.Error("Test error")

            with pytest.raises(sqlite3.Error) as exc_info:
                event_store.get_snapshot("workflow-abc")

            assert str(db_path) in str(exc_info.value)
            assert "Failed to retrieve snapshot" in str(exc_info.value)

    def test_rebuild_projection_error_includes_workflow_id(self, tmp_path):
        """Test that rebuild_projection error includes workflow_id."""
        from jean_claude.core.projection_builder import ProjectionBuilder

        class TestBuilder(ProjectionBuilder):
            def get_initial_state(self):
                return {}

            def apply_workflow_started(self, state, event):
                return state

            def apply_workflow_completed(self, state, event):
                return state

            def apply_workflow_failed(self, state, event):
                return state

            def apply_worktree_created(self, state, event):
                return state

            def apply_feature_planned(self, state, event):
                return state

            def apply_feature_started(self, state, event):
                return state

            def apply_feature_completed(self, state, event):
                return state

            def apply_feature_failed(self, state, event):
                return state

            def apply_phase_changed(self, state, event):
                return state

            def apply_worktree_active(self, state, event):
                return state

            def apply_worktree_merged(self, state, event):
                return state

            def apply_worktree_deleted(self, state, event):
                return state

            def apply_tests_started(self, state, event):
                return state

            def apply_tests_passed(self, state, event):
                return state

            def apply_tests_failed(self, state, event):
                return state

            def apply_commit_created(self, state, event):
                return state

            def apply_commit_failed(self, state, event):
                return state

        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)
        builder = TestBuilder()

        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = sqlite3.Error("Test error")

            with pytest.raises(sqlite3.Error) as exc_info:
                event_store.rebuild_projection("workflow-xyz", builder)

            assert "workflow-xyz" in str(exc_info.value)
            assert "Failed to rebuild projection" in str(exc_info.value)
