# ABOUTME: Test suite for message completion handler implementation
# ABOUTME: Tests apply_agent_message_completed() method to remove messages from outbox and add them to conversation_history when completed

"""Test suite for message completion handler implementation.

This module tests the apply_agent_message_completed() method implementation that processes
agent.message.completed events to update the mailbox projection state by:
- Finding outbox messages that match the correlation_id (which corresponds to the original event_id)
- Marking those messages as completed and moving them to conversation history
- Only processing completions from the current agent (the sender of the message)
- Handling cases where no matching messages are found gracefully

The tests cover successful completion, message matching logic, state preservation,
and edge cases for validation and error handling.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from jean_claude.core.mailbox_projection_builder import MailboxProjectionBuilder
from jean_claude.core.mailbox_message_models import InboxMessage, OutboxMessage, ConversationMessage
from jean_claude.core.message import Message


class TestAgentMessageCompletedHandler:
    """Test the apply_agent_message_completed method implementation."""

    @pytest.fixture
    def builder(self):
        """Provide a MailboxProjectionBuilder instance."""
        return MailboxProjectionBuilder()

    @pytest.fixture
    def current_agent_id(self):
        """Provide the current agent ID for testing."""
        return "sender-agent"

    @pytest.fixture
    def recipient_agent_id(self):
        """Provide the recipient agent ID for testing."""
        return "recipient-agent"

    @pytest.fixture
    def initial_state_with_outbox_messages(self, message_factory, current_agent_id, recipient_agent_id):
        """Provide initial state with some outbox messages."""
        now = datetime.now()

        # Create first message
        msg1 = message_factory(
            from_agent=current_agent_id,
            to_agent=recipient_agent_id,
            subject="First Message",
            body="First message content"
        )

        outbox_msg1 = OutboxMessage.from_message(
            message=msg1,
            event_id="evt-001",
            sent_at=now - timedelta(minutes=30)
        )

        # Create second message
        msg2 = message_factory(
            from_agent=current_agent_id,
            to_agent=recipient_agent_id,
            subject="Second Message",
            body="Second message content"
        )

        outbox_msg2 = OutboxMessage.from_message(
            message=msg2,
            event_id="evt-002",
            sent_at=now - timedelta(minutes=20)
        )

        # Create third message from different agent (shouldn't be affected)
        msg3 = message_factory(
            from_agent="other-agent",
            to_agent=recipient_agent_id,
            subject="Third Message",
            body="Third message content"
        )

        outbox_msg3 = OutboxMessage.from_message(
            message=msg3,
            event_id="evt-003",
            sent_at=now - timedelta(minutes=10)
        )

        return {
            'inbox': [],
            'outbox': [outbox_msg1, outbox_msg2, outbox_msg3],
            'conversation_history': []
        }

    @pytest.fixture
    def sample_completion_event(self, current_agent_id):
        """Provide sample agent.message.completed event data."""
        return {
            'correlation_id': 'evt-001',  # References the first outbox message
            'from_agent': current_agent_id,  # Sender is completing
            'completed_at': datetime.now(),
            'success': True,
            'result': 'Task completed successfully'
        }

    def test_apply_agent_message_completed_removes_from_outbox_and_adds_to_conversation_history(
        self, builder, initial_state_with_outbox_messages, sample_completion_event, current_agent_id
    ):
        """Test that apply_agent_message_completed removes message from outbox and adds to conversation history."""
        # Set up completion event for first message
        completion_time = datetime.now()
        sample_completion_event['completed_at'] = completion_time
        sample_completion_event['current_agent_id'] = current_agent_id

        result = builder.apply_agent_message_completed(
            sample_completion_event, initial_state_with_outbox_messages
        )

        # Verify message was removed from outbox
        assert len(result['outbox']) == 2  # One less than original

        # Verify remaining outbox messages don't include the completed one
        outbox_event_ids = [msg.event_id for msg in result['outbox']]
        assert 'evt-001' not in outbox_event_ids
        assert 'evt-002' in outbox_event_ids  # Should still be there
        assert 'evt-003' in outbox_event_ids  # Should still be there

        # Verify message was added to conversation history
        assert len(result['conversation_history']) == 1
        conversation_msg = result['conversation_history'][0]
        assert isinstance(conversation_msg, ConversationMessage)
        assert conversation_msg.event_id == 'evt-001'
        assert conversation_msg.from_agent == current_agent_id
        assert conversation_msg.subject == 'First Message'
        assert conversation_msg.body == 'First message content'
        assert conversation_msg.completed_at == completion_time
        assert conversation_msg.success is True
        assert conversation_msg.correlation_id == 'evt-001'

        # Verify inbox unchanged
        assert result['inbox'] == initial_state_with_outbox_messages['inbox']

    def test_apply_agent_message_completed_handles_no_matching_message(
        self, builder, initial_state_with_outbox_messages, current_agent_id
    ):
        """Test that apply_agent_message_completed handles case where no message matches correlation_id."""
        # Create completion event for non-existent message
        nonexistent_completion_event = {
            'correlation_id': 'evt-999',  # No message with this event_id
            'from_agent': current_agent_id,
            'completed_at': datetime.now(),
            'success': True,
            'result': 'Completed',
            'current_agent_id': current_agent_id
        }

        result = builder.apply_agent_message_completed(
            nonexistent_completion_event, initial_state_with_outbox_messages
        )

        # State should be unchanged
        assert len(result['outbox']) == 3
        assert len(result['conversation_history']) == 0
        assert result == initial_state_with_outbox_messages

    def test_apply_agent_message_completed_only_processes_for_correct_agent(
        self, builder, initial_state_with_outbox_messages, recipient_agent_id
    ):
        """Test that completion only works when the completing agent is the message sender."""
        # Try to complete from wrong agent (recipient instead of sender)
        wrong_agent_completion_event = {
            'correlation_id': 'evt-001',
            'from_agent': recipient_agent_id,  # Wrong agent - recipient trying to complete
            'completed_at': datetime.now(),
            'success': True,
            'result': 'Completed',
            'current_agent_id': 'different-agent'  # Different agent's projection
        }

        result = builder.apply_agent_message_completed(
            wrong_agent_completion_event, initial_state_with_outbox_messages
        )

        # No messages should be completed
        assert len(result['outbox']) == 3
        assert len(result['conversation_history']) == 0

        # State should be unchanged
        assert result == initial_state_with_outbox_messages

    def test_apply_agent_message_completed_preserves_inbox_and_other_outbox_messages(
        self, builder, message_factory, current_agent_id, recipient_agent_id
    ):
        """Test that apply_agent_message_completed preserves inbox and other outbox messages."""
        # Create state with messages in all sections
        msg_inbox = message_factory(to_agent=current_agent_id, subject="Inbox msg")
        inbox_msg = InboxMessage.from_message(msg_inbox, "evt-100", datetime.now())

        msg_outbox1 = message_factory(from_agent=current_agent_id, subject="Outbox msg 1")
        outbox_msg1 = OutboxMessage.from_message(msg_outbox1, "evt-101", datetime.now())

        msg_outbox2 = message_factory(from_agent=current_agent_id, subject="Outbox msg 2")
        outbox_msg2 = OutboxMessage.from_message(msg_outbox2, "evt-102", datetime.now())

        state_with_all_sections = {
            'inbox': [inbox_msg],
            'outbox': [outbox_msg1, outbox_msg2],
            'conversation_history': []
        }

        completion_event = {
            'correlation_id': 'evt-101',  # Complete first outbox message
            'from_agent': current_agent_id,
            'completed_at': datetime.now(),
            'success': True,
            'result': 'Completed successfully',
            'current_agent_id': current_agent_id
        }

        result = builder.apply_agent_message_completed(completion_event, state_with_all_sections)

        # Outbox should have one less message
        assert len(result['outbox']) == 1
        assert result['outbox'][0].event_id == 'evt-102'

        # Conversation history should have the completed message
        assert len(result['conversation_history']) == 1
        assert result['conversation_history'][0].event_id == 'evt-101'

        # Inbox should be preserved exactly
        assert result['inbox'] == state_with_all_sections['inbox']

    def test_apply_agent_message_completed_handles_failure_result(
        self, builder, message_factory, current_agent_id, recipient_agent_id
    ):
        """Test that apply_agent_message_completed handles failure results correctly."""
        # Create outbox message
        msg = message_factory(from_agent=current_agent_id, to_agent=recipient_agent_id, subject="Failed msg")
        outbox_msg = OutboxMessage.from_message(msg, "evt-fail", datetime.now())

        state_with_outbox = {
            'inbox': [],
            'outbox': [outbox_msg],
            'conversation_history': []
        }

        # Complete with failure
        failure_completion_event = {
            'correlation_id': 'evt-fail',
            'from_agent': current_agent_id,
            'completed_at': datetime.now(),
            'success': False,
            'result': 'Task failed due to error',
            'current_agent_id': current_agent_id
        }

        result = builder.apply_agent_message_completed(failure_completion_event, state_with_outbox)

        # Should still move to conversation history even on failure
        assert len(result['outbox']) == 0
        assert len(result['conversation_history']) == 1

        conversation_msg = result['conversation_history'][0]
        assert conversation_msg.success is False
        assert conversation_msg.event_id == 'evt-fail'

    def test_apply_agent_message_completed_handles_missing_required_fields(
        self, builder, initial_state_with_outbox_messages
    ):
        """Test that apply_agent_message_completed handles missing required fields gracefully."""
        # Test with missing correlation_id
        incomplete_event1 = {
            'from_agent': 'some-agent',
            'completed_at': datetime.now(),
            'success': True,
            'current_agent_id': 'some-agent'
            # Missing correlation_id
        }

        result1 = builder.apply_agent_message_completed(
            incomplete_event1, initial_state_with_outbox_messages
        )
        assert result1 == initial_state_with_outbox_messages

        # Test with missing from_agent
        incomplete_event2 = {
            'correlation_id': 'evt-001',
            'completed_at': datetime.now(),
            'success': True,
            'current_agent_id': 'some-agent'
            # Missing from_agent
        }

        result2 = builder.apply_agent_message_completed(
            incomplete_event2, initial_state_with_outbox_messages
        )
        assert result2 == initial_state_with_outbox_messages

    def test_apply_agent_message_completed_preserves_message_immutability(
        self, builder, message_factory, current_agent_id, recipient_agent_id
    ):
        """Test that apply_agent_message_completed doesn't mutate the original state objects."""
        msg = message_factory(from_agent=current_agent_id, to_agent=recipient_agent_id, subject="Immutable test")
        original_outbox_msg = OutboxMessage.from_message(msg, "evt-300", datetime.now())

        original_state = {
            'inbox': [],
            'outbox': [original_outbox_msg],
            'conversation_history': []
        }

        completion_event = {
            'correlation_id': 'evt-300',
            'from_agent': current_agent_id,
            'completed_at': datetime.now(),
            'success': True,
            'result': 'Completed',
            'current_agent_id': current_agent_id
        }

        result = builder.apply_agent_message_completed(completion_event, original_state)

        # Original message should be unchanged
        assert original_outbox_msg.completed is False
        assert original_outbox_msg.completed_at is None

        # Original state should still have the message
        assert len(original_state['outbox']) == 1
        assert original_state['outbox'][0] is original_outbox_msg

        # Result should have removed the message and added to conversation history
        assert len(result['outbox']) == 0
        assert len(result['conversation_history']) == 1

    def test_apply_agent_message_completed_with_multiple_matching_messages(
        self, builder, message_factory, current_agent_id, recipient_agent_id
    ):
        """Test behavior when multiple outbox messages have the same event_id (edge case)."""
        # This is technically an edge case that shouldn't happen normally,
        # but we should handle it gracefully
        msg = message_factory(from_agent=current_agent_id, to_agent=recipient_agent_id, subject="Duplicate event ID")

        # Create two outbox messages with same event_id (shouldn't happen normally)
        outbox_msg1 = OutboxMessage.from_message(msg, "evt-duplicate", datetime.now())
        outbox_msg2 = OutboxMessage.from_message(msg, "evt-duplicate", datetime.now())

        state_with_duplicates = {
            'inbox': [],
            'outbox': [outbox_msg1, outbox_msg2],
            'conversation_history': []
        }

        completion_time = datetime.now()
        completion_event = {
            'correlation_id': 'evt-duplicate',
            'from_agent': current_agent_id,
            'completed_at': completion_time,
            'success': True,
            'result': 'Completed',
            'current_agent_id': current_agent_id
        }

        result = builder.apply_agent_message_completed(completion_event, state_with_duplicates)

        # Both messages should be completed (since they have matching event_id)
        assert len(result['outbox']) == 0
        assert len(result['conversation_history']) == 2

        for conversation_msg in result['conversation_history']:
            assert conversation_msg.event_id == 'evt-duplicate'
            assert conversation_msg.success is True
            assert conversation_msg.completed_at == completion_time


