# ABOUTME: Test suite for EventStore.get_events() method functionality
# ABOUTME: Tests event querying with workflow_id filtering, optional event type filtering and timestamp ordering

"""Test suite for EventStore.get_events() method functionality.

This module comprehensively tests the EventStore.get_events() method, including:

- Event querying with required workflow_id filtering
- Optional event_type filtering for specific event types
- Timestamp ordering (ascending and descending)
- Integration with existing Event model and database schema
- Error handling for invalid parameters and database errors
- Performance with multiple events and complex queries

The tests follow TDD principles and use existing fixtures to ensure consistency
with the overall test suite.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
import pytest

from jean_claude.core.event_store import EventStore
from jean_claude.core.event_models import Event


class TestGetEventsBasicFunctionality:
    """Test basic functionality of EventStore.get_events() method."""

    def test_get_events_returns_list_of_events(self, tmp_path):
        """Test that get_events() returns a list of Event objects."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Add some test events
        event1 = Event(
            workflow_id="test-workflow-123",
            event_type="task_started",
            event_data={"task_id": "task-1"}
        )
        event2 = Event(
            workflow_id="test-workflow-123",
            event_type="task_completed",
            event_data={"task_id": "task-1", "status": "success"}
        )

        event_store.append(event1)
        event_store.append(event2)

        # Query events for the workflow
        events = event_store.get_events("test-workflow-123")

        # Verify return type and content
        assert isinstance(events, list)
        assert len(events) == 2
        assert all(isinstance(event, Event) for event in events)

    def test_get_events_filters_by_workflow_id(self, tmp_path):
        """Test that get_events() properly filters events by workflow_id."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Add events for multiple workflows
        workflow1_event1 = Event(
            workflow_id="workflow-1",
            event_type="started",
            event_data={"data": "workflow1_event1"}
        )
        workflow1_event2 = Event(
            workflow_id="workflow-1",
            event_type="completed",
            event_data={"data": "workflow1_event2"}
        )
        workflow2_event1 = Event(
            workflow_id="workflow-2",
            event_type="started",
            event_data={"data": "workflow2_event1"}
        )

        event_store.append(workflow1_event1)
        event_store.append(workflow1_event2)
        event_store.append(workflow2_event1)

        # Query events for workflow-1 only
        workflow1_events = event_store.get_events("workflow-1")

        # Verify only workflow-1 events are returned
        assert len(workflow1_events) == 2
        assert all(event.workflow_id == "workflow-1" for event in workflow1_events)
        assert any(event.event_data["data"] == "workflow1_event1" for event in workflow1_events)
        assert any(event.event_data["data"] == "workflow1_event2" for event in workflow1_events)

        # Query events for workflow-2 only
        workflow2_events = event_store.get_events("workflow-2")

        # Verify only workflow-2 events are returned
        assert len(workflow2_events) == 1
        assert workflow2_events[0].workflow_id == "workflow-2"
        assert workflow2_events[0].event_data["data"] == "workflow2_event1"

    def test_get_events_returns_empty_list_for_nonexistent_workflow(self, tmp_path):
        """Test that get_events() returns empty list for non-existent workflow_id."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Add an event for a different workflow
        event = Event(
            workflow_id="existing-workflow",
            event_type="test_event",
            event_data={"test": "data"}
        )
        event_store.append(event)

        # Query for non-existent workflow
        events = event_store.get_events("nonexistent-workflow")

        # Should return empty list
        assert isinstance(events, list)
        assert len(events) == 0

    def test_get_events_handles_empty_database(self, tmp_path):
        """Test that get_events() handles empty database gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Query events from empty database
        events = event_store.get_events("any-workflow-id")

        # Should return empty list
        assert isinstance(events, list)
        assert len(events) == 0


class TestGetEventsEventTypeFiltering:
    """Test event type filtering functionality in get_events() method."""

    def test_get_events_filters_by_event_type(self, tmp_path):
        """Test that get_events() can filter by event_type parameter."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Add events with different types for same workflow
        start_event = Event(
            workflow_id="filter-test",
            event_type="task_started",
            event_data={"task": "start"}
        )
        progress_event = Event(
            workflow_id="filter-test",
            event_type="task_progress",
            event_data={"progress": 50}
        )
        complete_event = Event(
            workflow_id="filter-test",
            event_type="task_completed",
            event_data={"result": "success"}
        )
        another_start_event = Event(
            workflow_id="filter-test",
            event_type="task_started",
            event_data={"task": "restart"}
        )

        event_store.append(start_event)
        event_store.append(progress_event)
        event_store.append(complete_event)
        event_store.append(another_start_event)

        # Query for specific event type
        started_events = event_store.get_events("filter-test", event_type="task_started")

        # Verify only task_started events are returned
        assert len(started_events) == 2
        assert all(event.event_type == "task_started" for event in started_events)
        assert any(event.event_data["task"] == "start" for event in started_events)
        assert any(event.event_data["task"] == "restart" for event in started_events)

        # Query for different event type
        progress_events = event_store.get_events("filter-test", event_type="task_progress")
        assert len(progress_events) == 1
        assert progress_events[0].event_type == "task_progress"
        assert progress_events[0].event_data["progress"] == 50

    def test_get_events_without_event_type_returns_all_events(self, tmp_path):
        """Test that get_events() without event_type parameter returns all workflow events."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Add events with different types
        events = [
            Event(workflow_id="all-events-test", event_type="type1", event_data={"order": 1}),
            Event(workflow_id="all-events-test", event_type="type2", event_data={"order": 2}),
            Event(workflow_id="all-events-test", event_type="type3", event_data={"order": 3})
        ]

        for event in events:
            event_store.append(event)

        # Query without event_type filter
        all_events = event_store.get_events("all-events-test")

        # Should return all events for the workflow
        assert len(all_events) == 3
        returned_types = {event.event_type for event in all_events}
        assert returned_types == {"type1", "type2", "type3"}

    def test_get_events_event_type_filter_returns_empty_for_no_matches(self, tmp_path):
        """Test that event_type filter returns empty list when no events match."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Add events of different types
        event = Event(
            workflow_id="no-match-test",
            event_type="existing_type",
            event_data={"test": "data"}
        )
        event_store.append(event)

        # Query for non-existent event type
        filtered_events = event_store.get_events("no-match-test", event_type="nonexistent_type")

        assert isinstance(filtered_events, list)
        assert len(filtered_events) == 0


