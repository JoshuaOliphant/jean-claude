# ABOUTME: Test suite for agent message sent handler implementation
# ABOUTME: Tests apply_agent_message_sent() method to add messages to inbox/outbox with proper state initialization

"""Test suite for agent message sent handler implementation.

This module tests the apply_agent_message_sent() method implementation that processes
agent.message.sent events to update the mailbox projection state by:
- Adding messages to inbox when the current agent is the recipient (to_agent matches)
- Adding messages to outbox when the current agent is the sender (from_agent matches)
- Properly initializing state with InboxMessage and OutboxMessage models
- Handling event data validation and state management

The tests cover both inbox and outbox scenarios, proper message transformation,
and edge cases for state management.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from jean_claude.core.mailbox_projection_builder import MailboxProjectionBuilder
from jean_claude.core.mailbox_message_models import InboxMessage, OutboxMessage
from jean_claude.core.message import Message


class TestAgentMessageSentHandler:
    """Test the apply_agent_message_sent method implementation."""

    @pytest.fixture
    def builder(self):
        """Provide a MailboxProjectionBuilder instance."""
        return MailboxProjectionBuilder()

    @pytest.fixture
    def current_agent_id(self):
        """Provide the current agent ID for testing."""
        return "current-agent"

    @pytest.fixture
    def initial_state(self):
        """Provide initial mailbox state."""
        return {
            'inbox': [],
            'outbox': [],
            'conversation_history': []
        }

    @pytest.fixture
    def sample_event_data(self, message_factory):
        """Provide sample agent.message.sent event data."""
        # Create a message using the factory
        msg = message_factory(
            from_agent="sender-agent",
            to_agent="recipient-agent",
            subject="Test Message",
            body="Test message content"
        )

        return {
            'event_id': 'evt-123',
            'message': msg,
            'sent_at': datetime.now()
        }

    def test_apply_agent_message_sent_adds_to_inbox_when_recipient(
        self, builder, initial_state, sample_event_data, current_agent_id
    ):
        """Test that apply_agent_message_sent adds message to inbox when current agent is recipient."""
        # Set up event where current agent is the recipient
        sample_event_data['message'].to_agent = current_agent_id
        sample_event_data['current_agent_id'] = current_agent_id

        result = builder.apply_agent_message_sent(sample_event_data, initial_state)

        # Verify message was added to inbox
        assert len(result['inbox']) == 1
        assert len(result['outbox']) == 0
        assert len(result['conversation_history']) == 0

        # Verify inbox message is properly created
        inbox_msg = result['inbox'][0]
        assert isinstance(inbox_msg, InboxMessage)
        assert inbox_msg.event_id == 'evt-123'
        assert inbox_msg.from_agent == 'sender-agent'
        assert inbox_msg.to_agent == current_agent_id
        assert inbox_msg.subject == 'Test Message'
        assert inbox_msg.body == 'Test message content'
        assert inbox_msg.acknowledged is False

    def test_apply_agent_message_sent_adds_to_outbox_when_sender(
        self, builder, initial_state, sample_event_data, current_agent_id
    ):
        """Test that apply_agent_message_sent adds message to outbox when current agent is sender."""
        # Set up event where current agent is the sender
        sample_event_data['message'].from_agent = current_agent_id
        sample_event_data['current_agent_id'] = current_agent_id

        result = builder.apply_agent_message_sent(sample_event_data, initial_state)

        # Verify message was added to outbox
        assert len(result['inbox']) == 0
        assert len(result['outbox']) == 1
        assert len(result['conversation_history']) == 0

        # Verify outbox message is properly created
        outbox_msg = result['outbox'][0]
        assert isinstance(outbox_msg, OutboxMessage)
        assert outbox_msg.event_id == 'evt-123'
        assert outbox_msg.from_agent == current_agent_id
        assert outbox_msg.to_agent == 'recipient-agent'
        assert outbox_msg.subject == 'Test Message'
        assert outbox_msg.body == 'Test message content'
        assert outbox_msg.completed is False

    def test_apply_agent_message_sent_ignores_unrelated_messages(
        self, builder, initial_state, sample_event_data
    ):
        """Test that apply_agent_message_sent ignores messages not involving current agent."""
        # Set up event where current agent is neither sender nor recipient
        sample_event_data['current_agent_id'] = 'different-agent'

        result = builder.apply_agent_message_sent(sample_event_data, initial_state)

        # Verify no messages were added to any list
        assert len(result['inbox']) == 0
        assert len(result['outbox']) == 0
        assert len(result['conversation_history']) == 0

        # Verify state is unchanged
        assert result == initial_state

    def test_apply_agent_message_sent_preserves_existing_state(
        self, builder, sample_event_data, current_agent_id, message_factory
    ):
        """Test that apply_agent_message_sent preserves existing messages in state."""
        # Create state with existing messages
        existing_inbox_msg = InboxMessage.from_message(
            message_factory(subject="Existing inbox"),
            event_id="existing-1",
            received_at=datetime.now()
        )

        existing_outbox_msg = OutboxMessage.from_message(
            message_factory(subject="Existing outbox"),
            event_id="existing-2",
            sent_at=datetime.now()
        )

        state_with_existing = {
            'inbox': [existing_inbox_msg],
            'outbox': [existing_outbox_msg],
            'conversation_history': []
        }

        # Add new message to inbox
        sample_event_data['message'].to_agent = current_agent_id
        sample_event_data['current_agent_id'] = current_agent_id

        result = builder.apply_agent_message_sent(sample_event_data, state_with_existing)

        # Verify existing messages are preserved
        assert len(result['inbox']) == 2
        assert len(result['outbox']) == 1
        assert result['inbox'][0] == existing_inbox_msg  # Existing message preserved
        assert result['outbox'][0] == existing_outbox_msg  # Existing message preserved

        # Verify new message is added
        new_inbox_msg = result['inbox'][1]
        assert new_inbox_msg.subject == 'Test Message'

    def test_apply_agent_message_sent_with_different_message_types_and_priorities(
        self, builder, initial_state, current_agent_id, message_factory
    ):
        """Test apply_agent_message_sent with various message types and priorities."""
        from jean_claude.core.message import MessagePriority

        # Test urgent help request
        urgent_msg = message_factory(
            from_agent="helper-agent",
            to_agent=current_agent_id,
            type="help_request",
            subject="Urgent Help",
            body="I need immediate assistance",
            priority=MessagePriority.URGENT
        )

        urgent_event = {
            'event_id': 'urgent-123',
            'message': urgent_msg,
            'sent_at': datetime.now(),
            'current_agent_id': current_agent_id
        }

        result = builder.apply_agent_message_sent(urgent_event, initial_state)

        inbox_msg = result['inbox'][0]
        assert inbox_msg.priority == MessagePriority.URGENT
        assert 'urgent' in inbox_msg.subject.lower()

    def test_apply_agent_message_sent_handles_missing_fields_gracefully(
        self, builder, initial_state, current_agent_id
    ):
        """Test apply_agent_message_sent handles malformed event data gracefully."""
        # Test with missing required fields
        incomplete_event = {
            'event_id': 'incomplete-123',
            'current_agent_id': current_agent_id
            # Missing message and sent_at
        }

        # Should handle missing data gracefully and return unchanged state
        result = builder.apply_agent_message_sent(incomplete_event, initial_state)
        assert result == initial_state

    def test_apply_agent_message_sent_preserves_message_timestamps(
        self, builder, initial_state, sample_event_data, current_agent_id
    ):
        """Test that apply_agent_message_sent preserves message timestamps correctly."""
        test_time = datetime(2024, 1, 15, 10, 30, 0)
        sample_event_data['sent_at'] = test_time
        sample_event_data['message'].to_agent = current_agent_id
        sample_event_data['current_agent_id'] = current_agent_id

        result = builder.apply_agent_message_sent(sample_event_data, initial_state)

        inbox_msg = result['inbox'][0]
        assert inbox_msg.received_at == test_time
        assert inbox_msg.created_at == sample_event_data['message'].created_at


class TestAgentMessageSentIntegration:
    """Integration tests for the agent message sent handler."""

    def test_bidirectional_message_flow_simulation(self, message_factory):
        """Test simulation of bidirectional message flow between two agents."""
        builder = MailboxProjectionBuilder()

        # Agent A's perspective
        agent_a_state = builder.get_initial_state()
        agent_a_id = "agent-a"

        # Agent B's perspective
        agent_b_state = builder.get_initial_state()
        agent_b_id = "agent-b"

        # Agent A sends message to Agent B
        msg_a_to_b = message_factory(
            from_agent=agent_a_id,
            to_agent=agent_b_id,
            subject="Hello from A",
            body="This is a message from Agent A"
        )

        event_a_sends = {
            'event_id': 'a-to-b-123',
            'message': msg_a_to_b,
            'sent_at': datetime.now(),
            'current_agent_id': agent_a_id
        }

        event_b_receives = {
            'event_id': 'a-to-b-123',
            'message': msg_a_to_b,
            'sent_at': datetime.now(),
            'current_agent_id': agent_b_id
        }

        # Apply events from both perspectives
        agent_a_state = builder.apply_agent_message_sent(event_a_sends, agent_a_state)
        agent_b_state = builder.apply_agent_message_sent(event_b_receives, agent_b_state)

        # Verify Agent A's outbox
        assert len(agent_a_state['outbox']) == 1
        assert len(agent_a_state['inbox']) == 0
        assert agent_a_state['outbox'][0].to_agent == agent_b_id

        # Verify Agent B's inbox
        assert len(agent_b_state['inbox']) == 1
        assert len(agent_b_state['outbox']) == 0
        assert agent_b_state['inbox'][0].from_agent == agent_a_id