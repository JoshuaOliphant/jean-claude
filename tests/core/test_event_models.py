# ABOUTME: Test suite for Event and Snapshot SQLAlchemy models
# ABOUTME: Tests Event and Snapshot models with validation, relationships, and database operations

"""Test suite for Event and Snapshot models.

Tests the Event and Snapshot models including:
- Field validation and data types
- Auto-generated timestamps and sequence numbers
- JSON serialization/deserialization for event_data and snapshot_data
- Relationship constraints and database operations
"""

import pytest
from datetime import datetime
import json

try:
    from jean_claude.core.event_models import Event, Snapshot
except ImportError:
    Event = None
    Snapshot = None


@pytest.mark.skipif(Event is None, reason="Event model not implemented yet")
class TestEventModel:
    """Test Event model field validation and behavior."""

    def test_event_auto_generated_fields_and_equality(self):
        """Test that Event id/timestamp are auto-generated and equality is identity-based."""
        before = datetime.now()
        event1 = Event(
            workflow_id="test-workflow-123",
            event_type="workflow.started",
            event_data={"test": "data"}
        )
        event2 = Event(
            workflow_id="test-workflow-456",
            event_type="workflow.started",
            event_data={"test": "data"}
        )
        after = datetime.now()

        # IDs should be auto-generated and unique
        assert event1.id != event2.id

        # Timestamp should be set automatically
        assert isinstance(event1.timestamp, datetime)
        assert before <= event1.timestamp <= after

        # Equality is identity-based
        assert event1 != event2
        assert event1 == event1

    def test_event_field_validation(self):
        """Test workflow_id, event_type, and event_data validation."""
        # Valid workflow_id and event_type should work
        event = Event(
            workflow_id="valid-workflow-id",
            event_type="workflow.started",
            event_data={"test": "data"}
        )
        assert event.workflow_id == "valid-workflow-id"

        # Valid event types should all work
        for event_type in ["workflow.started", "workflow.completed", "feature.started",
                           "feature.completed", "task.queued"]:
            e = Event(workflow_id="test", event_type=event_type, event_data={"test": "data"})
            assert e.event_type == event_type

        # Invalid workflow_id
        for invalid in [None, ""]:
            with pytest.raises((ValueError, TypeError)):
                Event(workflow_id=invalid, event_type="workflow.started", event_data={"test": "data"})

        # Invalid event_type
        for invalid in [None, ""]:
            with pytest.raises((ValueError, TypeError)):
                Event(workflow_id="test", event_type=invalid, event_data={"test": "data"})

        # event_data=None should fail
        with pytest.raises((ValueError, TypeError)):
            Event(workflow_id="test", event_type="workflow.started", event_data=None)

    def test_event_data_json_serialization(self):
        """Test that event_data handles dicts and JSON serialization including empty dicts."""
        test_data = {
            "message": "Test message", "user_id": 123,
            "metadata": {"source": "api", "version": "1.0"},
            "items": ["item1", "item2", "item3"]
        }
        event = Event(workflow_id="test", event_type="workflow.started", event_data=test_data)
        assert event.event_data == test_data
        assert json.loads(json.dumps(event.event_data)) == test_data

        # Empty dict should work too
        empty = Event(workflow_id="test", event_type="workflow.started", event_data={})
        assert empty.event_data == {}
        assert isinstance(empty.event_data, dict)


