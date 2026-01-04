# ABOUTME: Test suite for EventStore.get_snapshot() method functionality
# ABOUTME: Tests snapshot retrieval with latest snapshot logic, None handling, and multiple snapshot scenarios

"""Test suite for EventStore.get_snapshot() method functionality.

This module comprehensively tests the EventStore.get_snapshot() method, including:

- Latest snapshot retrieval for a workflow
- Return None when no snapshot exists for a workflow
- Handle multiple snapshots properly (return only latest)
- Snapshot object reconstruction from database rows
- Error handling for database and connection issues
- Input validation for workflow_id parameter
- Integration with existing database schema and Snapshot model
- Database connection management during retrieval operations

The tests follow TDD principles and use existing fixtures to ensure consistency
with the overall test suite.
"""

import sqlite3
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
import pytest

from jean_claude.core.event_store import EventStore
from jean_claude.core.event_models import Snapshot


class TestGetSnapshotBasicFunctionality:
    """Test basic functionality of EventStore.get_snapshot() method."""

    def test_get_snapshot_returns_latest_snapshot_success(self, tmp_path):
        """Test that get_snapshot() returns the latest snapshot for a workflow."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create and save a snapshot first
        snapshot = Snapshot(
            workflow_id="test-workflow-123",
            snapshot_data={"current_state": "active", "task_count": 5},
            event_sequence_number=100
        )
        assert event_store.save_snapshot(snapshot) is True

        # Retrieve the snapshot
        retrieved_snapshot = event_store.get_snapshot("test-workflow-123")

        # Verify we got a Snapshot object back
        assert retrieved_snapshot is not None
        assert isinstance(retrieved_snapshot, Snapshot)
        assert retrieved_snapshot.workflow_id == "test-workflow-123"
        assert retrieved_snapshot.snapshot_data["current_state"] == "active"
        assert retrieved_snapshot.snapshot_data["task_count"] == 5
        assert retrieved_snapshot.event_sequence_number == 100

    def test_get_snapshot_returns_none_when_no_snapshot_exists(self, tmp_path):
        """Test that get_snapshot() returns None when no snapshot exists for a workflow."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Try to retrieve a snapshot for a workflow that has no snapshots
        result = event_store.get_snapshot("nonexistent-workflow")

        # Should return None
        assert result is None

    def test_get_snapshot_returns_none_for_empty_database(self, tmp_path):
        """Test that get_snapshot() returns None when database is empty."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Database exists but has no data
        result = event_store.get_snapshot("any-workflow-id")

        # Should return None
        assert result is None

    def test_get_snapshot_handles_multiple_snapshots_returns_latest(self, tmp_path):
        """Test that get_snapshot() returns the latest snapshot when multiple snapshots exist."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create first snapshot
        snapshot1 = Snapshot(
            workflow_id="workflow-with-multiple",
            snapshot_data={"state": "initial", "count": 50},
            event_sequence_number=50
        )
        assert event_store.save_snapshot(snapshot1) is True

        # Wait a moment to ensure different timestamps
        import time
        time.sleep(0.01)

        # Create second snapshot (should replace first due to primary key)
        snapshot2 = Snapshot(
            workflow_id="workflow-with-multiple",
            snapshot_data={"state": "updated", "count": 100},
            event_sequence_number=100
        )
        assert event_store.save_snapshot(snapshot2) is True

        # Retrieve snapshot - should get the latest (second) one
        retrieved = event_store.get_snapshot("workflow-with-multiple")

        assert retrieved is not None
        assert retrieved.snapshot_data["state"] == "updated"
        assert retrieved.snapshot_data["count"] == 100
        assert retrieved.event_sequence_number == 100

    def test_get_snapshot_preserves_complex_snapshot_data(self, tmp_path):
        """Test that get_snapshot() properly reconstructs complex snapshot data."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create snapshot with complex nested data
        complex_data = {
            "nested": {"deep": {"data": ["list", "items"]}},
            "numbers": [1, 2, 3.14, -5],
            "boolean": True,
            "null_value": None,
            "status": "complex_test"
        }

        snapshot = Snapshot(
            workflow_id="complex-data-test",
            snapshot_data=complex_data,
            event_sequence_number=999
        )
        assert event_store.save_snapshot(snapshot) is True

        # Retrieve and verify complex data is preserved
        retrieved = event_store.get_snapshot("complex-data-test")

        assert retrieved is not None
        assert retrieved.snapshot_data == complex_data  # Exact match
        assert retrieved.snapshot_data["nested"]["deep"]["data"] == ["list", "items"]
        assert retrieved.snapshot_data["numbers"] == [1, 2, 3.14, -5]
        assert retrieved.snapshot_data["boolean"] is True
        assert retrieved.snapshot_data["null_value"] is None


class TestGetSnapshotValidation:
    """Test input validation and parameter handling in get_snapshot() method."""

    def test_get_snapshot_validates_workflow_id_parameter(self, tmp_path):
        """Test that get_snapshot() validates the workflow_id parameter."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Test None workflow_id
        with pytest.raises(ValueError, match="workflow_id cannot be None"):
            event_store.get_snapshot(None)

        # Test empty string workflow_id
        with pytest.raises(ValueError, match="workflow_id cannot be empty or whitespace-only"):
            event_store.get_snapshot("")

        # Test whitespace-only workflow_id
        with pytest.raises(ValueError, match="workflow_id cannot be empty or whitespace-only"):
            event_store.get_snapshot("   ")

        # Test non-string workflow_id
        with pytest.raises(TypeError, match="workflow_id must be a string"):
            event_store.get_snapshot(123)

    def test_get_snapshot_handles_workflow_id_with_whitespace(self, tmp_path):
        """Test that get_snapshot() properly handles workflow_id with leading/trailing whitespace."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Save snapshot with clean workflow_id
        snapshot = Snapshot(
            workflow_id="test-workflow",
            snapshot_data={"clean": "id"},
            event_sequence_number=1
        )
        assert event_store.save_snapshot(snapshot) is True

        # Retrieve with whitespace in workflow_id - should find the snapshot
        retrieved = event_store.get_snapshot("  test-workflow  ")

        assert retrieved is not None
        assert retrieved.workflow_id == "test-workflow"
        assert retrieved.snapshot_data["clean"] == "id"


class TestGetSnapshotErrorHandling:
    """Test error handling and edge cases in get_snapshot() method."""

    def test_get_snapshot_handles_database_connection_error(self, tmp_path):
        """Test that get_snapshot() handles database connection errors gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Mock get_connection to raise an error
        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = sqlite3.Error("Connection failed")

            # Should raise sqlite3.Error with context
            with pytest.raises(sqlite3.Error, match="Failed to retrieve snapshot from database"):
                event_store.get_snapshot("test-workflow")

    def test_get_snapshot_handles_sql_execution_error(self, tmp_path):
        """Test that get_snapshot() handles SQL execution errors gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Mock connection to simulate SQL execution error
        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_conn = Mock(spec=sqlite3.Connection)
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value = mock_conn

            # Simulate SQL execution error
            mock_cursor.execute.side_effect = sqlite3.DatabaseError("SQL execution failed")

            # Should raise sqlite3.Error with context
            with pytest.raises(sqlite3.Error, match="Failed to retrieve snapshot from database"):
                event_store.get_snapshot("test-workflow")

    def test_get_snapshot_handles_json_deserialization_error(self, tmp_path):
        """Test that get_snapshot() handles corrupted JSON data gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Manually insert corrupted JSON data into database
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO snapshots (workflow_id, sequence_number, state, created_at)
                VALUES (?, ?, ?, ?)
            """, ("corrupted-json-workflow", 1, "invalid json {", datetime.now().isoformat()))

        # Should return None when JSON is corrupted (graceful degradation)
        result = event_store.get_snapshot("corrupted-json-workflow")
        assert result is None

    def test_get_snapshot_resource_cleanup_on_error(self, tmp_path):
        """Test that get_snapshot() properly closes connections even when errors occur."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Mock connection and close_connection to track cleanup
        with patch.object(event_store, 'get_connection') as mock_get_conn, \
             patch.object(event_store, 'close_connection') as mock_close_conn:
            mock_conn = Mock(spec=sqlite3.Connection)
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value = mock_conn

            # Simulate an error during execution
            mock_cursor.execute.side_effect = sqlite3.Error("Database error")

            # Should raise error but still clean up connection
            with pytest.raises(sqlite3.Error):
                event_store.get_snapshot("test-workflow")

            # Verify connection cleanup was called
            mock_close_conn.assert_called_with(mock_conn)


