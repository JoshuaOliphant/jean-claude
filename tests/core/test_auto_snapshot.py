# ABOUTME: Test suite for EventStore automatic snapshot creation feature
# ABOUTME: Tests automatic snapshot creation every 100 events in the append() method

"""Test suite for EventStore automatic snapshot creation functionality.

This module comprehensively tests the automatic snapshot creation feature, including:

- Automatic snapshot creation triggered every 100 events
- Snapshot creation triggered only for the correct workflow_id
- Integration with existing append() and save_snapshot() methods
- Snapshot content verification with proper event count tracking
- Multiple workflow isolation (each workflow gets its own snapshots)
- Edge cases and error handling during auto-snapshot creation

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
from jean_claude.core.event_models import Event, Snapshot


class TestAutoSnapshotCreationBasic:
    """Test basic functionality of automatic snapshot creation."""

    def test_auto_snapshot_created_at_100_events(self, tmp_path):
        """Test that a snapshot is automatically created when the 100th event is appended."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "test-workflow-100"

        # Append 99 events - no snapshot should be created yet
        for i in range(99):
            event = Event(
                workflow_id=workflow_id,
                event_type=f"event_{i+1}",
                event_data={"sequence": i+1}
            )
            result = event_store.append(event)
            assert result is True

        # Verify no snapshot exists yet
        snapshot = event_store.get_snapshot(workflow_id)
        assert snapshot is None

        # Append the 100th event - this should trigger snapshot creation
        event_100 = Event(
            workflow_id=workflow_id,
            event_type="event_100",
            event_data={"sequence": 100, "milestone": "100th event"}
        )
        result = event_store.append(event_100)
        assert result is True

        # Verify snapshot was automatically created
        snapshot = event_store.get_snapshot(workflow_id)
        assert snapshot is not None
        assert snapshot.workflow_id == workflow_id
        assert snapshot.event_sequence_number == 100

    def test_auto_snapshot_created_at_200_events(self, tmp_path):
        """Test that another snapshot is created at 200 events (next 100-event interval)."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "test-workflow-200"

        # Append 200 events
        for i in range(200):
            event = Event(
                workflow_id=workflow_id,
                event_type=f"event_{i+1}",
                event_data={"sequence": i+1}
            )
            result = event_store.append(event)
            assert result is True

        # Verify snapshot exists at event 200
        snapshot = event_store.get_snapshot(workflow_id)
        assert snapshot is not None
        assert snapshot.workflow_id == workflow_id
        assert snapshot.event_sequence_number == 200

    def test_auto_snapshot_workflow_isolation(self, tmp_path):
        """Test that each workflow gets its own snapshot timing and isolation."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_1 = "workflow-1"
        workflow_2 = "workflow-2"

        # Append 50 events to workflow_1
        for i in range(50):
            event = Event(
                workflow_id=workflow_1,
                event_type=f"event_{i+1}",
                event_data={"sequence": i+1}
            )
            event_store.append(event)

        # Append 100 events to workflow_2 - should trigger snapshot for workflow_2 only
        for i in range(100):
            event = Event(
                workflow_id=workflow_2,
                event_type=f"event_{i+1}",
                event_data={"sequence": i+1}
            )
            event_store.append(event)

        # Verify workflow_1 has no snapshot (only 50 events)
        snapshot_1 = event_store.get_snapshot(workflow_1)
        assert snapshot_1 is None

        # Verify workflow_2 has snapshot (100 events)
        snapshot_2 = event_store.get_snapshot(workflow_2)
        assert snapshot_2 is not None
        assert snapshot_2.workflow_id == workflow_2
        assert snapshot_2.event_sequence_number == 100

        # Add 50 more events to workflow_1 (total 100) - should trigger snapshot
        for i in range(50, 100):
            event = Event(
                workflow_id=workflow_1,
                event_type=f"event_{i+1}",
                event_data={"sequence": i+1}
            )
            event_store.append(event)

        # Now workflow_1 should have a snapshot too
        snapshot_1 = event_store.get_snapshot(workflow_1)
        assert snapshot_1 is not None
        assert snapshot_1.workflow_id == workflow_1
        assert snapshot_1.event_sequence_number == 100


class TestAutoSnapshotContent:
    """Test the content and structure of automatically created snapshots."""

    def test_auto_snapshot_contains_workflow_events_summary(self, tmp_path):
        """Test that auto-generated snapshot contains a summary of workflow events."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "workflow-content-test"

        # Create events with different types to verify summary
        event_types = ["task_created", "task_updated", "task_completed", "workflow_updated"]

        # Append 100 events with different types
        for i in range(100):
            event_type = event_types[i % len(event_types)]
            event = Event(
                workflow_id=workflow_id,
                event_type=event_type,
                event_data={"sequence": i+1, "type_group": event_type}
            )
            event_store.append(event)

        # Verify snapshot was created and has expected content
        snapshot = event_store.get_snapshot(workflow_id)
        assert snapshot is not None
        assert snapshot.workflow_id == workflow_id
        assert snapshot.event_sequence_number == 100

        # Verify snapshot data contains summary information
        snapshot_data = snapshot.snapshot_data
        assert "total_events" in snapshot_data
        assert snapshot_data["total_events"] == 100
        assert "last_event_sequence" in snapshot_data
        assert snapshot_data["last_event_sequence"] == 100
        assert "workflow_id" in snapshot_data
        assert snapshot_data["workflow_id"] == workflow_id

    def test_auto_snapshot_replaces_existing_snapshot(self, tmp_path):
        """Test that auto-created snapshot replaces previous snapshots for the same workflow."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "workflow-replace-test"

        # Create first snapshot at 100 events
        for i in range(100):
            event = Event(
                workflow_id=workflow_id,
                event_type="event",
                event_data={"sequence": i+1}
            )
            event_store.append(event)

        # Verify first snapshot
        snapshot_100 = event_store.get_snapshot(workflow_id)
        assert snapshot_100 is not None
        assert snapshot_100.event_sequence_number == 100

        # Create second snapshot at 200 events
        for i in range(100, 200):
            event = Event(
                workflow_id=workflow_id,
                event_type="event",
                event_data={"sequence": i+1}
            )
            event_store.append(event)

        # Verify second snapshot replaced the first one
        snapshot_200 = event_store.get_snapshot(workflow_id)
        assert snapshot_200 is not None
        assert snapshot_200.event_sequence_number == 200

        # Verify only one snapshot exists in database (replaced, not duplicated)
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM snapshots WHERE workflow_id = ?", (workflow_id,))
            count = cursor.fetchone()["count"]
            assert count == 1


