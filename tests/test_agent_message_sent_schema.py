# ABOUTME: Test suite for agent message sent schema
# ABOUTME: Tests Pydantic schema for agent.message.sent events with validation

"""Test suite for agent message sent schema.

Tests the Pydantic schema for agent.message.sent events with fields:
- from_agent: ID of the sending agent
- to_agent: ID of the receiving agent
- content: Message content/payload
- priority: Message priority level
- correlation_id: Unique identifier for tracking
- awaiting_response: Whether sender expects a response
- message_type: Type/category of the message
"""

import pytest
from datetime import datetime
from uuid import uuid4
from pydantic import ValidationError

from jean_claude.core.events import Event, EventType
from jean_claude.core.event_schemas import (
    AgentMessageSentData,
    MessageType,
    MessagePriority
)


class TestAgentMessageSentSchema:
    """Test the Pydantic schema for agent.message.sent events."""

    def test_agent_message_sent_schema_alias(self):
        """Test that AgentMessageSentSchema is properly aliased to AgentMessageSentData."""
        from jean_claude.core.events import AgentMessageSentSchema

        # Verify the alias is correctly set up
        assert AgentMessageSentSchema is AgentMessageSentData

        # Test that the alias works for instantiation
        schema = AgentMessageSentSchema(
            from_agent="test-agent",
            to_agent="target-agent",
            content="Test alias functionality",
            message_type=MessageType.NOTIFICATION
        )

        # Should create an instance of the actual class
        assert isinstance(schema, AgentMessageSentData)
        assert schema.from_agent == "test-agent"
        assert schema.to_agent == "target-agent"

    def test_agent_message_sent_schema_creation(self):
        """Test creating AgentMessageSentSchema with all required fields."""
        # Test using the alias AgentMessageSentSchema (should be same as AgentMessageSentData)
        from jean_claude.core.events import AgentMessageSentSchema

        schema_data = AgentMessageSentSchema(
            from_agent="agent-1",
            to_agent="agent-2",
            content="Hello, please process this task",
            priority=MessagePriority.NORMAL,
            awaiting_response=True,
            message_type=MessageType.TASK_ASSIGNMENT
        )

        assert schema_data.from_agent == "agent-1"
        assert schema_data.to_agent == "agent-2"
        assert schema_data.content == "Hello, please process this task"
        assert schema_data.priority == MessagePriority.NORMAL
        assert schema_data.awaiting_response is True
        assert schema_data.message_type == MessageType.TASK_ASSIGNMENT
        assert schema_data.correlation_id  # Auto-generated UUID

    def test_agent_message_sent_schema_defaults(self):
        """Test schema with default values."""
        schema_data = AgentMessageSentData(
            from_agent="agent-1",
            to_agent="agent-2",
            content="Simple message",
            message_type=MessageType.NOTIFICATION
        )

        # Test default values
        assert schema_data.priority == MessagePriority.NORMAL
        assert schema_data.awaiting_response is False
        assert schema_data.correlation_id  # Auto-generated
        assert len(schema_data.correlation_id) > 10  # UUID should be long

    def test_agent_message_sent_schema_with_event(self):
        """Test using AgentMessageSentData with Event model."""
        schema_data = AgentMessageSentData(
            from_agent="agent-1",
            to_agent="agent-2",
            content="Hello, please process this task",
            message_type=MessageType.TASK_ASSIGNMENT
        )

        event = Event(
            workflow_id="test-workflow",
            event_type=EventType.AGENT_MESSAGE_SENT,
            data=schema_data.model_dump()
        )

        assert event.event_type == EventType.AGENT_MESSAGE_SENT
        assert event.data["from_agent"] == "agent-1"
        assert event.data["to_agent"] == "agent-2"
        assert event.data["content"] == "Hello, please process this task"
        assert event.data["priority"] == MessagePriority.NORMAL  # Default
        assert event.data["awaiting_response"] is False  # Default
        assert event.data["message_type"] == MessageType.TASK_ASSIGNMENT

    def test_agent_message_sent_schema_priority_levels(self):
        """Test schema with different priority levels."""
        priorities = [
            MessagePriority.LOW,
            MessagePriority.NORMAL,
            MessagePriority.URGENT
        ]

        for priority in priorities:
            schema_data = AgentMessageSentData(
                from_agent="sender",
                to_agent="receiver",
                content=f"Message with {priority} priority",
                priority=priority,
                awaiting_response=priority == MessagePriority.URGENT,
                message_type=MessageType.NOTIFICATION
            )

            assert schema_data.priority == priority
            assert schema_data.awaiting_response == (priority == MessagePriority.URGENT)

    def test_agent_message_sent_schema_different_message_types(self):
        """Test schema with various message types."""
        message_types = [
            MessageType.HELP_REQUEST,
            MessageType.NOTIFICATION,
            MessageType.TASK_ASSIGNMENT,
            MessageType.STATUS_UPDATE,
            MessageType.RESPONSE
        ]

        for msg_type in message_types:
            schema_data = AgentMessageSentData(
                from_agent="sender",
                to_agent="receiver",
                content=f"Message of type {msg_type}",
                awaiting_response=msg_type in [MessageType.HELP_REQUEST, MessageType.TASK_ASSIGNMENT],
                message_type=msg_type
            )

            assert schema_data.message_type == msg_type

    def test_agent_message_sent_schema_correlation_id_validation(self):
        """Test correlation_id validation and auto-generation."""
        # Test auto-generated correlation_id
        schema_data = AgentMessageSentData(
            from_agent="sender",
            to_agent="receiver",
            content="Test message",
            message_type=MessageType.NOTIFICATION
        )
        assert schema_data.correlation_id
        assert len(schema_data.correlation_id) > 3

        # Test custom correlation_id
        custom_id = "custom-msg-123"
        schema_data = AgentMessageSentData(
            from_agent="sender",
            to_agent="receiver",
            content="Test message",
            correlation_id=custom_id,
            message_type=MessageType.NOTIFICATION
        )
        assert schema_data.correlation_id == custom_id

        # Test correlation_id validation - too short
        with pytest.raises(ValidationError, match="at least 3 characters"):
            AgentMessageSentData(
                from_agent="sender",
                to_agent="receiver",
                content="Test message",
                correlation_id="xx",
                message_type=MessageType.NOTIFICATION
            )