class TestGetSnapshotIntegration:
    """Test integration of get_snapshot() with existing database schema and operations."""

    def test_get_snapshot_integrates_with_save_snapshot(self, tmp_path):
        """Test that get_snapshot() properly integrates with save_snapshot() operations."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Save multiple snapshots for different workflows
        snapshot1 = Snapshot(
            workflow_id="workflow-1",
            snapshot_data={"integration": "test1"},
            event_sequence_number=10
        )
        snapshot2 = Snapshot(
            workflow_id="workflow-2",
            snapshot_data={"integration": "test2"},
            event_sequence_number=20
        )

        assert event_store.save_snapshot(snapshot1) is True
        assert event_store.save_snapshot(snapshot2) is True

        # Retrieve both snapshots
        retrieved1 = event_store.get_snapshot("workflow-1")
        retrieved2 = event_store.get_snapshot("workflow-2")

        # Verify both snapshots are properly retrieved and isolated
        assert retrieved1 is not None
        assert retrieved1.workflow_id == "workflow-1"
        assert retrieved1.snapshot_data["integration"] == "test1"
        assert retrieved1.event_sequence_number == 10

        assert retrieved2 is not None
        assert retrieved2.workflow_id == "workflow-2"
        assert retrieved2.snapshot_data["integration"] == "test2"
        assert retrieved2.event_sequence_number == 20

    def test_get_snapshot_works_with_database_schema(self, tmp_path):
        """Test that get_snapshot() correctly uses the actual database schema column names."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Verify the database schema exists correctly
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(snapshots)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type mapping

            # Verify expected schema columns
            assert "workflow_id" in columns
            assert "sequence_number" in columns
            assert "state" in columns
            assert "created_at" in columns

        # Save and retrieve snapshot using the schema
        snapshot = Snapshot(
            workflow_id="schema-test",
            snapshot_data={"schema": "verification"},
            event_sequence_number=42
        )
        assert event_store.save_snapshot(snapshot) is True

        retrieved = event_store.get_snapshot("schema-test")
        assert retrieved is not None
        assert retrieved.workflow_id == "schema-test"
        assert retrieved.snapshot_data["schema"] == "verification"
        assert retrieved.event_sequence_number == 42

    def test_get_snapshot_handles_concurrent_workflows(self, tmp_path):
        """Test that get_snapshot() correctly isolates snapshots for different workflows."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create snapshots for multiple workflows with similar data but different IDs
        workflows = [f"workflow-{i}" for i in range(5)]

        for i, workflow_id in enumerate(workflows):
            snapshot = Snapshot(
                workflow_id=workflow_id,
                snapshot_data={"index": i, "workflow": workflow_id},
                event_sequence_number=i * 10
            )
            assert event_store.save_snapshot(snapshot) is True

        # Verify each workflow gets its own snapshot
        for i, workflow_id in enumerate(workflows):
            retrieved = event_store.get_snapshot(workflow_id)
            assert retrieved is not None
            assert retrieved.workflow_id == workflow_id
            assert retrieved.snapshot_data["index"] == i
            assert retrieved.snapshot_data["workflow"] == workflow_id
            assert retrieved.event_sequence_number == i * 10

        # Verify non-existent workflow returns None
        assert event_store.get_snapshot("workflow-999") is None