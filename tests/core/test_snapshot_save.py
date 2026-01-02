# ABOUTME: Test suite for EventStore.save_snapshot() method functionality
# ABOUTME: Tests snapshot creation in snapshots table with workflow_id, data serialization, and event_count tracking

"""Test suite for EventStore.save_snapshot() method functionality.

This module comprehensively tests the EventStore.save_snapshot() method, including:

- Snapshot creation in the snapshots table
- Workflow_id tracking and validation
- Snapshot_data serialization to JSON
- Event_count tracking with sequence_number
- ACID transaction handling with automatic commit/rollback
- Error handling with proper transaction rollback on failures
- Data validation and serialization
- Database connection management during save operations
- Integration with existing database schema and Snapshot model

The tests follow TDD principles and use existing fixtures to ensure consistency
with the overall test suite.
"""

import sqlite3
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime
import pytest

from jean_claude.core.event_store import EventStore
from jean_claude.core.event_models import Snapshot


class TestSaveSnapshotBasicFunctionality:
    """Test basic functionality of EventStore.save_snapshot() method."""

    def test_save_snapshot_success(self, tmp_path):
        """Test that save_snapshot() successfully writes a snapshot to the database."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create a snapshot to save
        snapshot = Snapshot(
            workflow_id="test-workflow-123",
            snapshot_data={"current_state": "active", "task_count": 5},
            event_sequence_number=100
        )

        # Save the snapshot
        result = event_store.save_snapshot(snapshot)

        # Verify return value indicates success
        assert result is True

        # Verify snapshot was written to database using actual schema columns
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM snapshots WHERE workflow_id = ?", ("test-workflow-123",))
            row = cursor.fetchone()

            assert row is not None
            assert row["workflow_id"] == "test-workflow-123"
            assert row["sequence_number"] == 100
            # Parse JSON data back to dict for verification (schema uses 'state' column)
            state_data = json.loads(row["state"])
            assert state_data["current_state"] == "active"
            assert state_data["task_count"] == 5
            assert row["created_at"] is not None

    def test_save_snapshot_with_proper_timestamp(self, tmp_path):
        """Test that save_snapshot() generates proper timestamp when saving to database."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        snapshot = Snapshot(
            workflow_id="test-workflow-456",
            snapshot_data={"status": "completed", "results": ["task1", "task2"]},
            event_sequence_number=150
        )

        # Save the snapshot
        event_store.save_snapshot(snapshot)

        # Verify timestamp was generated and stored
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT created_at FROM snapshots WHERE workflow_id = ?", ("test-workflow-456",))
            row = cursor.fetchone()

            # Should have a valid ISO timestamp
            assert row["created_at"] is not None
            # Verify it's a valid datetime string
            datetime.fromisoformat(row["created_at"])

    def test_save_snapshot_replaces_existing_snapshot(self, tmp_path):
        """Test that save_snapshot() replaces existing snapshots for the same workflow_id."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create first snapshot
        snapshot1 = Snapshot(
            workflow_id="workflow-replacement",
            snapshot_data={"state": "initial", "count": 50},
            event_sequence_number=50
        )

        # Create second snapshot for same workflow
        snapshot2 = Snapshot(
            workflow_id="workflow-replacement",
            snapshot_data={"state": "updated", "count": 100},
            event_sequence_number=100
        )

        # Save first snapshot
        assert event_store.save_snapshot(snapshot1) is True

        # Save second snapshot - should replace first
        assert event_store.save_snapshot(snapshot2) is True

        # Verify only the latest snapshot exists
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM snapshots WHERE workflow_id = ?", ("workflow-replacement",))
            count = cursor.fetchone()["count"]
            assert count == 1

            # Verify it's the second snapshot
            cursor.execute("SELECT * FROM snapshots WHERE workflow_id = ?", ("workflow-replacement",))
            row = cursor.fetchone()
            state_data = json.loads(row["state"])
            assert state_data["state"] == "updated"
            assert state_data["count"] == 100
            assert row["sequence_number"] == 100

    def test_save_multiple_snapshots_different_workflows(self, tmp_path):
        """Test that save_snapshot() handles multiple snapshots for different workflows."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create snapshots for different workflows
        snapshot1 = Snapshot(
            workflow_id="workflow-1",
            snapshot_data={"state": "active", "data": "workflow1"},
            event_sequence_number=75
        )
        snapshot2 = Snapshot(
            workflow_id="workflow-2",
            snapshot_data={"state": "completed", "data": "workflow2"},
            event_sequence_number=200
        )

        # Save both snapshots
        assert event_store.save_snapshot(snapshot1) is True
        assert event_store.save_snapshot(snapshot2) is True

        # Verify both snapshots exist
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM snapshots")
            total_count = cursor.fetchone()["count"]
            assert total_count == 2

            # Verify each workflow has its own snapshot
            cursor.execute("SELECT * FROM snapshots WHERE workflow_id = ?", ("workflow-1",))
            row1 = cursor.fetchone()
            state1 = json.loads(row1["state"])
            assert state1["data"] == "workflow1"
            assert row1["sequence_number"] == 75

            cursor.execute("SELECT * FROM snapshots WHERE workflow_id = ?", ("workflow-2",))
            row2 = cursor.fetchone()
            state2 = json.loads(row2["state"])
            assert state2["data"] == "workflow2"
            assert row2["sequence_number"] == 200


