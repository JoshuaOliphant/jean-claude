# ABOUTME: Test suite for WorkflowEvent Pydantic model
# ABOUTME: Tests model creation, validation, immutability, and auto-generation

"""Test suite for WorkflowEvent model.

Tests the WorkflowEvent Pydantic model with frozen=True, validating:
- Required fields: event_id (UUID), workflow_id (str), event_type (str), timestamp (datetime), data (dict)
- Auto-generation of UUID and timestamp
- Field validation for required strings
- Immutability with frozen=True
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import ValidationError

# Import will fail until we implement the model - that's expected in TDD
try:
    from jean_claude.core.workflow_event import WorkflowEvent
except ImportError:
    # Allow tests to be written before implementation
    WorkflowEvent = None


@pytest.mark.skipif(WorkflowEvent is None, reason="WorkflowEvent not implemented yet")
class TestWorkflowEventCreation:
    """Test WorkflowEvent model creation and basic functionality."""

    def test_create_workflow_event_with_all_fields(self):
        """Test creating a WorkflowEvent with all required fields."""
        event_id = uuid4()
        timestamp = datetime.now()

        event = WorkflowEvent(
            event_id=event_id,
            workflow_id="test-workflow-123",
            event_type="workflow.started",
            timestamp=timestamp,
            data={"key": "value", "count": 42}
        )

        assert event.event_id == event_id
        assert event.workflow_id == "test-workflow-123"
        assert event.event_type == "workflow.started"
        assert event.timestamp == timestamp
        assert event.data == {"key": "value", "count": 42}

    def test_create_workflow_event_with_auto_generated_fields(self):
        """Test creating WorkflowEvent with auto-generated event_id and timestamp."""
        event = WorkflowEvent(
            workflow_id="auto-workflow",
            event_type="test.event",
            data={"test": True}
        )

        # Should auto-generate UUID for event_id
        assert isinstance(event.event_id, UUID)

        # Should auto-generate timestamp
        assert isinstance(event.timestamp, datetime)

        # Should be recent (within last minute)
        time_diff = datetime.now() - event.timestamp
        assert time_diff.total_seconds() < 60

    def test_create_workflow_event_minimal(self):
        """Test creating WorkflowEvent with minimal required fields."""
        event = WorkflowEvent(
            workflow_id="minimal-workflow",
            event_type="minimal.event",
            data={}
        )

        assert event.workflow_id == "minimal-workflow"
        assert event.event_type == "minimal.event"
        assert event.data == {}
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.timestamp, datetime)


@pytest.mark.skipif(WorkflowEvent is None, reason="WorkflowEvent not implemented yet")
class TestWorkflowEventValidation:
    """Test WorkflowEvent field validation."""

    def test_workflow_id_required(self):
        """Test that workflow_id is required."""
        with pytest.raises(ValueError, match="workflow_id cannot be empty"):
            WorkflowEvent(
                workflow_id="",
                event_type="test.event",
                data={}
            )

    def test_workflow_id_cannot_be_whitespace_only(self):
        """Test that workflow_id cannot be only whitespace."""
        with pytest.raises(ValueError, match="workflow_id cannot be empty"):
            WorkflowEvent(
                workflow_id="   ",
                event_type="test.event",
                data={}
            )

    def test_event_type_required(self):
        """Test that event_type is required."""
        with pytest.raises(ValueError, match="event_type cannot be empty"):
            WorkflowEvent(
                workflow_id="test-workflow",
                event_type="",
                data={}
            )

    def test_event_type_cannot_be_whitespace_only(self):
        """Test that event_type cannot be only whitespace."""
        with pytest.raises(ValueError, match="event_type cannot be empty"):
            WorkflowEvent(
                workflow_id="test-workflow",
                event_type="   ",
                data={}
            )

    def test_data_field_is_required(self):
        """Test that data field is required (not None)."""
        # This should work - empty dict is valid
        event = WorkflowEvent(
            workflow_id="test-workflow",
            event_type="test.event",
            data={}
        )
        assert event.data == {}

        # But None should be rejected by Pydantic
        with pytest.raises((ValueError, TypeError)):
            WorkflowEvent(
                workflow_id="test-workflow",
                event_type="test.event"
                # Missing data field
            )


@pytest.mark.skipif(WorkflowEvent is None, reason="WorkflowEvent not implemented yet")
class TestWorkflowEventImmutability:
    """Test WorkflowEvent immutability with frozen=True."""

    def test_workflow_event_is_immutable(self):
        """Test that WorkflowEvent fields cannot be modified after creation."""
        event = WorkflowEvent(
            workflow_id="immutable-test",
            event_type="test.immutable",
            data={"original": "value"}
        )

        # Attempt to modify fields should raise ValidationError (Pydantic v2 frozen behavior)
        with pytest.raises(ValidationError, match="Instance is frozen"):
            event.workflow_id = "modified-workflow"

        with pytest.raises(ValidationError, match="Instance is frozen"):
            event.event_type = "modified.type"

        with pytest.raises(ValidationError, match="Instance is frozen"):
            event.data = {"modified": "data"}

        with pytest.raises(ValidationError, match="Instance is frozen"):
            event.event_id = uuid4()

        with pytest.raises(ValidationError, match="Instance is frozen"):
            event.timestamp = datetime.now()

    def test_data_dict_mutability_note(self):
        """Test that while the data field reference is immutable, the dict contents may be mutable.

        Note: This test documents the behavior - the data dict itself may still be
        mutable even though the field reference is frozen. For true immutability,
        the dict would need to be frozen separately.
        """
        event = WorkflowEvent(
            workflow_id="dict-test",
            event_type="test.dict",
            data={"mutable": "original"}
        )

        # The field reference cannot be changed (Pydantic v2 raises ValidationError)
        with pytest.raises(ValidationError, match="Instance is frozen"):
            event.data = {"different": "dict"}

        # But the dict contents might still be mutable (documenting current behavior)
        # This could be restricted further if needed by using a frozen dict type
        original_data_id = id(event.data)
        event.data["mutable"] = "modified"  # This may or may not work depending on implementation

        # The reference should be the same even if contents changed
        assert id(event.data) == original_data_id


@pytest.mark.skipif(WorkflowEvent is None, reason="WorkflowEvent not implemented yet")
class TestWorkflowEventDataTypes:
    """Test WorkflowEvent field data types and constraints."""

    def test_event_id_is_uuid(self):
        """Test that event_id field is properly typed as UUID."""
        # Auto-generated should be UUID
        event = WorkflowEvent(
            workflow_id="uuid-test",
            event_type="test.uuid",
            data={}
        )
        assert isinstance(event.event_id, UUID)

        # Explicitly provided UUID should work
        custom_uuid = uuid4()
        event2 = WorkflowEvent(
            event_id=custom_uuid,
            workflow_id="uuid-test-2",
            event_type="test.uuid",
            data={}
        )
        assert event2.event_id == custom_uuid

    def test_timestamp_is_datetime(self):
        """Test that timestamp field is properly typed as datetime."""
        # Auto-generated should be datetime
        event = WorkflowEvent(
            workflow_id="datetime-test",
            event_type="test.datetime",
            data={}
        )
        assert isinstance(event.timestamp, datetime)

        # Explicitly provided datetime should work
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        event2 = WorkflowEvent(
            timestamp=custom_time,
            workflow_id="datetime-test-2",
            event_type="test.datetime",
            data={}
        )
        assert event2.timestamp == custom_time

    def test_data_is_dict(self):
        """Test that data field properly accepts dict types."""
        # Empty dict
        event1 = WorkflowEvent(
            workflow_id="dict-test",
            event_type="test.dict",
            data={}
        )
        assert event1.data == {}
        assert isinstance(event1.data, dict)

        # Nested dict with various types
        complex_data = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "nested": {"inner": "value"}
        }
        event2 = WorkflowEvent(
            workflow_id="dict-test-2",
            event_type="test.dict",
            data=complex_data
        )
        assert event2.data == complex_data