# ABOUTME: Test suite for message acknowledgment handler implementation
# ABOUTME: Tests apply_agent_message_acknowledged() method to mark inbox messages as acknowledged based on event_id matching

"""Test suite for message acknowledgment handler implementation.

This module tests the apply_agent_message_acknowledged() method implementation that processes
agent.message.acknowledged events to update the mailbox projection state by:
- Finding inbox messages that match the correlation_id (which corresponds to the original event_id)
- Marking those messages as acknowledged with the appropriate timestamp
- Only acknowledging messages where the acknowledging agent is the recipient (to_agent)
- Handling cases where no matching messages are found gracefully

The tests cover successful acknowledgment, message matching logic, state preservation,
and edge cases for validation and error handling.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from jean_claude.core.mailbox_projection_builder import MailboxProjectionBuilder
from jean_claude.core.mailbox_message_models import InboxMessage, OutboxMessage
from jean_claude.core.message import Message


class TestAgentMessageAcknowledgedHandler:
    """Test the apply_agent_message_acknowledged method implementation."""

    @pytest.fixture
    def builder(self):
        """Provide a MailboxProjectionBuilder instance."""
        return MailboxProjectionBuilder()

    @pytest.fixture
    def current_agent_id(self):
        """Provide the current agent ID for testing."""
        return "recipient-agent"

    @pytest.fixture
    def sender_agent_id(self):
        """Provide the sender agent ID for testing."""
        return "sender-agent"

    @pytest.fixture
    def initial_state_with_inbox_messages(self, message_factory, current_agent_id, sender_agent_id):
        """Provide initial state with some unacknowledged inbox messages."""
        now = datetime.now()

        # Create first message
        msg1 = message_factory(
            from_agent=sender_agent_id,
            to_agent=current_agent_id,
            subject="First Message",
            body="First message content"
        )

        inbox_msg1 = InboxMessage.from_message(
            message=msg1,
            event_id="evt-001",
            received_at=now - timedelta(minutes=30)
        )

        # Create second message
        msg2 = message_factory(
            from_agent=sender_agent_id,
            to_agent=current_agent_id,
            subject="Second Message",
            body="Second message content"
        )

        inbox_msg2 = InboxMessage.from_message(
            message=msg2,
            event_id="evt-002",
            received_at=now - timedelta(minutes=20)
        )

        # Create third message from different sender
        msg3 = message_factory(
            from_agent="other-agent",
            to_agent=current_agent_id,
            subject="Third Message",
            body="Third message content"
        )

        inbox_msg3 = InboxMessage.from_message(
            message=msg3,
            event_id="evt-003",
            received_at=now - timedelta(minutes=10)
        )

        return {
            'inbox': [inbox_msg1, inbox_msg2, inbox_msg3],
            'outbox': [],
            'conversation_history': []
        }

    @pytest.fixture
    def sample_acknowledgment_event(self, current_agent_id):
        """Provide sample agent.message.acknowledged event data."""
        return {
            'correlation_id': 'evt-001',  # References the first inbox message
            'from_agent': current_agent_id,  # Recipient is acknowledging
            'acknowledged_at': datetime.now()
        }

    def test_apply_agent_message_acknowledged_marks_matching_message_as_acknowledged(
        self, builder, initial_state_with_inbox_messages, sample_acknowledgment_event, current_agent_id
    ):
        """Test that apply_agent_message_acknowledged marks the correct inbox message as acknowledged."""
        # Set up acknowledgment event for first message
        ack_time = datetime.now()
        sample_acknowledgment_event['acknowledged_at'] = ack_time
        sample_acknowledgment_event['current_agent_id'] = current_agent_id

        result = builder.apply_agent_message_acknowledged(
            sample_acknowledgment_event, initial_state_with_inbox_messages
        )

        # Verify the right message was acknowledged
        assert len(result['inbox']) == 3
        acknowledged_msg = None
        unacknowledged_count = 0

        for msg in result['inbox']:
            if msg.event_id == 'evt-001':
                acknowledged_msg = msg
                assert msg.acknowledged is True
                assert msg.acknowledged_at == ack_time
            else:
                assert msg.acknowledged is False
                assert msg.acknowledged_at is None
                unacknowledged_count += 1

        # Should have found the acknowledged message
        assert acknowledged_msg is not None
        # Other messages should remain unacknowledged
        assert unacknowledged_count == 2

        # Verify other state sections unchanged
        assert result['outbox'] == initial_state_with_inbox_messages['outbox']
        assert result['conversation_history'] == initial_state_with_inbox_messages['conversation_history']

    def test_apply_agent_message_acknowledged_handles_no_matching_message(
        self, builder, initial_state_with_inbox_messages, current_agent_id
    ):
        """Test that apply_agent_message_acknowledged handles case where no message matches correlation_id."""
        # Create acknowledgment event for non-existent message
        nonexistent_ack_event = {
            'correlation_id': 'evt-999',  # No message with this event_id
            'from_agent': current_agent_id,
            'acknowledged_at': datetime.now(),
            'current_agent_id': current_agent_id
        }

        result = builder.apply_agent_message_acknowledged(
            nonexistent_ack_event, initial_state_with_inbox_messages
        )

        # State should be unchanged
        assert len(result['inbox']) == 3
        for msg in result['inbox']:
            assert msg.acknowledged is False
            assert msg.acknowledged_at is None

        assert result == initial_state_with_inbox_messages

    def test_apply_agent_message_acknowledged_only_acknowledges_for_correct_agent(
        self, builder, initial_state_with_inbox_messages, sender_agent_id
    ):
        """Test that acknowledgment only works when the acknowledging agent is the message recipient."""
        # Try to acknowledge from wrong agent (sender instead of recipient)
        wrong_agent_ack_event = {
            'correlation_id': 'evt-001',
            'from_agent': sender_agent_id,  # Wrong agent - sender trying to ack
            'acknowledged_at': datetime.now(),
            'current_agent_id': 'different-agent'  # Different agent's projection
        }

        result = builder.apply_agent_message_acknowledged(
            wrong_agent_ack_event, initial_state_with_inbox_messages
        )

        # No messages should be acknowledged
        for msg in result['inbox']:
            assert msg.acknowledged is False
            assert msg.acknowledged_at is None

        # State should be unchanged
        assert result == initial_state_with_inbox_messages

    def test_apply_agent_message_acknowledged_preserves_outbox_and_conversation_history(
        self, builder, message_factory, current_agent_id
    ):
        """Test that apply_agent_message_acknowledged preserves outbox and conversation history."""
        # Create state with messages in all sections
        msg_inbox = message_factory(to_agent=current_agent_id, subject="Inbox msg")
        inbox_msg = InboxMessage.from_message(msg_inbox, "evt-100", datetime.now())

        msg_outbox = message_factory(from_agent=current_agent_id, subject="Outbox msg")
        outbox_msg = OutboxMessage.from_message(msg_outbox, "evt-101", datetime.now())

        state_with_all_sections = {
            'inbox': [inbox_msg],
            'outbox': [outbox_msg],
            'conversation_history': ['some_conversation_data']
        }

        ack_event = {
            'correlation_id': 'evt-100',
            'from_agent': current_agent_id,
            'acknowledged_at': datetime.now(),
            'current_agent_id': current_agent_id
        }

        result = builder.apply_agent_message_acknowledged(ack_event, state_with_all_sections)

        # Inbox should be modified (acknowledgment)
        assert result['inbox'][0].acknowledged is True

        # Outbox and conversation history should be preserved exactly
        assert result['outbox'] == state_with_all_sections['outbox']
        assert result['conversation_history'] == state_with_all_sections['conversation_history']

    def test_apply_agent_message_acknowledged_handles_already_acknowledged_message(
        self, builder, message_factory, current_agent_id
    ):
        """Test that acknowledging an already-acknowledged message doesn't change its timestamp."""
        # Create inbox message that's already acknowledged
        msg = message_factory(to_agent=current_agent_id, subject="Already acked")
        inbox_msg = InboxMessage.from_message(msg, "evt-200", datetime.now())

        original_ack_time = datetime.now() - timedelta(hours=1)
        inbox_msg.acknowledge(original_ack_time)

        state_with_acked_msg = {
            'inbox': [inbox_msg],
            'outbox': [],
            'conversation_history': []
        }

        # Try to acknowledge again with newer timestamp
        later_ack_event = {
            'correlation_id': 'evt-200',
            'from_agent': current_agent_id,
            'acknowledged_at': datetime.now(),  # Later time
            'current_agent_id': current_agent_id
        }

        result = builder.apply_agent_message_acknowledged(later_ack_event, state_with_acked_msg)

        # Should keep original acknowledgment time
        assert result['inbox'][0].acknowledged is True
        assert result['inbox'][0].acknowledged_at == original_ack_time

    def test_apply_agent_message_acknowledged_handles_missing_required_fields(
        self, builder, initial_state_with_inbox_messages
    ):
        """Test that apply_agent_message_acknowledged handles missing required fields gracefully."""
        # Test with missing correlation_id
        incomplete_event1 = {
            'from_agent': 'some-agent',
            'acknowledged_at': datetime.now(),
            'current_agent_id': 'some-agent'
            # Missing correlation_id
        }

        result1 = builder.apply_agent_message_acknowledged(
            incomplete_event1, initial_state_with_inbox_messages
        )
        assert result1 == initial_state_with_inbox_messages

        # Test with missing from_agent
        incomplete_event2 = {
            'correlation_id': 'evt-001',
            'acknowledged_at': datetime.now(),
            'current_agent_id': 'some-agent'
            # Missing from_agent
        }

        result2 = builder.apply_agent_message_acknowledged(
            incomplete_event2, initial_state_with_inbox_messages
        )
        assert result2 == initial_state_with_inbox_messages

    def test_apply_agent_message_acknowledged_preserves_message_immutability(
        self, builder, message_factory, current_agent_id
    ):
        """Test that apply_agent_message_acknowledged doesn't mutate the original state objects."""
        msg = message_factory(to_agent=current_agent_id, subject="Immutable test")
        original_inbox_msg = InboxMessage.from_message(msg, "evt-300", datetime.now())

        original_state = {
            'inbox': [original_inbox_msg],
            'outbox': [],
            'conversation_history': []
        }

        ack_event = {
            'correlation_id': 'evt-300',
            'from_agent': current_agent_id,
            'acknowledged_at': datetime.now(),
            'current_agent_id': current_agent_id
        }

        result = builder.apply_agent_message_acknowledged(ack_event, original_state)

        # Original message should be unchanged
        assert original_inbox_msg.acknowledged is False
        assert original_inbox_msg.acknowledged_at is None

        # Result should have acknowledged message
        assert result['inbox'][0].acknowledged is True
        assert result['inbox'][0].acknowledged_at is not None

        # But they should be different objects
        assert result['inbox'][0] is not original_inbox_msg

    def test_apply_agent_message_acknowledged_with_multiple_matching_messages(
        self, builder, message_factory, current_agent_id
    ):
        """Test behavior when multiple messages have the same event_id (edge case)."""
        # This is technically an edge case that shouldn't happen normally,
        # but we should handle it gracefully
        msg = message_factory(to_agent=current_agent_id, subject="Duplicate event ID")

        # Create two inbox messages with same event_id (shouldn't happen normally)
        inbox_msg1 = InboxMessage.from_message(msg, "evt-duplicate", datetime.now())
        inbox_msg2 = InboxMessage.from_message(msg, "evt-duplicate", datetime.now())

        state_with_duplicates = {
            'inbox': [inbox_msg1, inbox_msg2],
            'outbox': [],
            'conversation_history': []
        }

        ack_time = datetime.now()
        ack_event = {
            'correlation_id': 'evt-duplicate',
            'from_agent': current_agent_id,
            'acknowledged_at': ack_time,
            'current_agent_id': current_agent_id
        }

        result = builder.apply_agent_message_acknowledged(ack_event, state_with_duplicates)

        # Both messages should be acknowledged (since they have matching event_id)
        assert len(result['inbox']) == 2
        for msg in result['inbox']:
            assert msg.acknowledged is True
            assert msg.acknowledged_at == ack_time