class TestSaveSnapshotTransactions:
    """Test ACID transaction handling in EventStore.save_snapshot() method."""

    def test_save_snapshot_uses_transaction_commit_on_success(self, tmp_path):
        """Test that save_snapshot() uses transactions and commits on success."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        snapshot = Snapshot(
            workflow_id="transaction-test",
            snapshot_data={"committed": True},
            event_sequence_number=42
        )

        # Mock connection to track transaction calls
        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_conn = Mock(spec=sqlite3.Connection)
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value = mock_conn

            # Save should succeed
            result = event_store.save_snapshot(snapshot)
            assert result is True

            # Verify transaction handling
            mock_conn.commit.assert_called_once()
            mock_conn.rollback.assert_not_called()
            mock_conn.close.assert_called_once()

    def test_save_snapshot_rollback_on_database_error(self, tmp_path):
        """Test that save_snapshot() rolls back transaction on database errors."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        snapshot = Snapshot(
            workflow_id="rollback-test",
            snapshot_data={"will_fail": True},
            event_sequence_number=99
        )

        # Mock connection to simulate database error during insert
        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_conn = Mock(spec=sqlite3.Connection)
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value = mock_conn

            # Simulate database error on execute
            mock_cursor.execute.side_effect = sqlite3.DatabaseError("Simulated database error")

            # Save should fail and return False
            result = event_store.save_snapshot(snapshot)
            assert result is False

            # Verify transaction was rolled back
            mock_conn.rollback.assert_called_once()
            mock_conn.commit.assert_not_called()
            mock_conn.close.assert_called_once()

    def test_save_snapshot_rollback_on_connection_error(self, tmp_path):
        """Test that save_snapshot() handles connection errors gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        snapshot = Snapshot(
            workflow_id="connection-error-test",
            snapshot_data={"connection": "failed"},
            event_sequence_number=1
        )

        # Mock get_connection to raise an error
        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = sqlite3.Error("Connection failed")

            # Save should fail gracefully
            result = event_store.save_snapshot(snapshot)
            assert result is False


class TestSaveSnapshotValidation:
    """Test snapshot validation and error handling in save_snapshot() method."""

    def test_save_snapshot_validates_snapshot_parameter(self, tmp_path):
        """Test that save_snapshot() validates the snapshot parameter."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Test None snapshot
        result = event_store.save_snapshot(None)
        assert result is False

        # Test non-Snapshot object
        result = event_store.save_snapshot({"not": "a_snapshot"})
        assert result is False

        # Test string instead of Snapshot
        result = event_store.save_snapshot("invalid_snapshot")
        assert result is False

    def test_save_snapshot_validates_required_snapshot_fields(self, tmp_path):
        """Test that save_snapshot() validates required snapshot fields before database insert."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create snapshot with missing required fields (this should be caught by Snapshot model validation)
        with pytest.raises(ValueError, match="workflow_id cannot be None or empty"):
            Snapshot(
                workflow_id="",  # Empty workflow_id should fail validation
                snapshot_data={"test": "data"},
                event_sequence_number=10
            )

        with pytest.raises(ValueError, match="snapshot_data cannot be None"):
            Snapshot(
                workflow_id="test-workflow",
                snapshot_data=None,  # None snapshot_data should fail validation
                event_sequence_number=10
            )

        with pytest.raises(ValueError, match="event_sequence_number must be non-negative"):
            Snapshot(
                workflow_id="test-workflow",
                snapshot_data={"test": "data"},
                event_sequence_number=-5  # Negative sequence number should fail validation
            )

    def test_save_snapshot_handles_json_serialization_error(self, tmp_path):
        """Test that save_snapshot() handles JSON serialization errors in snapshot_data."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create snapshot with non-serializable data
        snapshot = Snapshot(
            workflow_id="json-error-test",
            snapshot_data={"function": lambda x: x},  # Function is not JSON serializable
            event_sequence_number=25
        )

        # Mock the database operations to focus on JSON handling
        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_conn = Mock(spec=sqlite3.Connection)
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value = mock_conn

            # Simulate JSON serialization error during execute
            mock_cursor.execute.side_effect = TypeError("Object is not JSON serializable")

            # Save should fail gracefully
            result = event_store.save_snapshot(snapshot)
            assert result is False

            # Verify rollback occurred
            mock_conn.rollback.assert_called_once()


