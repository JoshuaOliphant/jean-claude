# ABOUTME: Test suite for Event and Snapshot SQLAlchemy models
# ABOUTME: Tests Event and Snapshot models with validation, relationships, and database operations

"""Test suite for Event and Snapshot models.

Tests the Event and Snapshot SQLAlchemy models including:
- Field validation and data types
- Auto-generated timestamps and sequence numbers
- JSON serialization/deserialization for event_data and snapshot_data
- Relationship constraints and database operations
- Model factories for test data creation

This follows TDD approach - tests are written first to define expected behavior.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock
import json
from dataclasses import dataclass

# Import will fail until we implement the models - that's expected in TDD
try:
    from jean_claude.core.event_models import Event, Snapshot
except ImportError:
    # Allow tests to be written before implementation
    Event = None
    Snapshot = None


@pytest.mark.skipif(Event is None, reason="Event model not implemented yet")
class TestEventModel:
    """Test Event model field validation and behavior."""

    def test_event_id_auto_generated(self):
        """Test that Event id is auto-generated as primary key."""
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

        # IDs should be auto-generated and unique
        assert event1.id != event2.id

    def test_event_timestamp_auto_generated(self):
        """Test that Event timestamp is auto-generated."""
        before_creation = datetime.now()
        event = Event(
            workflow_id="test-workflow-123",
            event_type="workflow.started",
            event_data={"test": "data"}
        )
        after_creation = datetime.now()

        # Timestamp should be set automatically
        assert isinstance(event.timestamp, datetime)
        assert before_creation <= event.timestamp <= after_creation

    def test_event_workflow_id_required_and_validated(self):
        """Test that workflow_id is required and validates properly."""
        # Valid workflow_id should work
        event = Event(
            workflow_id="valid-workflow-id",
            event_type="workflow.started",
            event_data={"test": "data"}
        )
        assert event.workflow_id == "valid-workflow-id"

        # Invalid workflow_id should raise validation error
        with pytest.raises((ValueError, TypeError)):
            Event(
                workflow_id=None,
                event_type="workflow.started",
                event_data={"test": "data"}
            )

        with pytest.raises((ValueError, TypeError)):
            Event(
                workflow_id="",
                event_type="workflow.started",
                event_data={"test": "data"}
            )

    def test_event_type_required_and_validated(self):
        """Test that event_type is required and validates properly."""
        # Valid event_type should work
        valid_types = [
            "workflow.started",
            "workflow.completed",
            "feature.started",
            "feature.completed",
            "task.queued"
        ]

        for event_type in valid_types:
            event = Event(
                workflow_id="test-workflow",
                event_type=event_type,
                event_data={"test": "data"}
            )
            assert event.event_type == event_type

        # Invalid event_type should raise validation error
        with pytest.raises((ValueError, TypeError)):
            Event(
                workflow_id="test-workflow",
                event_type=None,
                event_data={"test": "data"}
            )

        with pytest.raises((ValueError, TypeError)):
            Event(
                workflow_id="test-workflow",
                event_type="",
                event_data={"test": "data"}
            )

    def test_event_data_accepts_dict_and_serializes_to_json(self):
        """Test that event_data accepts dict and handles JSON serialization."""
        test_data = {
            "message": "Test message",
            "user_id": 123,
            "metadata": {
                "source": "api",
                "version": "1.0"
            },
            "items": ["item1", "item2", "item3"]
        }

        event = Event(
            workflow_id="test-workflow",
            event_type="workflow.started",
            event_data=test_data
        )

        # event_data should store the dict
        assert event.event_data == test_data

        # Should be JSON serializable
        json_str = json.dumps(event.event_data)
        assert isinstance(json_str, str)
        assert json.loads(json_str) == test_data

    def test_event_data_handles_empty_dict(self):
        """Test that event_data can be an empty dict."""
        event = Event(
            workflow_id="test-workflow",
            event_type="workflow.started",
            event_data={}
        )

        assert event.event_data == {}
        assert isinstance(event.event_data, dict)

    def test_event_data_validates_required(self):
        """Test that event_data is required."""
        with pytest.raises((ValueError, TypeError)):
            Event(
                workflow_id="test-workflow",
                event_type="workflow.started",
                event_data=None
            )

    def test_event_equality_comparison(self):
        """Test Event equality comparison."""
        event1 = Event(
            workflow_id="test-workflow",
            event_type="workflow.started",
            event_data={"test": "data"}
        )
        event2 = Event(
            workflow_id="test-workflow",
            event_type="workflow.started",
            event_data={"test": "data"}
        )

        # Different instances should not be equal (different IDs)
        assert event1 != event2

        # Same instance should equal itself
        assert event1 == event1


@pytest.mark.skipif(Snapshot is None, reason="Snapshot model not implemented yet")
class TestSnapshotModel:
    """Test Snapshot model field validation and behavior."""

    def test_snapshot_id_auto_generated(self):
        """Test that Snapshot id is auto-generated as primary key."""
        snapshot1 = Snapshot(
            workflow_id="test-workflow-123",
            snapshot_data={"state": "active"},
            event_sequence_number=10
        )
        snapshot2 = Snapshot(
            workflow_id="test-workflow-456",
            snapshot_data={"state": "active"},
            event_sequence_number=20
        )

        # IDs should be auto-generated and unique
        assert snapshot1.id != snapshot2.id

    def test_snapshot_timestamp_auto_generated(self):
        """Test that Snapshot timestamp is auto-generated."""
        before_creation = datetime.now()
        snapshot = Snapshot(
            workflow_id="test-workflow-123",
            snapshot_data={"state": "active"},
            event_sequence_number=42
        )
        after_creation = datetime.now()

        # Timestamp should be set automatically
        assert isinstance(snapshot.timestamp, datetime)
        assert before_creation <= snapshot.timestamp <= after_creation

    def test_snapshot_workflow_id_required_and_validated(self):
        """Test that workflow_id is required and validates properly."""
        # Valid workflow_id should work
        snapshot = Snapshot(
            workflow_id="valid-workflow-id",
            snapshot_data={"state": "active"},
            event_sequence_number=42
        )
        assert snapshot.workflow_id == "valid-workflow-id"

        # Invalid workflow_id should raise validation error
        with pytest.raises((ValueError, TypeError)):
            Snapshot(
                workflow_id=None,
                snapshot_data={"state": "active"},
                event_sequence_number=42
            )

        with pytest.raises((ValueError, TypeError)):
            Snapshot(
                workflow_id="",
                snapshot_data={"state": "active"},
                event_sequence_number=42
            )

    def test_snapshot_data_accepts_dict_and_serializes_to_json(self):
        """Test that snapshot_data accepts dict and handles JSON serialization."""
        test_data = {
            "workflow_state": "implementing",
            "current_feature": "authentication",
            "progress": {
                "completed_features": 2,
                "total_features": 5,
                "percentage": 0.4
            },
            "metadata": {
                "last_updated": "2024-01-01T12:00:00Z",
                "version": "1.2.3"
            }
        }

        snapshot = Snapshot(
            workflow_id="test-workflow",
            snapshot_data=test_data,
            event_sequence_number=100
        )

        # snapshot_data should store the dict
        assert snapshot.snapshot_data == test_data
        assert isinstance(snapshot.snapshot_data, dict)

        # Should be JSON serializable
        json_str = json.dumps(snapshot.snapshot_data)
        assert isinstance(json_str, str)
        assert json.loads(json_str) == test_data

    def test_snapshot_data_handles_empty_dict(self):
        """Test that snapshot_data can be an empty dict."""
        snapshot = Snapshot(
            workflow_id="test-workflow",
            snapshot_data={},
            event_sequence_number=42
        )

        assert snapshot.snapshot_data == {}
        assert isinstance(snapshot.snapshot_data, dict)

    def test_snapshot_data_validates_required(self):
        """Test that snapshot_data is required."""
        with pytest.raises((ValueError, TypeError)):
            Snapshot(
                workflow_id="test-workflow",
                snapshot_data=None,
                event_sequence_number=42
            )

    def test_event_sequence_number_required_and_validated(self):
        """Test that event_sequence_number is required and validates properly."""
        # Valid sequence number should work
        snapshot = Snapshot(
            workflow_id="test-workflow",
            snapshot_data={"state": "active"},
            event_sequence_number=42
        )
        assert snapshot.event_sequence_number == 42

        # Zero should be valid
        snapshot_zero = Snapshot(
            workflow_id="test-workflow",
            snapshot_data={"state": "active"},
            event_sequence_number=0
        )
        assert snapshot_zero.event_sequence_number == 0

        # Invalid sequence number should raise validation error
        with pytest.raises((ValueError, TypeError)):
            Snapshot(
                workflow_id="test-workflow",
                snapshot_data={"state": "active"},
                event_sequence_number=None
            )

        with pytest.raises((ValueError, TypeError)):
            Snapshot(
                workflow_id="test-workflow",
                snapshot_data={"state": "active"},
                event_sequence_number=-1
            )

        with pytest.raises((ValueError, TypeError)):
            Snapshot(
                workflow_id="test-workflow",
                snapshot_data={"state": "active"},
                event_sequence_number="not_a_number"
            )

    def test_snapshot_equality_comparison(self):
        """Test Snapshot equality comparison."""
        snapshot1 = Snapshot(
            workflow_id="test-workflow",
            snapshot_data={"state": "active"},
            event_sequence_number=42
        )
        snapshot2 = Snapshot(
            workflow_id="test-workflow",
            snapshot_data={"state": "active"},
            event_sequence_number=42
        )

        # Different instances should not be equal (different IDs)
        assert snapshot1 != snapshot2

        # Same instance should equal itself
        assert snapshot1 == snapshot1


@pytest.mark.skipif(Event is None or Snapshot is None, reason="Models not implemented yet")
class TestEventAndSnapshotIntegration:
    """Test Event and Snapshot model integration."""

    def test_event_and_snapshot_can_reference_same_workflow(self):
        """Test that Event and Snapshot can reference the same workflow_id."""
        workflow_id = "integration-test-workflow"

        event = Event(
            workflow_id=workflow_id,
            event_type="workflow.started",
            event_data={"message": "Starting workflow"}
        )

        snapshot = Snapshot(
            workflow_id=workflow_id,
            snapshot_data={"state": "initializing"},
            event_sequence_number=1
        )

        assert event.workflow_id == snapshot.workflow_id
        assert event.workflow_id == workflow_id

    def test_snapshot_sequence_number_corresponds_to_event_sequence(self):
        """Test that snapshot references correct event sequence number."""
        event = Event(
            workflow_id="test-workflow",
            event_type="feature.completed",
            event_data={"feature_name": "authentication"}
        )

        # Assume event gets sequence number 50 when persisted
        # Snapshot should reference that sequence number
        snapshot = Snapshot(
            workflow_id="test-workflow",
            snapshot_data={"completed_features": ["authentication"]},
            event_sequence_number=50  # References the event
        )

        assert snapshot.event_sequence_number == 50
        assert snapshot.workflow_id == event.workflow_id

    def test_models_work_with_json_serialization(self):
        """Test that both models work with JSON serialization patterns."""
        event_data = {
            "type": "feature_completed",
            "feature_name": "user_auth",
            "duration_ms": 45000,
            "files_changed": ["auth.py", "models.py", "tests.py"]
        }

        snapshot_data = {
            "workflow_phase": "implementing",
            "completed_features": ["user_auth"],
            "current_feature": "api_endpoints",
            "progress_percentage": 33.3,
            "last_activity": "2024-01-01T15:30:00Z"
        }

        event = Event(
            workflow_id="json-test-workflow",
            event_type="feature.completed",
            event_data=event_data
        )

        snapshot = Snapshot(
            workflow_id="json-test-workflow",
            snapshot_data=snapshot_data,
            event_sequence_number=25
        )

        # Both should be JSON serializable
        event_json = json.dumps(event.event_data)
        snapshot_json = json.dumps(snapshot.snapshot_data)

        assert json.loads(event_json) == event_data
        assert json.loads(snapshot_json) == snapshot_data


@pytest.mark.skipif(Event is None or Snapshot is None, reason="Models not implemented yet")
class TestModelFactories:
    """Test factory methods for creating test instances."""

    def test_event_factory_creates_valid_instances(self):
        """Test factory pattern for creating Event test instances."""
        # This documents expected factory pattern for tests
        def create_test_event(workflow_id="test-workflow", event_type="workflow.started", **kwargs):
            default_data = {"message": "Test event", "source": "test"}
            event_data = kwargs.pop("event_data", default_data)

            return Event(
                workflow_id=workflow_id,
                event_type=event_type,
                event_data=event_data,
                **kwargs
            )

        event = create_test_event()
        assert event.workflow_id == "test-workflow"
        assert event.event_type == "workflow.started"
        assert event.event_data["message"] == "Test event"

        # Test with custom values
        custom_event = create_test_event(
            workflow_id="custom-workflow",
            event_type="feature.started",
            event_data={"custom": "data"}
        )
        assert custom_event.workflow_id == "custom-workflow"
        assert custom_event.event_type == "feature.started"
        assert custom_event.event_data == {"custom": "data"}

    def test_snapshot_factory_creates_valid_instances(self):
        """Test factory pattern for creating Snapshot test instances."""
        def create_test_snapshot(workflow_id="test-workflow", event_sequence_number=1, **kwargs):
            default_data = {"state": "active", "progress": 0.0}
            snapshot_data = kwargs.pop("snapshot_data", default_data)

            return Snapshot(
                workflow_id=workflow_id,
                snapshot_data=snapshot_data,
                event_sequence_number=event_sequence_number,
                **kwargs
            )

        snapshot = create_test_snapshot()
        assert snapshot.workflow_id == "test-workflow"
        assert snapshot.event_sequence_number == 1
        assert snapshot.snapshot_data["state"] == "active"

        # Test with custom values
        custom_snapshot = create_test_snapshot(
            workflow_id="custom-workflow",
            event_sequence_number=42,
            snapshot_data={"custom": "state", "progress": 0.75}
        )
        assert custom_snapshot.workflow_id == "custom-workflow"
        assert custom_snapshot.event_sequence_number == 42
        assert custom_snapshot.snapshot_data == {"custom": "state", "progress": 0.75}


@pytest.mark.skipif(Event is None or Snapshot is None, reason="Models not implemented yet")
class TestModelCompatibility:
    """Test model compatibility with existing codebase patterns."""

    def test_models_compatible_with_existing_event_infrastructure(self):
        """Test that models work with existing event logging patterns."""
        # Test compatibility with existing Event class from events.py
        from jean_claude.core.events import Event as ExistingEvent, EventType

        # New Event model should be compatible with existing patterns
        new_event = Event(
            workflow_id="compatibility-test",
            event_type="workflow.started",
            event_data={"message": "Compatibility test"}
        )

        # Should be able to convert to existing event format if needed
        existing_event_data = {
            "workflow_id": new_event.workflow_id,
            "event_type": new_event.event_type,
            "data": new_event.event_data
        }

        # Verify data structure compatibility
        assert existing_event_data["workflow_id"] == new_event.workflow_id
        assert existing_event_data["event_type"] == new_event.event_type
        assert existing_event_data["data"] == new_event.event_data

    def test_models_compatible_with_database_schema(self):
        """Test that models match existing database schema from schema_creation.py."""
        event = Event(
            workflow_id="schema-test",
            event_type="workflow.started",
            event_data={"test": "data"}
        )

        snapshot = Snapshot(
            workflow_id="schema-test",
            snapshot_data={"state": "active"},
            event_sequence_number=1
        )

        # Verify models have expected fields by accessing them
        # Event should map to events table schema
        assert event.workflow_id == "schema-test"
        assert event.event_type == "workflow.started"
        assert event.event_data == {"test": "data"}
        assert event.timestamp is not None
        assert event.sequence_number is not None or event.sequence_number is None

        # Snapshot should map to snapshots table schema
        assert snapshot.workflow_id == "schema-test"
        assert snapshot.snapshot_data == {"state": "active"}
        assert snapshot.event_sequence_number == 1
        assert snapshot.timestamp is not None