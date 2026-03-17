# ABOUTME: Test suite for EventStore.save_snapshot() method functionality
# ABOUTME: Tests snapshot creation in snapshots table with workflow_id, data serialization, and event_count tracking

"""Test suite for EventStore.save_snapshot() method.

Tests snapshot save, replace, multi-workflow, transactions,
validation, and integration with events table.
"""

import sqlite3
import json
from unittest.mock import patch, Mock
from datetime import datetime
import pytest

from jean_claude.core.event_store import EventStore
from jean_claude.core.event_models import Snapshot


class TestSaveSnapshotBasicFunctionality:
    """Test basic save_snapshot functionality."""

    def test_save_and_replace_snapshot(self, tmp_path):
        """Test save, verify, and replace snapshot for same workflow."""
        event_store = EventStore(tmp_path / "test.db")

        snap1 = Snapshot(workflow_id="w-123", snapshot_data={"state": "initial", "count": 50},
                         event_sequence_number=50)
        assert event_store.save_snapshot(snap1) is True

        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM snapshots WHERE workflow_id = ?", ("w-123",))
            row = cursor.fetchone()
            assert row is not None
            assert row["sequence_number"] == 50
            assert json.loads(row["state"])["state"] == "initial"
            assert row["created_at"] is not None
            datetime.fromisoformat(row["created_at"])  # validates timestamp format

        # Replace with updated snapshot
        snap2 = Snapshot(workflow_id="w-123", snapshot_data={"state": "updated", "count": 100},
                         event_sequence_number=100)
        assert event_store.save_snapshot(snap2) is True

        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as c FROM snapshots WHERE workflow_id = ?", ("w-123",))
            assert cursor.fetchone()["c"] == 1
            cursor.execute("SELECT * FROM snapshots WHERE workflow_id = ?", ("w-123",))
            row = cursor.fetchone()
            assert json.loads(row["state"])["state"] == "updated"
            assert row["sequence_number"] == 100

    def test_save_multiple_workflows(self, tmp_path):
        """Test snapshots for different workflows are stored independently."""
        event_store = EventStore(tmp_path / "test.db")

        for wf_id, seq in [("w1", 75), ("w2", 200)]:
            snap = Snapshot(workflow_id=wf_id, snapshot_data={"wf": wf_id}, event_sequence_number=seq)
            assert event_store.save_snapshot(snap) is True

        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as c FROM snapshots")
            assert cursor.fetchone()["c"] == 2


class TestSaveSnapshotTransactions:
    """Test transaction handling in save_snapshot."""

    def test_commit_and_rollback_behavior(self, tmp_path):
        """Test commit on success and rollback on database/connection errors."""
        event_store = EventStore(tmp_path / "test.db")
        snap = Snapshot(workflow_id="tx-test", snapshot_data={"ok": True}, event_sequence_number=42)

        # Success path: commit called
        with patch.object(event_store, 'get_connection') as mock_get:
            mock_conn = Mock(spec=sqlite3.Connection)
            mock_conn.cursor.return_value = Mock()
            mock_get.return_value = mock_conn
            assert event_store.save_snapshot(snap) is True
            mock_conn.commit.assert_called_once()
            mock_conn.rollback.assert_not_called()

        # DB error: rollback called
        with patch.object(event_store, 'get_connection') as mock_get:
            mock_conn = Mock(spec=sqlite3.Connection)
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.DatabaseError("DB error")
            mock_get.return_value = mock_conn
            assert event_store.save_snapshot(snap) is False
            mock_conn.rollback.assert_called_once()
            mock_conn.commit.assert_not_called()

        # Connection error: returns False
        with patch.object(event_store, 'get_connection', side_effect=sqlite3.Error("Connection failed")):
            assert event_store.save_snapshot(snap) is False


class TestSaveSnapshotValidation:
    """Test snapshot parameter validation."""

    def test_validates_snapshot_parameter(self, tmp_path):
        """Test save_snapshot rejects None, non-Snapshot, and validates model fields."""
        event_store = EventStore(tmp_path / "test.db")

        assert event_store.save_snapshot(None) is False
        assert event_store.save_snapshot({"not": "a_snapshot"}) is False
        assert event_store.save_snapshot("invalid") is False

        # Model validation catches bad fields
        with pytest.raises(ValueError):
            Snapshot(workflow_id="", snapshot_data={"test": "data"}, event_sequence_number=10)
        with pytest.raises(ValueError):
            Snapshot(workflow_id="w", snapshot_data=None, event_sequence_number=10)
        with pytest.raises(ValueError):
            Snapshot(workflow_id="w", snapshot_data={"test": "data"}, event_sequence_number=-5)


class TestSaveSnapshotIntegration:
    """Test integration with database schema and events table."""

    def test_snapshot_alongside_events(self, tmp_path):
        """Test save_snapshot works alongside events table and preserves complex data."""
        from jean_claude.core.event_models import Event

        event_store = EventStore(tmp_path / "test.db")

        # Add event
        event = Event(workflow_id="int-wf", event_type="task_started", event_data={"task": "test"})
        assert event_store.append(event) is True

        # Save snapshot with complex data
        complex_data = {
            "complex": {"nested": {"data": ["list", "items"]}},
            "numbers": [1, 2, 3.14, -5], "boolean": True, "null_value": None
        }
        snap = Snapshot(workflow_id="int-wf", snapshot_data=complex_data, event_sequence_number=1)
        assert event_store.save_snapshot(snap) is True

        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as c FROM events WHERE workflow_id = ?", ("int-wf",))
            assert cursor.fetchone()["c"] == 1
            cursor.execute("SELECT * FROM snapshots WHERE workflow_id = ?", ("int-wf",))
            row = cursor.fetchone()
            assert json.loads(row["state"]) == complex_data
            assert row["sequence_number"] == 1