class TestAgentMessageAcknowledgedIntegration:
    """Integration tests for the agent message acknowledged handler."""

    def test_complete_message_lifecycle_with_acknowledgment(self, message_factory):
        """Test the complete message flow: send -> receive -> acknowledge."""
        builder = MailboxProjectionBuilder()

        # Agent A's perspective (sender)
        agent_a_state = builder.get_initial_state()
        agent_a_id = "agent-a"

        # Agent B's perspective (recipient)
        agent_b_state = builder.get_initial_state()
        agent_b_id = "agent-b"

        sent_time = datetime.now()

        # Step 1: Agent A sends message to Agent B
        msg = message_factory(
            from_agent=agent_a_id,
            to_agent=agent_b_id,
            subject="Task Request",
            body="Please complete this task"
        )

        sent_event = {
            'event_id': 'msg-123',
            'message': msg,
            'sent_at': sent_time,
            'current_agent_id': agent_a_id  # A's perspective
        }

        receive_event = {
            'event_id': 'msg-123',
            'message': msg,
            'sent_at': sent_time,
            'current_agent_id': agent_b_id  # B's perspective
        }

        # Apply send/receive events
        agent_a_state = builder.apply_agent_message_sent(sent_event, agent_a_state)
        agent_b_state = builder.apply_agent_message_sent(receive_event, agent_b_state)

        # Verify initial state
        assert len(agent_a_state['outbox']) == 1
        assert len(agent_b_state['inbox']) == 1
        assert agent_b_state['inbox'][0].acknowledged is False

        # Step 2: Agent B acknowledges the message
        ack_time = sent_time + timedelta(minutes=5)
        ack_event = {
            'correlation_id': 'msg-123',  # References the original event_id
            'from_agent': agent_b_id,
            'acknowledged_at': ack_time,
            'current_agent_id': agent_b_id  # B's perspective
        }

        agent_b_state = builder.apply_agent_message_acknowledged(ack_event, agent_b_state)

        # Verify acknowledgment was processed
        assert len(agent_b_state['inbox']) == 1
        acknowledged_msg = agent_b_state['inbox'][0]
        assert acknowledged_msg.acknowledged is True
        assert acknowledged_msg.acknowledged_at == ack_time
        assert acknowledged_msg.event_id == 'msg-123'
        assert acknowledged_msg.subject == "Task Request"

        # Agent A's state should be unchanged by B's acknowledgment event
        # (A would need to process the acknowledgment from their perspective)
        assert len(agent_a_state['outbox']) == 1
        assert agent_a_state['outbox'][0].event_id == 'msg-123'

    def test_cross_agent_acknowledgment_isolation(self, message_factory):
        """Test that acknowledgments are properly isolated between different agents."""
        builder = MailboxProjectionBuilder()

        agent_a_id = "agent-a"
        agent_b_id = "agent-b"
        agent_c_id = "agent-c"

        # Create states for all agents
        agent_a_state = builder.get_initial_state()
        agent_b_state = builder.get_initial_state()
        agent_c_state = builder.get_initial_state()

        # Send messages: A->B and A->C
        msg_to_b = message_factory(from_agent=agent_a_id, to_agent=agent_b_id, subject="To B")
        msg_to_c = message_factory(from_agent=agent_a_id, to_agent=agent_c_id, subject="To C")

        # Both agents receive their respective messages
        agent_b_state = builder.apply_agent_message_sent({
            'event_id': 'msg-b-001',
            'message': msg_to_b,
            'sent_at': datetime.now(),
            'current_agent_id': agent_b_id
        }, agent_b_state)

        agent_c_state = builder.apply_agent_message_sent({
            'event_id': 'msg-c-001',
            'message': msg_to_c,
            'sent_at': datetime.now(),
            'current_agent_id': agent_c_id
        }, agent_c_state)

        # Agent B acknowledges their message
        agent_b_state = builder.apply_agent_message_acknowledged({
            'correlation_id': 'msg-b-001',
            'from_agent': agent_b_id,
            'acknowledged_at': datetime.now(),
            'current_agent_id': agent_b_id
        }, agent_b_state)

        # Verify B's message is acknowledged
        assert agent_b_state['inbox'][0].acknowledged is True

        # Verify C's message is still unacknowledged
        assert agent_c_state['inbox'][0].acknowledged is False

        # Verify C can't acknowledge B's message (wrong agent/correlation_id)
        agent_c_state_after_wrong_ack = builder.apply_agent_message_acknowledged({
            'correlation_id': 'msg-b-001',  # B's message
            'from_agent': agent_c_id,       # But C trying to ack
            'acknowledged_at': datetime.now(),
            'current_agent_id': agent_c_id
        }, agent_c_state)

        # C's state should be unchanged (no matching message in their inbox)
        assert agent_c_state_after_wrong_ack == agent_c_state