# ABOUTME: Test error handling for EventStore operations including invalid data,
# ABOUTME: database connection failures, and transaction conflicts

"""Test comprehensive error handling for EventStore operations.

Tests validation, database errors, transaction rollback,
and informative error messages.
"""

import pytest
import sqlite3
from unittest.mock import patch, Mock
from jean_claude.core.event_store import EventStore
from jean_claude.core.event_models import Event, Snapshot


class TestEventDataValidation:
    """Test validation of event data and query parameters."""

    def test_append_rejects_invalid_input(self, tmp_path):
        """Test append returns False for None, non-Event, and dict."""
        event_store = EventStore(tmp_path / "test.db")
        assert event_store.append(None) is False
        assert event_store.append("not an event") is False
        assert event_store.append({"workflow_id": "test"}) is False

    def test_get_events_validates_parameters(self, tmp_path):
        """Test get_events validates workflow_id, event_type, and order_by."""
        event_store = EventStore(tmp_path / "test.db")

        with pytest.raises(ValueError, match="workflow_id cannot be None"):
            event_store.get_events(None)
        for invalid in ["", "   "]:
            with pytest.raises(ValueError, match="workflow_id cannot be empty"):
                event_store.get_events(invalid)
        for invalid in ["", "   "]:
            with pytest.raises(ValueError, match="event_type cannot be empty"):
                event_store.get_events("w-123", event_type=invalid)
        for invalid in ["invalid", "ascending"]:
            with pytest.raises(ValueError, match="order_by must be 'asc' or 'desc'"):
                event_store.get_events("w-123", order_by=invalid)


class TestDatabaseConnectionErrors:
    """Test handling of database connection failures."""

    def test_operations_handle_database_errors(self, tmp_path):
        """Test append, get_events, save_snapshot, get_snapshot handle DB errors."""
        event_store = EventStore(tmp_path / "test.db")
        event = Event(workflow_id="w", event_type="test", event_data={"k": "v"})
        snapshot = Snapshot(workflow_id="w", snapshot_data={"state": "test"}, event_sequence_number=10)

        with patch.object(event_store, 'get_connection', side_effect=sqlite3.OperationalError("DB locked")):
            assert event_store.append(event) is False

        with patch.object(event_store, 'get_connection', side_effect=sqlite3.OperationalError("DB corrupted")):
            with pytest.raises(sqlite3.Error, match="Failed to query events"):
                event_store.get_events("w-123")

        with patch.object(event_store, 'get_connection', side_effect=sqlite3.Error("Connection failed")):
            assert event_store.save_snapshot(snapshot) is False

        with patch.object(event_store, 'get_connection', side_effect=sqlite3.Error("Read error")):
            with pytest.raises(sqlite3.Error, match="Failed to retrieve snapshot"):
                event_store.get_snapshot("w-123")


class TestTransactionConflicts:
    """Test handling of transaction conflicts and rollback."""

    def test_append_rolls_back_on_commit_failure(self, tmp_path):
        """Test append rolls back on commit failure and handles rollback failure."""
        event_store = EventStore(tmp_path / "test.db")
        event = Event(workflow_id="w", event_type="test", event_data={"k": "v"})

        # Normal rollback
        with patch.object(event_store, 'get_connection') as mock_get:
            mock_conn = Mock()
            mock_conn.cursor.return_value = Mock()
            mock_conn.commit.side_effect = sqlite3.OperationalError("Commit failed")
            mock_get.return_value = mock_conn

            assert event_store.append(event) is False
            mock_conn.rollback.assert_called_once()

        # Rollback also fails
        with patch.object(event_store, 'get_connection') as mock_get:
            mock_conn = Mock()
            mock_conn.cursor.return_value = Mock()
            mock_conn.commit.side_effect = sqlite3.Error("Commit failed")
            mock_conn.rollback.side_effect = sqlite3.Error("Rollback failed")
            mock_get.return_value = mock_conn

            assert event_store.append(event) is False
            mock_conn.close.assert_called()

    def test_save_snapshot_rolls_back_on_error(self, tmp_path):
        """Test save_snapshot rolls back on commit failure."""
        event_store = EventStore(tmp_path / "test.db")
        snapshot = Snapshot(workflow_id="w", snapshot_data={"state": "test"}, event_sequence_number=10)

        with patch.object(event_store, 'get_connection') as mock_get:
            mock_conn = Mock()
            mock_conn.cursor.return_value = Mock()
            mock_conn.commit.side_effect = sqlite3.IntegrityError("Constraint violation")
            mock_get.return_value = mock_conn

            assert event_store.save_snapshot(snapshot) is False
            mock_conn.rollback.assert_called_once()


class TestErrorMessages:
    """Test that error messages include useful context."""

    def test_error_messages_include_database_path_and_context(self, tmp_path):
        """Test errors include database path for get_events, get_snapshot, and rebuild_projection."""
        from jean_claude.core.projection_builder import ProjectionBuilder

        class StubBuilder(ProjectionBuilder):
            def get_initial_state(self): return {}
            def apply_workflow_started(self, s, e): return s
            def apply_workflow_completed(self, s, e): return s
            def apply_workflow_failed(self, s, e): return s
            def apply_worktree_created(self, s, e): return s
            def apply_worktree_active(self, s, e): return s
            def apply_worktree_merged(self, s, e): return s
            def apply_worktree_deleted(self, s, e): return s
            def apply_feature_planned(self, s, e): return s
            def apply_feature_started(self, s, e): return s
            def apply_feature_completed(self, s, e): return s
            def apply_feature_failed(self, s, e): return s
            def apply_phase_changed(self, s, e): return s
            def apply_tests_started(self, s, e): return s
            def apply_tests_passed(self, s, e): return s
            def apply_tests_failed(self, s, e): return s
            def apply_commit_created(self, s, e): return s
            def apply_commit_failed(self, s, e): return s

        db_path = tmp_path / "test.db"
        event_store = EventStore(db_path)

        for method, args, expected in [
            (event_store.get_events, ("w-123",), "Failed to query events"),
            (event_store.get_snapshot, ("w-abc",), "Failed to retrieve snapshot"),
            (event_store.rebuild_projection, ("w-xyz", StubBuilder()), "Failed to rebuild projection"),
        ]:
            with patch.object(event_store, 'get_connection', side_effect=sqlite3.Error("Test")):
                with pytest.raises(sqlite3.Error) as exc_info:
                    method(*args)
                assert expected in str(exc_info.value)
                assert str(db_path) in str(exc_info.value) or args[0] in str(exc_info.value)