class TestAgentMessageCompletedIntegration:
    """Integration tests for the agent message completed handler."""

    def test_complete_message_lifecycle_with_completion(self, message_factory):
        """Test the complete message flow: send -> acknowledge -> complete."""
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
        assert agent_a_state['outbox'][0].completed is False

        # Step 2: Agent B acknowledges the message
        ack_time = sent_time + timedelta(minutes=5)
        ack_event = {
            'correlation_id': 'msg-123',  # References the original event_id
            'from_agent': agent_b_id,
            'acknowledged_at': ack_time,
            'current_agent_id': agent_b_id  # B's perspective
        }

        agent_b_state = builder.apply_agent_message_acknowledged(ack_event, agent_b_state)
        assert agent_b_state['inbox'][0].acknowledged is True

        # Step 3: Agent A completes the message processing
        completion_time = sent_time + timedelta(minutes=10)
        completion_event = {
            'correlation_id': 'msg-123',  # References the original event_id
            'from_agent': agent_a_id,
            'completed_at': completion_time,
            'success': True,
            'result': 'Message processed successfully',
            'current_agent_id': agent_a_id  # A's perspective
        }

        agent_a_state = builder.apply_agent_message_completed(completion_event, agent_a_state)

        # Verify completion was processed
        assert len(agent_a_state['outbox']) == 0  # Message removed from outbox
        assert len(agent_a_state['conversation_history']) == 1  # Message added to conversation

        completed_msg = agent_a_state['conversation_history'][0]
        assert completed_msg.event_id == 'msg-123'
        assert completed_msg.subject == "Task Request"
        assert completed_msg.success is True
        assert completed_msg.completed_at == completion_time
        assert completed_msg.correlation_id == 'msg-123'

        # Agent B's state should be unchanged by A's completion event
        # (B would need to process the completion from their perspective if needed)
        assert len(agent_b_state['inbox']) == 1
        assert agent_b_state['inbox'][0].event_id == 'msg-123'

    def test_cross_agent_completion_isolation(self, message_factory):
        """Test that completions are properly isolated between different agents."""
        builder = MailboxProjectionBuilder()

        agent_a_id = "agent-a"
        agent_b_id = "agent-b"
        agent_c_id = "agent-c"

        # Create states for all agents
        agent_a_state = builder.get_initial_state()
        agent_b_state = builder.get_initial_state()
        agent_c_state = builder.get_initial_state()

        # Send messages: A->B and C->B
        msg_from_a = message_factory(from_agent=agent_a_id, to_agent=agent_b_id, subject="From A")
        msg_from_c = message_factory(from_agent=agent_c_id, to_agent=agent_b_id, subject="From C")

        # A sends to B
        agent_a_state = builder.apply_agent_message_sent({
            'event_id': 'msg-a-001',
            'message': msg_from_a,
            'sent_at': datetime.now(),
            'current_agent_id': agent_a_id
        }, agent_a_state)

        # C sends to B
        agent_c_state = builder.apply_agent_message_sent({
            'event_id': 'msg-c-001',
            'message': msg_from_c,
            'sent_at': datetime.now(),
            'current_agent_id': agent_c_id
        }, agent_c_state)

        # Agent A completes their message
        completion_time = datetime.now()
        agent_a_state = builder.apply_agent_message_completed({
            'correlation_id': 'msg-a-001',
            'from_agent': agent_a_id,
            'completed_at': completion_time,
            'success': True,
            'result': 'A completed successfully',
            'current_agent_id': agent_a_id
        }, agent_a_state)

        # Verify A's message is completed
        assert len(agent_a_state['outbox']) == 0
        assert len(agent_a_state['conversation_history']) == 1

        # Verify C's message is still pending
        assert len(agent_c_state['outbox']) == 1
        assert len(agent_c_state['conversation_history']) == 0

        # Verify A can't complete C's message (wrong agent/correlation_id)
        agent_a_state_after_wrong_completion = builder.apply_agent_message_completed({
            'correlation_id': 'msg-c-001',  # C's message
            'from_agent': agent_a_id,       # But A trying to complete
            'completed_at': datetime.now(),
            'success': True,
            'result': 'Should not work',
            'current_agent_id': agent_a_id
        }, agent_a_state)

        # A's state should be unchanged (no matching message in their outbox)
        assert len(agent_a_state_after_wrong_completion['outbox']) == 0
        assert len(agent_a_state_after_wrong_completion['conversation_history']) == 1
        assert agent_a_state_after_wrong_completion == agent_a_state