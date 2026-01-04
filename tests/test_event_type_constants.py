# ABOUTME: Test suite for new agent message event type constants
# ABOUTME: Tests AGENT_MESSAGE_SENT, AGENT_MESSAGE_ACKNOWLEDGED, AGENT_MESSAGE_COMPLETED

"""Test suite for agent message event type constants.

Tests the new agent messaging event type constants added to the EventType enum:
- AGENT_MESSAGE_SENT: When an agent sends a message
- AGENT_MESSAGE_ACKNOWLEDGED: When a message is acknowledged
- AGENT_MESSAGE_COMPLETED: When a message request is completed
"""

import pytest
from jean_claude.core.events import EventType, Event


class TestAgentMessageEventTypes:
    """Test new agent message event type constants."""

    def test_agent_message_sent_constant_exists(self):
        """Test that AGENT_MESSAGE_SENT constant exists and has correct value."""
        assert hasattr(EventType, 'AGENT_MESSAGE_SENT')
        assert EventType.AGENT_MESSAGE_SENT == "agent.message.sent"

    def test_agent_message_acknowledged_constant_exists(self):
        """Test that AGENT_MESSAGE_ACKNOWLEDGED constant exists and has correct value."""
        assert hasattr(EventType, 'AGENT_MESSAGE_ACKNOWLEDGED')
        assert EventType.AGENT_MESSAGE_ACKNOWLEDGED == "agent.message.acknowledged"

    def test_agent_message_completed_constant_exists(self):
        """Test that AGENT_MESSAGE_COMPLETED constant exists and has correct value."""
        assert hasattr(EventType, 'AGENT_MESSAGE_COMPLETED')
        assert EventType.AGENT_MESSAGE_COMPLETED == "agent.message.completed"

    def test_agent_message_constants_are_strings(self):
        """Test that all agent message constants are string values."""
        assert isinstance(EventType.AGENT_MESSAGE_SENT, str)
        assert isinstance(EventType.AGENT_MESSAGE_ACKNOWLEDGED, str)
        assert isinstance(EventType.AGENT_MESSAGE_COMPLETED, str)

    def test_agent_message_constants_follow_naming_pattern(self):
        """Test that constants follow the agent.* namespace pattern."""
        agent_message_types = [
            EventType.AGENT_MESSAGE_SENT,
            EventType.AGENT_MESSAGE_ACKNOWLEDGED,
            EventType.AGENT_MESSAGE_COMPLETED
        ]

        for event_type in agent_message_types:
            assert event_type.startswith("agent.")
            assert "message" in event_type

    def test_agent_message_constants_are_unique(self):
        """Test that each agent message constant has a unique value."""
        agent_message_types = [
            EventType.AGENT_MESSAGE_SENT,
            EventType.AGENT_MESSAGE_ACKNOWLEDGED,
            EventType.AGENT_MESSAGE_COMPLETED
        ]

        # Check that all values are unique
        assert len(set(agent_message_types)) == len(agent_message_types)


class TestAgentMessageEventTypeUsage:
    """Test that agent message event types can be used with Event model."""

    def test_create_event_with_agent_message_sent(self):
        """Test creating Event with AGENT_MESSAGE_SENT type."""
        event = Event(
            workflow_id="test-workflow",
            event_type=EventType.AGENT_MESSAGE_SENT,
            data={
                "from_agent": "agent-1",
                "to_agent": "agent-2",
                "content": "Test message",
                "priority": "normal"
            }
        )

        assert event.event_type == EventType.AGENT_MESSAGE_SENT
        assert event.workflow_id == "test-workflow"
        assert event.data["from_agent"] == "agent-1"

    def test_create_event_with_agent_message_acknowledged(self):
        """Test creating Event with AGENT_MESSAGE_ACKNOWLEDGED type."""
        event = Event(
            workflow_id="test-workflow",
            event_type=EventType.AGENT_MESSAGE_ACKNOWLEDGED,
            data={
                "correlation_id": "msg-123",
                "from_agent": "agent-2",
                "acknowledged_at": "2024-01-01T12:00:00Z"
            }
        )

        assert event.event_type == EventType.AGENT_MESSAGE_ACKNOWLEDGED
        assert event.data["correlation_id"] == "msg-123"

    def test_create_event_with_agent_message_completed(self):
        """Test creating Event with AGENT_MESSAGE_COMPLETED type."""
        event = Event(
            workflow_id="test-workflow",
            event_type=EventType.AGENT_MESSAGE_COMPLETED,
            data={
                "correlation_id": "msg-123",
                "from_agent": "agent-2",
                "result": "Task completed successfully",
                "success": True
            }
        )

        assert event.event_type == EventType.AGENT_MESSAGE_COMPLETED
        assert event.data["success"] is True


class TestEventTypeEnumCompleteness:
    """Test that agent message types are properly included in EventType enum."""

    def test_agent_message_types_in_enum_values(self):
        """Test that agent message types appear in EventType values."""
        enum_values = [e.value for e in EventType]

        assert "agent.message.sent" in enum_values
        assert "agent.message.acknowledged" in enum_values
        assert "agent.message.completed" in enum_values

    def test_agent_message_types_enumerable(self):
        """Test that agent message types can be enumerated from EventType."""
        all_event_types = list(EventType)

        # Find agent message types
        agent_message_types = [
            et for et in all_event_types
            if et.value.startswith("agent.message.")
        ]

        assert len(agent_message_types) == 3

        # Check that our expected types are present
        agent_message_values = {et.value for et in agent_message_types}
        expected_values = {
            "agent.message.sent",
            "agent.message.acknowledged",
            "agent.message.completed"
        }

        assert agent_message_values == expected_values

    def test_existing_agent_events_still_present(self):
        """Test that existing agent.* event types are still present."""
        enum_values = [e.value for e in EventType]

        # These should still exist from the original EventType
        assert "agent.tool_use" in enum_values
        assert "agent.test_result" in enum_values
        assert "agent.error" in enum_values