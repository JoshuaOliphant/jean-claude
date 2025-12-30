# ABOUTME: Tests for JSON serialization/deserialization of WorkflowEvent
# ABOUTME: Validates datetime and UUID handling in JSON serialization

"""Tests for JSON serialization/deserialization of WorkflowEvent.

Tests JSON serialization and deserialization including:
- Datetime field serialization to ISO format
- UUID field serialization to string format
- Round-trip serialization (serialize then deserialize)
- Data integrity after serialization
- Snapshot state field serialization
"""

import json
from datetime import datetime
from uuid import uuid4

import pytest

from jean_claude.core.workflow_event import WorkflowEvent


class TestWorkflowEventJSONSerialization:
    """Test JSON serialization for WorkflowEvent model."""

    def test_workflow_event_serializes_to_json(self):
        """Test that WorkflowEvent can be serialized to JSON string."""
        event = WorkflowEvent(
            workflow_id="test-workflow-123",
            event_type="workflow.started",
            data={"message": "Starting workflow", "user": "test_user"}
        )

        # Should be able to convert to JSON
        json_str = event.model_dump_json()

        # Should be valid JSON
        json_data = json.loads(json_str)

        # Should contain all fields
        assert "event_id" in json_data
        assert "workflow_id" in json_data
        assert "event_type" in json_data
        assert "timestamp" in json_data
        assert "data" in json_data

    def test_workflow_event_datetime_serialized_as_iso_format(self):
        """Test that datetime field is serialized in ISO format."""
        event = WorkflowEvent(
            workflow_id="test-workflow-123",
            event_type="workflow.started",
            data={"message": "Starting"}
        )

        json_str = event.model_dump_json()
        json_data = json.loads(json_str)

        # Timestamp should be ISO format string
        timestamp_str = json_data["timestamp"]
        assert isinstance(timestamp_str, str)

        # Should be parseable back to datetime
        parsed_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        assert isinstance(parsed_dt, datetime)

    def test_workflow_event_uuid_serialized_as_string(self):
        """Test that UUID field is serialized as string."""
        event = WorkflowEvent(
            workflow_id="test-workflow-123",
            event_type="workflow.started",
            data={"message": "Starting"}
        )

        json_str = event.model_dump_json()
        json_data = json.loads(json_str)

        # Event ID should be a string
        event_id_str = json_data["event_id"]
        assert isinstance(event_id_str, str)

        # Should be a valid UUID format
        from uuid import UUID
        UUID(event_id_str)  # Should not raise ValueError

    def test_workflow_event_data_field_preserved_in_json(self):
        """Test that complex data field is correctly serialized."""
        complex_data = {
            "message": "Complex event",
            "metadata": {
                "user": "test_user",
                "session_id": "session-123"
            },
            "count": 42,
            "active": True
        }

        event = WorkflowEvent(
            workflow_id="test-workflow-123",
            event_type="workflow.data.updated",
            data=complex_data
        )

        json_str = event.model_dump_json()
        json_data = json.loads(json_str)

        # Data should be preserved exactly
        assert json_data["data"] == complex_data

    def test_workflow_event_roundtrip_serialization(self):
        """Test that WorkflowEvent can be serialized and deserialized without data loss."""
        original_event = WorkflowEvent(
            workflow_id="test-workflow-456",
            event_type="workflow.completed",
            data={"result": "success", "duration_ms": 1500}
        )

        # Serialize to JSON
        json_str = original_event.model_dump_json()

        # Deserialize back to WorkflowEvent
        deserialized_event = WorkflowEvent.model_validate_json(json_str)

        # Should have same values
        assert deserialized_event.event_id == original_event.event_id
        assert deserialized_event.workflow_id == original_event.workflow_id
        assert deserialized_event.event_type == original_event.event_type
        assert deserialized_event.data == original_event.data

        # Timestamps should be very close (within 1 second)
        time_diff = abs((deserialized_event.timestamp - original_event.timestamp).total_seconds())
        assert time_diff < 1.0

    def test_workflow_event_deserialize_from_json_string(self):
        """Test that WorkflowEvent can be created from JSON string."""
        json_str = json.dumps({
            "event_id": str(uuid4()),
            "workflow_id": "workflow-789",
            "event_type": "workflow.paused",
            "timestamp": datetime.now().isoformat(),
            "data": {"reason": "waiting_for_input"}
        })

        # Should deserialize successfully
        event = WorkflowEvent.model_validate_json(json_str)

        assert event.workflow_id == "workflow-789"
        assert event.event_type == "workflow.paused"
        assert event.data == {"reason": "waiting_for_input"}

    def test_workflow_event_to_dict_preserves_types(self):
        """Test that model_dump() preserves Python types (UUID, datetime)."""
        event = WorkflowEvent(
            workflow_id="test-workflow-123",
            event_type="workflow.started",
            data={"message": "Starting"}
        )

        # Get dict representation
        event_dict = event.model_dump()

        # UUID should stay as UUID object
        from uuid import UUID
        assert isinstance(event_dict["event_id"], UUID)

        # Datetime should stay as datetime object
        assert isinstance(event_dict["timestamp"], datetime)

        # Data should be dict
        assert isinstance(event_dict["data"], dict)

    def test_workflow_event_json_schema_generation(self):
        """Test that WorkflowEvent can generate JSON schema."""
        # Should be able to generate JSON schema
        schema = WorkflowEvent.model_json_schema()

        # Schema should have properties for all fields
        assert "properties" in schema
        assert "event_id" in schema["properties"]
        assert "workflow_id" in schema["properties"]
        assert "event_type" in schema["properties"]
        assert "timestamp" in schema["properties"]
        assert "data" in schema["properties"]

    def test_workflow_event_custom_json_encoders(self):
        """Test that custom JSON encoding works for datetime and UUID."""
        event = WorkflowEvent(
            workflow_id="test-workflow-123",
            event_type="workflow.started",
            data={"nested_datetime": "2023-01-01T00:00:00"}
        )

        # Should serialize without errors
        json_str = event.model_dump_json()
        json_data = json.loads(json_str)

        # All fields should be JSON-serializable strings/dicts
        assert isinstance(json_data["event_id"], str)
        assert isinstance(json_data["timestamp"], str)
        assert isinstance(json_data["workflow_id"], str)
        assert isinstance(json_data["event_type"], str)
        assert isinstance(json_data["data"], dict)