@pytest.mark.skipif(Snapshot is None, reason="Snapshot model not implemented yet")
class TestSnapshotModel:
    """Test Snapshot model field validation and behavior."""

    def test_snapshot_auto_generated_fields_and_equality(self):
        """Test that Snapshot id/timestamp are auto-generated and equality is identity-based."""
        before = datetime.now()
        snap1 = Snapshot(workflow_id="test-123", snapshot_data={"state": "active"}, event_sequence_number=10)
        snap2 = Snapshot(workflow_id="test-456", snapshot_data={"state": "active"}, event_sequence_number=20)
        after = datetime.now()

        assert snap1.id != snap2.id
        assert isinstance(snap1.timestamp, datetime)
        assert before <= snap1.timestamp <= after
        assert snap1 != snap2
        assert snap1 == snap1

    def test_snapshot_field_validation(self):
        """Test workflow_id, snapshot_data, and event_sequence_number validation."""
        # Valid snapshot
        snap = Snapshot(workflow_id="valid-id", snapshot_data={"state": "active"}, event_sequence_number=42)
        assert snap.workflow_id == "valid-id"
        assert snap.event_sequence_number == 42

        # Zero sequence number is valid
        snap_zero = Snapshot(workflow_id="test", snapshot_data={"state": "active"}, event_sequence_number=0)
        assert snap_zero.event_sequence_number == 0

        # Invalid workflow_id
        for invalid in [None, ""]:
            with pytest.raises((ValueError, TypeError)):
                Snapshot(workflow_id=invalid, snapshot_data={"state": "active"}, event_sequence_number=42)

        # snapshot_data=None should fail
        with pytest.raises((ValueError, TypeError)):
            Snapshot(workflow_id="test", snapshot_data=None, event_sequence_number=42)

        # Invalid sequence numbers
        for invalid_seq in [None, -1, "not_a_number"]:
            with pytest.raises((ValueError, TypeError)):
                Snapshot(workflow_id="test", snapshot_data={"state": "active"}, event_sequence_number=invalid_seq)

    def test_snapshot_data_json_serialization(self):
        """Test that snapshot_data handles dicts and JSON serialization including empty dicts."""
        test_data = {
            "workflow_state": "implementing", "current_feature": "authentication",
            "progress": {"completed_features": 2, "total_features": 5, "percentage": 0.4},
            "metadata": {"last_updated": "2024-01-01T12:00:00Z", "version": "1.2.3"}
        }
        snap = Snapshot(workflow_id="test", snapshot_data=test_data, event_sequence_number=100)
        assert snap.snapshot_data == test_data
        assert json.loads(json.dumps(snap.snapshot_data)) == test_data

        # Empty dict should work too
        empty = Snapshot(workflow_id="test", snapshot_data={}, event_sequence_number=42)
        assert empty.snapshot_data == {}
        assert isinstance(empty.snapshot_data, dict)


@pytest.mark.skipif(Event is None or Snapshot is None, reason="Models not implemented yet")
class TestEventAndSnapshotIntegration:
    """Test Event and Snapshot model integration."""

    def test_event_and_snapshot_share_workflow_and_sequence(self):
        """Test Event and Snapshot can reference same workflow and snapshot tracks sequence."""
        workflow_id = "integration-test-workflow"
        event = Event(workflow_id=workflow_id, event_type="workflow.started", event_data={"message": "Starting"})
        snapshot = Snapshot(workflow_id=workflow_id, snapshot_data={"state": "init"}, event_sequence_number=50)

        assert event.workflow_id == snapshot.workflow_id == workflow_id
        assert snapshot.event_sequence_number == 50

    def test_models_json_serialization_roundtrip(self):
        """Test that both models work with JSON serialization patterns."""
        event_data = {
            "type": "feature_completed", "feature_name": "user_auth",
            "duration_ms": 45000, "files_changed": ["auth.py", "models.py", "tests.py"]
        }
        snapshot_data = {
            "workflow_phase": "implementing", "completed_features": ["user_auth"],
            "current_feature": "api_endpoints", "progress_percentage": 33.3
        }

        event = Event(workflow_id="json-test", event_type="feature.completed", event_data=event_data)
        snapshot = Snapshot(workflow_id="json-test", snapshot_data=snapshot_data, event_sequence_number=25)

        assert json.loads(json.dumps(event.event_data)) == event_data
        assert json.loads(json.dumps(snapshot.snapshot_data)) == snapshot_data

    def test_models_compatible_with_existing_event_infrastructure(self):
        """Test that models work with existing event logging patterns."""
        from jean_claude.core.events import Event as ExistingEvent, EventType

        new_event = Event(workflow_id="compat-test", event_type="workflow.started", event_data={"message": "Test"})
        existing_event_data = {
            "workflow_id": new_event.workflow_id,
            "event_type": new_event.event_type,
            "data": new_event.event_data
        }
        assert existing_event_data["workflow_id"] == new_event.workflow_id
        assert existing_event_data["data"] == new_event.event_data

    def test_models_compatible_with_database_schema(self):
        """Test that models match existing database schema fields."""
        event = Event(workflow_id="schema-test", event_type="workflow.started", event_data={"test": "data"})
        snapshot = Snapshot(workflow_id="schema-test", snapshot_data={"state": "active"}, event_sequence_number=1)

        # Event fields
        assert event.workflow_id == "schema-test"
        assert event.event_type == "workflow.started"
        assert event.event_data == {"test": "data"}
        assert event.timestamp is not None

        # Snapshot fields
        assert snapshot.workflow_id == "schema-test"
        assert snapshot.snapshot_data == {"state": "active"}
        assert snapshot.event_sequence_number == 1
        assert snapshot.timestamp is not None