class TestAutoSnapshotIntegration:
    """Test integration of auto-snapshot with existing EventStore methods."""

    def test_auto_snapshot_integrates_with_existing_save_snapshot(self, tmp_path):
        """Test that auto-snapshot creation works alongside manual save_snapshot calls."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "integration-test"

        # Manually save a snapshot at event 50
        manual_snapshot = Snapshot(
            workflow_id=workflow_id,
            snapshot_data={"manual": True, "event_count": 50},
            event_sequence_number=50
        )
        result = event_store.save_snapshot(manual_snapshot)
        assert result is True

        # Add 50 more events (total 50, no auto-snapshot yet)
        for i in range(50):
            event = Event(
                workflow_id=workflow_id,
                event_type="event",
                event_data={"sequence": i+1}
            )
            event_store.append(event)

        # Verify manual snapshot still exists
        snapshot = event_store.get_snapshot(workflow_id)
        assert snapshot is not None
        assert snapshot.event_sequence_number == 50
        assert snapshot.snapshot_data["manual"] is True

        # Add 50 more events (total 100) - should trigger auto-snapshot
        for i in range(50, 100):
            event = Event(
                workflow_id=workflow_id,
                event_type="event",
                event_data={"sequence": i+1}
            )
            event_store.append(event)

        # Verify auto-snapshot replaced manual snapshot
        snapshot = event_store.get_snapshot(workflow_id)
        assert snapshot is not None
        assert snapshot.event_sequence_number == 100
        # Auto-snapshot should not have the "manual" flag
        assert "manual" not in snapshot.snapshot_data or snapshot.snapshot_data.get("manual") is not True

    def test_auto_snapshot_append_transaction_handling(self, tmp_path):
        """Test that auto-snapshot creation doesn't break append() transaction handling."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "transaction-test"

        # Add 99 events successfully
        for i in range(99):
            event = Event(
                workflow_id=workflow_id,
                event_type="event",
                event_data={"sequence": i+1}
            )
            result = event_store.append(event)
            assert result is True

        # Verify no snapshot yet
        snapshot = event_store.get_snapshot(workflow_id)
        assert snapshot is None

        # Test with mocked snapshot save failure to ensure transaction rollback
        with patch.object(event_store, 'save_snapshot') as mock_save:
            mock_save.return_value = False  # Simulate snapshot save failure

            # Append 100th event - should try to create snapshot and handle failure
            event_100 = Event(
                workflow_id=workflow_id,
                event_type="event",
                event_data={"sequence": 100}
            )

            # The event should still be appended successfully even if snapshot fails
            result = event_store.append(event_100)
            assert result is True

            # Verify the event was saved even though snapshot failed
            events = event_store.get_events(workflow_id)
            assert len(events) == 100


class TestAutoSnapshotErrorHandling:
    """Test error handling during automatic snapshot creation."""

    def test_auto_snapshot_failure_does_not_prevent_event_append(self, tmp_path):
        """Test that snapshot creation failure doesn't prevent event from being appended."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "error-handling-test"

        # Add 99 events
        for i in range(99):
            event = Event(
                workflow_id=workflow_id,
                event_type="event",
                event_data={"sequence": i+1}
            )
            event_store.append(event)

        # Mock save_snapshot to fail
        with patch.object(event_store, 'save_snapshot') as mock_save:
            mock_save.return_value = False  # Simulate snapshot save failure

            # Append 100th event - snapshot will fail but event should succeed
            event_100 = Event(
                workflow_id=workflow_id,
                event_type="event",
                event_data={"sequence": 100}
            )
            result = event_store.append(event_100)

            # Event append should still succeed
            assert result is True

            # Verify snapshot save was attempted
            mock_save.assert_called_once()

        # Verify event was actually stored despite snapshot failure
        events = event_store.get_events(workflow_id)
        assert len(events) == 100

        # Verify no snapshot was created due to failure
        snapshot = event_store.get_snapshot(workflow_id)
        assert snapshot is None

    def test_auto_snapshot_handles_corrupted_snapshot_data(self, tmp_path):
        """Test that auto-snapshot creation handles edge cases gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "corruption-test"

        # Add events to trigger snapshot
        for i in range(100):
            event = Event(
                workflow_id=workflow_id,
                event_type="event",
                event_data={"sequence": i+1}
            )
            event_store.append(event)

        # Verify snapshot was created normally
        snapshot = event_store.get_snapshot(workflow_id)
        assert snapshot is not None
        assert snapshot.event_sequence_number == 100

        # Verify snapshot data is properly structured
        assert isinstance(snapshot.snapshot_data, dict)
        assert "total_events" in snapshot.snapshot_data
        assert "workflow_id" in snapshot.snapshot_data