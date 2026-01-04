# ABOUTME: Test suite for EventStore.append() method functionality
# ABOUTME: Tests single event writing, ACID transactions, and error handling with rollback

"""Test suite for EventStore.append() method functionality.

This module comprehensively tests the EventStore.append() method, including:

- Single event writing to SQLite database
- ACID transaction handling and automatic commit/rollback
- Error handling with proper transaction rollback on failures
- Event data validation and serialization
- Database connection management during append operations
- Integration with existing Event model and database schema

The tests follow TDD principles and use existing fixtures to ensure consistency
with the overall test suite.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

from jean_claude.core.event_store import EventStore
from jean_claude.core.event_models import Event


class TestEventAppendBasicFunctionality:
    """Test basic functionality of EventStore.append() method."""

    def test_append_single_event_success(self, tmp_path):
        """Test that append() successfully writes a single event to the database."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create an event to append
        event = Event(
            workflow_id="test-workflow-123",
            event_type="task_started",
            event_data={"task_id": "task-456", "priority": "high"}
        )

        # Append the event
        result = event_store.append(event)

        # Verify return value indicates success
        assert result is True

        # Verify event was written to database
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE workflow_id = ?", ("test-workflow-123",))
            row = cursor.fetchone()

            assert row is not None
            assert row["workflow_id"] == "test-workflow-123"
            assert row["event_type"] == "task_started"
            # Parse JSON data back to dict for verification (schema uses 'data' column as JSON text)
            import json
            data = json.loads(row["data"])
            assert data["task_id"] == "task-456"
            assert data["priority"] == "high"

    def test_append_event_with_proper_timestamp(self, tmp_path):
        """Test that append() preserves event timestamp when writing to database."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        event = Event(
            workflow_id="test-workflow-456",
            event_type="status_changed",
            event_data={"status": "completed"}
        )
        original_timestamp = event.timestamp

        # Append the event
        event_store.append(event)

        # Verify timestamp was preserved
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp FROM events WHERE workflow_id = ?", ("test-workflow-456",))
            row = cursor.fetchone()

            # Schema stores timestamp as TEXT in ISO format, so compare ISO strings
            from datetime import datetime
            assert row["timestamp"] == original_timestamp.isoformat()

    def test_append_multiple_events_sequential(self, tmp_path):
        """Test that multiple sequential append() calls work correctly."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create multiple events
        event1 = Event(
            workflow_id="workflow-seq-1",
            event_type="event_one",
            event_data={"sequence": 1}
        )
        event2 = Event(
            workflow_id="workflow-seq-1",
            event_type="event_two",
            event_data={"sequence": 2}
        )
        event3 = Event(
            workflow_id="workflow-seq-2",
            event_type="event_three",
            event_data={"sequence": 3}
        )

        # Append events sequentially
        assert event_store.append(event1) is True
        assert event_store.append(event2) is True
        assert event_store.append(event3) is True

        # Verify all events were stored
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM events")
            total_count = cursor.fetchone()["count"]
            assert total_count == 3

            # Verify specific workflow events
            cursor.execute("SELECT COUNT(*) as count FROM events WHERE workflow_id = ?", ("workflow-seq-1",))
            workflow1_count = cursor.fetchone()["count"]
            assert workflow1_count == 2


