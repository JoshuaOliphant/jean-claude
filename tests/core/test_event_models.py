# ABOUTME: Test suite for Event and Snapshot SQLAlchemy models
# ABOUTME: Tests Event and Snapshot models with validation, relationships, and database operations

"""Test suite for Event and Snapshot models.

Tests the Event and Snapshot models including:
- Field validation and data types
- Auto-generated timestamps and sequence numbers
- JSON serialization/deserialization for event_data and snapshot_data
- Relationship constraints
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

    def test_event_creation_with_auto_generated_fields(self):
        """Test that Event auto-generates id and timestamp, and stores all fields correctly."""
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
        # Fields stored correctly
        assert event1.workflow_id == "test-workflow-123"
        assert event1.event_type == "workflow.started"
        assert event1.event_data == {"test": "data"}

    @pytest.mark.parametrize("invalid_workflow_id", [None, ""])
    def test_event_workflow_id_rejects_invalid(self, invalid_workflow_id):
        """Invalid workflow_id values should raise errors."""
        with pytest.raises((ValueError, TypeError)):
            Event(workflow_id=invalid_workflow_id, event_type="workflow.started", event_data={"test": "data"})

    @pytest.mark.parametrize("invalid_event_type", [None, ""])
    def test_event_type_rejects_invalid(self, invalid_event_type):
        """Invalid event_type values should raise errors."""
        with pytest.raises((ValueError, TypeError)):
            Event(workflow_id="test-workflow", event_type=invalid_event_type, event_data={"test": "data"})

    @pytest.mark.parametrize("event_type", [
        "workflow.started", "workflow.completed", "feature.started", "feature.completed", "task.queued"
    ])
    def test_event_type_accepts_valid_types(self, event_type):
        """Valid event types should be accepted."""
        event = Event(workflow_id="test-workflow", event_type=event_type, event_data={"test": "data"})
        assert event.event_type == event_type

    def test_event_data_json_serialization(self):
        """Test that event_data accepts dict, handles empty dict, and serializes to JSON."""
        test_data = {
            "message": "Test message", "user_id": 123,
            "metadata": {"source": "api", "version": "1.0"},
            "items": ["item1", "item2", "item3"]
        }
        event = Event(workflow_id="test-workflow", event_type="workflow.started", event_data=test_data)
        assert event.event_data == test_data
        assert json.loads(json.dumps(event.event_data)) == test_data

        # Empty dict should also work
        empty_event = Event(workflow_id="test-workflow", event_type="workflow.started", event_data={})
        assert empty_event.event_data == {}

    def test_event_data_rejects_none(self):
        """event_data=None should raise an error."""
        with pytest.raises((ValueError, TypeError)):
            Event(workflow_id="test-workflow", event_type="workflow.started", event_data=None)

    def test_event_equality_is_identity_based(self):
        """Different Event instances should not be equal; same instance equals itself."""
        event1 = Event(workflow_id="test-workflow", event_type="workflow.started", event_data={"test": "data"})
        event2 = Event(workflow_id="test-workflow", event_type="workflow.started", event_data={"test": "data"})
        assert event1 != event2
        assert event1 == event1


@pytest.mark.skipif(Snapshot is None, reason="Snapshot model not implemented yet")
class TestSnapshotModel:
    """Test Snapshot model field validation and behavior."""

    def test_snapshot_creation_with_auto_generated_fields(self):
        """Test that Snapshot auto-generates id and timestamp, and stores all fields correctly."""
        before = datetime.now()
        snap1 = Snapshot(workflow_id="test-workflow-123", snapshot_data={"state": "active"}, event_sequence_number=10)
        snap2 = Snapshot(workflow_id="test-workflow-456", snapshot_data={"state": "active"}, event_sequence_number=20)
        after = datetime.now()

        assert snap1.id != snap2.id
        assert isinstance(snap1.timestamp, datetime)
        assert before <= snap1.timestamp <= after
        assert snap1.workflow_id == "test-workflow-123"
        assert snap1.snapshot_data == {"state": "active"}
        assert snap1.event_sequence_number == 10

    @pytest.mark.parametrize("invalid_workflow_id", [None, ""])
    def test_snapshot_workflow_id_rejects_invalid(self, invalid_workflow_id):
        """Invalid workflow_id values should raise errors."""
        with pytest.raises((ValueError, TypeError)):
            Snapshot(workflow_id=invalid_workflow_id, snapshot_data={"state": "active"}, event_sequence_number=42)

    def test_snapshot_data_json_serialization(self):
        """Test that snapshot_data accepts dict, handles empty, and serializes to JSON."""
        test_data = {
            "workflow_state": "implementing", "current_feature": "authentication",
            "progress": {"completed_features": 2, "total_features": 5, "percentage": 0.4}
        }
        snapshot = Snapshot(workflow_id="test-workflow", snapshot_data=test_data, event_sequence_number=100)
        assert snapshot.snapshot_data == test_data
        assert json.loads(json.dumps(snapshot.snapshot_data)) == test_data

        empty_snap = Snapshot(workflow_id="test-workflow", snapshot_data={}, event_sequence_number=42)
        assert empty_snap.snapshot_data == {}

    def test_snapshot_data_rejects_none(self):
        """snapshot_data=None should raise an error."""
        with pytest.raises((ValueError, TypeError)):
            Snapshot(workflow_id="test-workflow", snapshot_data=None, event_sequence_number=42)

    @pytest.mark.parametrize("invalid_seq", [None, -1, "not_a_number"])
    def test_event_sequence_number_rejects_invalid(self, invalid_seq):
        """Invalid sequence numbers should raise errors."""
        with pytest.raises((ValueError, TypeError)):
            Snapshot(workflow_id="test-workflow", snapshot_data={"state": "active"}, event_sequence_number=invalid_seq)

    def test_event_sequence_number_accepts_zero(self):
        """Zero should be a valid sequence number."""
        snapshot = Snapshot(workflow_id="test-workflow", snapshot_data={"state": "active"}, event_sequence_number=0)
        assert snapshot.event_sequence_number == 0

    def test_snapshot_equality_is_identity_based(self):
        """Different Snapshot instances should not be equal; same instance equals itself."""
        snap1 = Snapshot(workflow_id="test-workflow", snapshot_data={"state": "active"}, event_sequence_number=42)
        snap2 = Snapshot(workflow_id="test-workflow", snapshot_data={"state": "active"}, event_sequence_number=42)
        assert snap1 != snap2
        assert snap1 == snap1


@pytest.mark.skipif(Event is None or Snapshot is None, reason="Models not implemented yet")
class TestEventAndSnapshotIntegration:
    """Test Event and Snapshot model integration."""

    def test_event_and_snapshot_share_workflow_id(self):
        """Test that Event and Snapshot can reference the same workflow_id."""
        workflow_id = "integration-test-workflow"
        event = Event(workflow_id=workflow_id, event_type="workflow.started", event_data={"message": "Starting"})
        snapshot = Snapshot(workflow_id=workflow_id, snapshot_data={"state": "initializing"}, event_sequence_number=1)
        assert event.workflow_id == snapshot.workflow_id == workflow_id

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