class TestGetEventsTimestampOrdering:
    """Test timestamp ordering functionality in get_events() method."""

    def test_get_events_orders_by_timestamp_ascending_by_default(self, tmp_path):
        """Test that get_events() orders events by timestamp in ascending order by default."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create events with known timestamps (oldest to newest)
        base_time = datetime.now()
        oldest_event = Event(
            workflow_id="order-test",
            event_type="first",
            event_data={"order": "oldest"}
        )
        oldest_event.timestamp = base_time

        middle_event = Event(
            workflow_id="order-test",
            event_type="second",
            event_data={"order": "middle"}
        )
        middle_event.timestamp = base_time + timedelta(minutes=1)

        newest_event = Event(
            workflow_id="order-test",
            event_type="third",
            event_data={"order": "newest"}
        )
        newest_event.timestamp = base_time + timedelta(minutes=2)

        # Append in non-chronological order to test ordering
        event_store.append(middle_event)
        event_store.append(oldest_event)
        event_store.append(newest_event)

        # Query events (should be ordered by timestamp ascending)
        events = event_store.get_events("order-test")

        # Verify ascending timestamp order
        assert len(events) == 3
        assert events[0].event_data["order"] == "oldest"
        assert events[1].event_data["order"] == "middle"
        assert events[2].event_data["order"] == "newest"

        # Verify timestamps are in ascending order
        timestamps = [event.timestamp for event in events]
        assert timestamps == sorted(timestamps)

    def test_get_events_supports_descending_timestamp_order(self, tmp_path):
        """Test that get_events() can order events by timestamp in descending order."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create events with known timestamps
        base_time = datetime.now()
        events_data = [
            ("first", base_time, "oldest"),
            ("second", base_time + timedelta(minutes=1), "middle"),
            ("third", base_time + timedelta(minutes=2), "newest")
        ]

        # Add events to store
        for event_type, timestamp, order in events_data:
            event = Event(
                workflow_id="desc-order-test",
                event_type=event_type,
                event_data={"order": order}
            )
            event.timestamp = timestamp
            event_store.append(event)

        # Query with descending order
        events = event_store.get_events("desc-order-test", order_by="desc")

        # Verify descending timestamp order (newest first)
        assert len(events) == 3
        assert events[0].event_data["order"] == "newest"
        assert events[1].event_data["order"] == "middle"
        assert events[2].event_data["order"] == "oldest"

        # Verify timestamps are in descending order
        timestamps = [event.timestamp for event in events]
        assert timestamps == sorted(timestamps, reverse=True)


