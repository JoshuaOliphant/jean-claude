# ABOUTME: Test suite for EventStore.get_events() method functionality
# ABOUTME: Tests event querying with workflow_id filtering, optional event type filtering and timestamp ordering

"""Test suite for EventStore.get_events() method.

Tests querying with workflow_id filtering, event_type filtering,
timestamp ordering, parameter validation, and error handling.
"""

import sqlite3
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
import pytest

from jean_claude.core.event_store import EventStore
from jean_claude.core.event_models import Event


class TestGetEventsBasicAndFiltering:
    """Test basic get_events functionality and filtering."""

    def test_get_events_filters_by_workflow_and_event_type(self, tmp_path):
        """Test querying by workflow_id, event_type, and handling empty results."""
        event_store = EventStore(tmp_path / "test.db")

        # Empty database returns empty list
        assert event_store.get_events("any-wf") == []

        # Add events for multiple workflows and types
        for wf in ["w1", "w1", "w2"]:
            for etype in ["started", "progress", "completed"]:
                event_store.append(Event(
                    workflow_id=wf, event_type=etype,
                    event_data={"wf": wf, "type": etype}
                ))

        # Filter by workflow
        w1_events = event_store.get_events("w1")
        assert len(w1_events) == 6  # 2 workflows * 3 types
        assert all(isinstance(e, Event) for e in w1_events)
        assert all(e.workflow_id == "w1" for e in w1_events)

        w2_events = event_store.get_events("w2")
        assert len(w2_events) == 3

        # Filter by workflow and event_type
        w1_started = event_store.get_events("w1", event_type="started")
        assert len(w1_started) == 2
        assert all(e.event_type == "started" for e in w1_started)

        # No matching event_type returns empty
        assert event_store.get_events("w1", event_type="nonexistent") == []

        # Non-existent workflow returns empty
        assert event_store.get_events("nonexistent-wf") == []

    def test_get_events_timestamp_ordering(self, tmp_path):
        """Test ascending (default) and descending timestamp ordering."""
        event_store = EventStore(tmp_path / "test.db")

        base = datetime.now()
        for i, (etype, label) in enumerate([("first", "oldest"), ("second", "middle"), ("third", "newest")]):
            e = Event(workflow_id="order-test", event_type=etype, event_data={"order": label})
            e.timestamp = base + timedelta(minutes=i)
            event_store.append(e)

        # Ascending (default)
        events_asc = event_store.get_events("order-test")
        assert len(events_asc) == 3
        assert events_asc[0].event_data["order"] == "oldest"
        assert events_asc[2].event_data["order"] == "newest"
        timestamps = [e.timestamp for e in events_asc]
        assert timestamps == sorted(timestamps)

        # Descending
        events_desc = event_store.get_events("order-test", order_by="desc")
        assert events_desc[0].event_data["order"] == "newest"
        assert events_desc[2].event_data["order"] == "oldest"

    def test_get_events_reconstructs_complex_event_data(self, tmp_path):
        """Test that complex event data is correctly reconstructed."""
        event_store = EventStore(tmp_path / "test.db")

        data = {
            "complex_data": {"nested": {"values": [1, 2, 3]}, "array": ["a", "b"], "boolean": True, "null_value": None},
            "number": 42
        }
        original = Event(workflow_id="recon-test", event_type="complex", event_data=data, version=5)
        ts = original.timestamp
        event_store.append(original)

        retrieved = event_store.get_events("recon-test")
        assert len(retrieved) == 1
        assert retrieved[0].event_data == data
        assert retrieved[0].timestamp == ts


class TestGetEventsValidation:
    """Test parameter validation in get_events()."""

    def test_get_events_validates_parameters(self, tmp_path):
        """Test validation of workflow_id, event_type, and order_by parameters."""
        event_store = EventStore(tmp_path / "test.db")

        # Invalid workflow_id
        for invalid in [None]:
            with pytest.raises((ValueError, TypeError)):
                event_store.get_events(invalid)
        for invalid in ["", "   "]:
            with pytest.raises(ValueError):
                event_store.get_events(invalid)

        # Invalid event_type
        for invalid in ["", "   "]:
            with pytest.raises(ValueError):
                event_store.get_events("valid-wf", event_type=invalid)

        # None event_type is OK (no filtering)
        assert isinstance(event_store.get_events("valid-wf", event_type=None), list)

        # Invalid order_by
        for invalid in ["invalid", ""]:
            with pytest.raises(ValueError):
                event_store.get_events("valid-wf", order_by=invalid)

        # Valid order_by values work
        for valid in ["asc", "desc"]:
            assert isinstance(event_store.get_events("valid-wf", order_by=valid), list)


class TestGetEventsErrorHandling:
    """Test error handling for database errors."""

    def test_get_events_handles_database_errors(self, tmp_path):
        """Test handling of connection and SQL execution errors."""
        event_store = EventStore(tmp_path / "test.db")

        # Connection error
        with patch.object(event_store, 'get_connection', side_effect=sqlite3.Error("Connection failed")):
            with pytest.raises(sqlite3.Error):
                event_store.get_events("test-wf")

        # SQL execution error
        with patch.object(event_store, 'get_connection') as mock_get, \
             patch.object(event_store, 'close_connection') as mock_close:
            mock_conn = Mock(spec=sqlite3.Connection)
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get.return_value = mock_conn
            mock_cursor.execute.side_effect = sqlite3.DatabaseError("SQL failed")

            with pytest.raises(sqlite3.Error):
                event_store.get_events("test-wf")
            mock_close.assert_called_with(mock_conn)