class TestAgentMessageSentSchemaValidation:
    """Test validation behavior of the AgentMessageSentData schema."""

    def test_required_field_validation(self):
        """Test that schema properly validates required fields."""
        # Test missing from_agent
        with pytest.raises(ValidationError, match="from_agent"):
            AgentMessageSentData(
                to_agent="receiver",
                content="Test message",
                message_type=MessageType.NOTIFICATION
            )

        # Test missing to_agent
        with pytest.raises(ValidationError, match="to_agent"):
            AgentMessageSentData(
                from_agent="sender",
                content="Test message",
                message_type=MessageType.NOTIFICATION
            )

        # Test missing content
        with pytest.raises(ValidationError, match="content"):
            AgentMessageSentData(
                from_agent="sender",
                to_agent="receiver",
                message_type=MessageType.NOTIFICATION
            )

        # Test missing message_type
        with pytest.raises(ValidationError, match="message_type"):
            AgentMessageSentData(
                from_agent="sender",
                to_agent="receiver",
                content="Test message"
            )

    def test_empty_string_validation(self):
        """Test validation of empty or whitespace-only strings."""
        # Test empty from_agent
        with pytest.raises(ValidationError, match="cannot be empty"):
            AgentMessageSentData(
                from_agent="",
                to_agent="receiver",
                content="Test message",
                message_type=MessageType.NOTIFICATION
            )

        # Test whitespace-only to_agent
        with pytest.raises(ValidationError, match="cannot be empty"):
            AgentMessageSentData(
                from_agent="sender",
                to_agent="   ",
                content="Test message",
                message_type=MessageType.NOTIFICATION
            )

        # Test whitespace-only content
        with pytest.raises(ValidationError, match="cannot be empty"):
            AgentMessageSentData(
                from_agent="sender",
                to_agent="receiver",
                content="   ",
                message_type=MessageType.NOTIFICATION
            )

    def test_agent_identifier_validation(self):
        """Test agent identifier validation for invalid characters."""
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']

        for char in invalid_chars:
            # Test invalid from_agent
            with pytest.raises(ValidationError, match="cannot contain characters"):
                AgentMessageSentData(
                    from_agent=f"invalid{char}agent",
                    to_agent="receiver",
                    content="Test message",
                    message_type=MessageType.NOTIFICATION
                )

            # Test invalid to_agent
            with pytest.raises(ValidationError, match="cannot contain characters"):
                AgentMessageSentData(
                    from_agent="sender",
                    to_agent=f"invalid{char}agent",
                    content="Test message",
                    message_type=MessageType.NOTIFICATION
                )

    def test_extra_fields_forbidden(self):
        """Test that extra fields are not allowed (strict validation)."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            AgentMessageSentData(
                from_agent="sender",
                to_agent="receiver",
                content="Test message",
                message_type=MessageType.NOTIFICATION,
                extra_field="not allowed"  # This should fail
            )

    def test_field_trimming(self):
        """Test that string fields are properly trimmed."""
        schema_data = AgentMessageSentData(
            from_agent="  agent-1  ",
            to_agent="  agent-2  ",
            content="  Test message  ",
            message_type=MessageType.NOTIFICATION
        )

        assert schema_data.from_agent == "agent-1"
        assert schema_data.to_agent == "agent-2"
        assert schema_data.content == "Test message"


class TestAgentMessageSentEventIntegration:
    """Test integration of agent message sent schema with event system."""

    def test_agent_message_sent_event_serialization(self):
        """Test that agent message sent events serialize correctly."""
        schema_data = AgentMessageSentData(
            from_agent="agent-1",
            to_agent="agent-2",
            content="Serialization test message",
            priority=MessagePriority.URGENT,
            awaiting_response=True,
            message_type=MessageType.HELP_REQUEST
        )

        event = Event(
            workflow_id="test-workflow",
            event_type=EventType.AGENT_MESSAGE_SENT,
            data=schema_data.model_dump()
        )

        # Test JSON serialization
        event_dict = event.model_dump(mode="json")

        assert event_dict["event_type"] == "agent.message.sent"
        assert event_dict["data"]["from_agent"] == "agent-1"
        assert event_dict["data"]["to_agent"] == "agent-2"
        assert event_dict["data"]["awaiting_response"] is True
        assert event_dict["data"]["priority"] == "urgent"
        assert event_dict["data"]["message_type"] == "help_request"

    def test_agent_message_sent_event_metadata(self):
        """Test event metadata is properly set."""
        schema_data = AgentMessageSentData(
            from_agent="workflow-agent",
            to_agent="coordinator",
            content="Feature implementation completed",
            priority=MessagePriority.NORMAL,
            message_type=MessageType.STATUS_UPDATE
        )

        event = Event(
            workflow_id="workflow-456",
            event_type=EventType.AGENT_MESSAGE_SENT,
            data=schema_data.model_dump()
        )

        assert event.workflow_id == "workflow-456"
        assert event.event_type == EventType.AGENT_MESSAGE_SENT
        assert isinstance(event.timestamp, datetime)
        assert str(event.id)  # UUID should be convertible to string

    def test_agent_message_sent_round_trip(self):
        """Test creating schema, converting to event, and accessing data."""
        correlation_id = str(uuid4())

        schema_data = AgentMessageSentData(
            from_agent="task-processor",
            to_agent="status-monitor",
            content="Task processing completed successfully",
            priority=MessagePriority.NORMAL,
            correlation_id=correlation_id,
            awaiting_response=False,
            message_type=MessageType.STATUS_UPDATE
        )

        event = Event(
            workflow_id="progress-tracking",
            event_type=EventType.AGENT_MESSAGE_SENT,
            data=schema_data.model_dump()
        )

        # Test accessing the data back through event
        assert event.data["correlation_id"] == correlation_id
        assert event.data["from_agent"] == "task-processor"
        assert event.data["to_agent"] == "status-monitor"
        assert event.data["message_type"] == MessageType.STATUS_UPDATE
        assert event.data["priority"] == MessagePriority.NORMAL