class TestEventAppendTransactions:
    """Test ACID transaction handling in EventStore.append() method."""

    def test_append_uses_transaction_commit_on_success(self, tmp_path):
        """Test that append() uses transactions and commits on success."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        event = Event(
            workflow_id="transaction-test",
            event_type="committed_event",
            event_data={"committed": True}
        )

        # Mock connection to track transaction calls
        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_conn = Mock(spec=sqlite3.Connection)
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value = mock_conn

            # Append should succeed
            result = event_store.append(event)
            assert result is True

            # Verify transaction handling
            mock_conn.commit.assert_called_once()
            mock_conn.rollback.assert_not_called()
            # Connection may be closed multiple times (e.g., by auto-snapshot cleanup)
            mock_conn.close.assert_called()

    def test_append_rollback_on_database_error(self, tmp_path):
        """Test that append() rolls back transaction on database errors."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        event = Event(
            workflow_id="rollback-test",
            event_type="failed_event",
            event_data={"will_fail": True}
        )

        # Mock connection to simulate database error during insert
        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_conn = Mock(spec=sqlite3.Connection)
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value = mock_conn

            # Simulate database error on execute
            mock_cursor.execute.side_effect = sqlite3.DatabaseError("Simulated database error")

            # Append should fail and return False
            result = event_store.append(event)
            assert result is False

            # Verify transaction was rolled back
            mock_conn.rollback.assert_called_once()
            mock_conn.commit.assert_not_called()
            # Connection may be closed multiple times (cleanup logic)
            mock_conn.close.assert_called()

    def test_append_rollback_on_connection_error(self, tmp_path):
        """Test that append() handles connection errors gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        event = Event(
            workflow_id="connection-error-test",
            event_type="connection_failed",
            event_data={"connection": "failed"}
        )

        # Mock get_connection to raise an error
        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = sqlite3.Error("Connection failed")

            # Append should fail gracefully
            result = event_store.append(event)
            assert result is False


class TestEventAppendValidation:
    """Test event validation and error handling in append() method."""

    def test_append_validates_event_parameter(self, tmp_path):
        """Test that append() validates the event parameter."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Test None event
        result = event_store.append(None)
        assert result is False

        # Test non-Event object
        result = event_store.append({"not": "an_event"})
        assert result is False

        # Test string instead of Event
        result = event_store.append("invalid_event")
        assert result is False

    def test_append_validates_required_event_fields(self, tmp_path):
        """Test that append() validates required event fields before database insert."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create event with missing required fields (this should be caught by Event model validation)
        with pytest.raises(ValueError, match="workflow_id cannot be None or empty"):
            Event(
                workflow_id="",  # Empty workflow_id should fail validation
                event_type="test_event",
                event_data={"test": "data"}
            )

        with pytest.raises(ValueError, match="event_type cannot be None or empty"):
            Event(
                workflow_id="test-workflow",
                event_type="",  # Empty event_type should fail validation
                event_data={"test": "data"}
            )

    def test_append_handles_json_serialization_error(self, tmp_path):
        """Test that append() handles JSON serialization errors in event_data."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create event with non-serializable data
        event = Event(
            workflow_id="json-error-test",
            event_type="serialization_test",
            event_data={"function": lambda x: x}  # Function is not JSON serializable
        )

        # Mock the database operations to focus on JSON handling
        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_conn = Mock(spec=sqlite3.Connection)
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value = mock_conn

            # Simulate JSON serialization error during execute
            mock_cursor.execute.side_effect = TypeError("Object is not JSON serializable")

            # Append should fail gracefully
            result = event_store.append(event)
            assert result is False

            # Verify rollback occurred
            mock_conn.rollback.assert_called_once()


class TestEventAppendIntegration:
    """Test integration of append() with existing database schema and Event model."""

    def test_append_integrates_with_existing_database_schema(self, tmp_path):
        """Test that append() works with the existing database schema."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Verify the database schema was created correctly
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(events)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type mapping

            # Verify expected columns exist (using actual schema column names)
            assert "sequence_number" in columns
            assert "workflow_id" in columns
            assert "event_id" in columns
            assert "event_type" in columns
            assert "data" in columns
            assert "timestamp" in columns

        # Append should work with this schema
        event = Event(
            workflow_id="schema-integration-test",
            event_type="schema_verified",
            event_data={"schema": "valid"}
        )

        result = event_store.append(event)
        assert result is True

        # Verify data was stored correctly according to schema
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE workflow_id = ?", ("schema-integration-test",))
            row = cursor.fetchone()

            assert row["sequence_number"] is not None  # Auto-generated sequence number
            assert row["event_id"] is not None  # Generated event ID
            assert row["workflow_id"] == "schema-integration-test"
            assert row["event_type"] == "schema_verified"
            # Parse JSON data
            import json
            data = json.loads(row["data"])
            assert data["schema"] == "valid"
            assert row["timestamp"] is not None

    def test_append_preserves_event_model_properties(self, tmp_path):
        """Test that append() preserves all Event model properties correctly."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create event with all properties
        original_event = Event(
            workflow_id="model-properties-test",
            event_type="properties_test",
            event_data={
                "complex": {"nested": {"data": ["list", "items"]}},
                "numbers": [1, 2, 3.14, -5],
                "boolean": True,
                "null_value": None
            },
            version=42
        )

        # Store original values for comparison
        original_workflow_id = original_event.workflow_id
        original_event_type = original_event.event_type
        original_event_data = original_event.event_data
        original_timestamp = original_event.timestamp
        original_version = original_event.version

        # Append the event
        result = event_store.append(original_event)
        assert result is True

        # Retrieve and verify all properties were preserved
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE workflow_id = ?", ("model-properties-test",))
            row = cursor.fetchone()

            assert row["workflow_id"] == original_workflow_id
            assert row["event_type"] == original_event_type
            # Parse JSON data for comparison
            import json
            stored_data = json.loads(row["data"])
            assert stored_data == original_event_data  # JSON should match exactly
            assert row["timestamp"] == original_timestamp.isoformat()
            # Note: version is stored as part of the Event model but not in this schema