class TestGetEventsValidation:
    """Test parameter validation and error handling in get_events() method."""

    def test_get_events_validates_workflow_id_parameter(self, tmp_path):
        """Test that get_events() validates workflow_id parameter."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Test None workflow_id
        with pytest.raises((ValueError, TypeError)):
            event_store.get_events(None)

        # Test empty string workflow_id
        with pytest.raises(ValueError):
            event_store.get_events("")

        # Test whitespace-only workflow_id
        with pytest.raises(ValueError):
            event_store.get_events("   ")

    def test_get_events_validates_event_type_parameter(self, tmp_path):
        """Test that get_events() validates event_type parameter when provided."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Test empty string event_type
        with pytest.raises(ValueError):
            event_store.get_events("valid-workflow", event_type="")

        # Test whitespace-only event_type
        with pytest.raises(ValueError):
            event_store.get_events("valid-workflow", event_type="   ")

        # Test None event_type should be allowed (means no filtering)
        # This should not raise an exception
        events = event_store.get_events("valid-workflow", event_type=None)
        assert isinstance(events, list)

    def test_get_events_validates_order_by_parameter(self, tmp_path):
        """Test that get_events() validates order_by parameter."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Test invalid order_by values
        with pytest.raises(ValueError):
            event_store.get_events("valid-workflow", order_by="invalid")

        with pytest.raises(ValueError):
            event_store.get_events("valid-workflow", order_by="")

        # Test valid order_by values should not raise exception
        events_asc = event_store.get_events("valid-workflow", order_by="asc")
        events_desc = event_store.get_events("valid-workflow", order_by="desc")
        assert isinstance(events_asc, list)
        assert isinstance(events_desc, list)


class TestGetEventsErrorHandling:
    """Test error handling and database error scenarios in get_events() method."""

    def test_get_events_handles_database_connection_error(self, tmp_path):
        """Test that get_events() handles database connection errors gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Mock get_connection to raise an error
        with patch.object(event_store, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = sqlite3.Error("Connection failed")

            # get_events should handle the error and return empty list or raise appropriate exception
            with pytest.raises(sqlite3.Error):
                event_store.get_events("test-workflow")

    def test_get_events_handles_sql_execution_error(self, tmp_path):
        """Test that get_events() handles SQL execution errors gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Mock connection and close_connection to simulate SQL error
        with patch.object(event_store, 'get_connection') as mock_get_conn, \
             patch.object(event_store, 'close_connection') as mock_close_conn:
            mock_conn = Mock(spec=sqlite3.Connection)
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value = mock_conn

            # Simulate SQL execution error
            mock_cursor.execute.side_effect = sqlite3.DatabaseError("SQL execution failed")

            # get_events should handle the error appropriately
            with pytest.raises(sqlite3.Error):
                event_store.get_events("test-workflow")

            # Verify connection cleanup
            mock_close_conn.assert_called_with(mock_conn)


class TestGetEventsIntegration:
    """Test integration of get_events() with existing database schema and Event model."""

    def test_get_events_reconstructs_event_objects_properly(self, tmp_path):
        """Test that get_events() properly reconstructs Event objects from database rows."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create complex event data
        original_event_data = {
            "complex_data": {
                "nested": {"values": [1, 2, 3]},
                "array": ["a", "b", "c"],
                "boolean": True,
                "null_value": None
            },
            "simple_string": "test_string",
            "number": 42
        }

        # Create and store event
        original_event = Event(
            workflow_id="reconstruction-test",
            event_type="complex_event",
            event_data=original_event_data,
            version=5
        )
        original_timestamp = original_event.timestamp

        event_store.append(original_event)

        # Retrieve and verify reconstruction
        retrieved_events = event_store.get_events("reconstruction-test")

        assert len(retrieved_events) == 1
        reconstructed_event = retrieved_events[0]

        # Verify all properties are correctly reconstructed
        assert reconstructed_event.workflow_id == "reconstruction-test"
        assert reconstructed_event.event_type == "complex_event"
        assert reconstructed_event.event_data == original_event_data
        assert reconstructed_event.timestamp == original_timestamp

    def test_get_events_works_with_append_integration(self, tmp_path):
        """Test that get_events() works seamlessly with append() method."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create and append multiple events
        events_to_append = []
        for i in range(5):
            event = Event(
                workflow_id="integration-test",
                event_type=f"event_type_{i}",
                event_data={"sequence": i, "description": f"Event number {i}"}
            )
            events_to_append.append(event)
            assert event_store.append(event) is True

        # Retrieve all events
        retrieved_events = event_store.get_events("integration-test")

        # Verify count and data integrity
        assert len(retrieved_events) == 5
        for i, retrieved_event in enumerate(retrieved_events):
            assert retrieved_event.event_type == f"event_type_{i}"
            assert retrieved_event.event_data["sequence"] == i
            assert retrieved_event.event_data["description"] == f"Event number {i}"

    def test_get_events_handles_multiple_workflows_complex_scenario(self, tmp_path):
        """Test get_events() in complex scenario with multiple workflows and event types."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Setup complex scenario with multiple workflows and event types
        workflows = ["workflow-A", "workflow-B", "workflow-C"]
        event_types = ["started", "progress", "completed", "error"]

        # Add events for each workflow and type combination
        for workflow in workflows:
            for event_type in event_types:
                event = Event(
                    workflow_id=workflow,
                    event_type=event_type,
                    event_data={"workflow": workflow, "type": event_type}
                )
                event_store.append(event)

        # Test filtering by workflow
        workflow_a_events = event_store.get_events("workflow-A")
        assert len(workflow_a_events) == 4  # 4 event types for workflow-A
        assert all(event.workflow_id == "workflow-A" for event in workflow_a_events)

        # Test filtering by workflow and event type
        workflow_b_started = event_store.get_events("workflow-B", event_type="started")
        assert len(workflow_b_started) == 1
        assert workflow_b_started[0].workflow_id == "workflow-B"
        assert workflow_b_started[0].event_type == "started"

        # Test that error events are properly isolated
        workflow_c_errors = event_store.get_events("workflow-C", event_type="error")
        assert len(workflow_c_errors) == 1
        assert workflow_c_errors[0].event_data["type"] == "error"