class TestSaveSnapshotIntegration:
    """Test integration of save_snapshot() with existing database schema and Snapshot model."""

    def test_save_snapshot_integrates_with_existing_database_schema(self, tmp_path):
        """Test that save_snapshot() works with the existing database schema."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Verify the database schema was created correctly
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(snapshots)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type mapping

            # Verify expected columns exist (using actual schema column names)
            assert "workflow_id" in columns
            assert "sequence_number" in columns
            assert "state" in columns
            assert "created_at" in columns

        # Save should work with this schema
        snapshot = Snapshot(
            workflow_id="schema-integration-test",
            snapshot_data={"schema": "valid", "integration": True},
            event_sequence_number=333
        )

        result = event_store.save_snapshot(snapshot)
        assert result is True

        # Verify data was stored correctly according to schema
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM snapshots WHERE workflow_id = ?", ("schema-integration-test",))
            row = cursor.fetchone()

            assert row["workflow_id"] == "schema-integration-test"
            assert row["sequence_number"] == 333
            # Parse JSON data
            state_data = json.loads(row["state"])
            assert state_data["schema"] == "valid"
            assert state_data["integration"] is True
            assert row["created_at"] is not None

    def test_save_snapshot_preserves_snapshot_model_properties(self, tmp_path):
        """Test that save_snapshot() preserves all Snapshot model properties correctly."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create snapshot with complex data
        original_snapshot = Snapshot(
            workflow_id="model-properties-test",
            snapshot_data={
                "complex": {"nested": {"data": ["list", "items"]}},
                "numbers": [1, 2, 3.14, -5],
                "boolean": True,
                "null_value": None,
                "status": "active"
            },
            event_sequence_number=999
        )

        # Store original values for comparison
        original_workflow_id = original_snapshot.workflow_id
        original_snapshot_data = original_snapshot.snapshot_data
        original_sequence_number = original_snapshot.event_sequence_number

        # Save the snapshot
        result = event_store.save_snapshot(original_snapshot)
        assert result is True

        # Retrieve and verify all properties were preserved
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM snapshots WHERE workflow_id = ?", ("model-properties-test",))
            row = cursor.fetchone()

            assert row["workflow_id"] == original_workflow_id
            assert row["sequence_number"] == original_sequence_number
            # Parse JSON data for comparison
            stored_data = json.loads(row["state"])
            assert stored_data == original_snapshot_data  # JSON should match exactly

    def test_save_snapshot_integration_with_events_table(self, tmp_path):
        """Test that save_snapshot() works alongside events table operations."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # First add some events to the events table
        from jean_claude.core.event_models import Event
        event1 = Event(
            workflow_id="integration-workflow",
            event_type="task_started",
            event_data={"task": "integration_test"}
        )
        assert event_store.append(event1) is True

        # Now save a snapshot for the same workflow
        snapshot = Snapshot(
            workflow_id="integration-workflow",
            snapshot_data={"after_events": True, "event_count": 1},
            event_sequence_number=1
        )
        assert event_store.save_snapshot(snapshot) is True

        # Verify both tables have data
        with event_store as conn:
            cursor = conn.cursor()

            # Check events table
            cursor.execute("SELECT COUNT(*) as count FROM events WHERE workflow_id = ?", ("integration-workflow",))
            events_count = cursor.fetchone()["count"]
            assert events_count == 1

            # Check snapshots table
            cursor.execute("SELECT COUNT(*) as count FROM snapshots WHERE workflow_id = ?", ("integration-workflow",))
            snapshots_count = cursor.fetchone()["count"]
            assert snapshots_count == 1

            # Verify snapshot references correct event count
            cursor.execute("SELECT * FROM snapshots WHERE workflow_id = ?", ("integration-workflow",))
            snapshot_row = cursor.fetchone()
            assert snapshot_row["sequence_number"] == 1
