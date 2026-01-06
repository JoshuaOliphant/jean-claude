# ABOUTME: Test suite for correlation_id tracking and validation across inbox/outbox operations
# ABOUTME: Tests correlation_id consistency, thread tracking, and validation in MailboxProjectionBuilder

"""Test suite for correlation_id tracking and validation implementation.

This module tests the correlation_id tracking functionality that ensures message thread consistency
across inbox/outbox operations by:
- Validating correlation_id format and uniqueness
- Tracking message threads through their lifecycle (sent → acknowledged → completed)
- Ensuring correlation_id consistency between related messages
- Preventing orphaned or mismatched correlation IDs
- Handling edge cases for correlation_id validation

The tests cover correlation_id validation, thread tracking, consistency checks,
and edge cases for error handling and thread reconstruction.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from jean_claude.core.mailbox_projection_builder import MailboxProjectionBuilder
from jean_claude.core.mailbox_message_models import InboxMessage, OutboxMessage, ConversationMessage
from jean_claude.core.message import Message, MessagePriority


class TestCorrelationIdValidation:
    """Test correlation_id validation and format checking."""

    @pytest.fixture
    def builder(self):
        """Provide a MailboxProjectionBuilder instance."""
        return MailboxProjectionBuilder()

    @pytest.fixture
    def base_event_data(self):
        """Provide base event data for testing."""
        return {
            'current_agent_id': 'test-agent',
            'from_agent': 'sender-agent',
            'to_agent': 'test-agent',
            'sent_at': datetime.now(),
        }

    def test_correlation_id_format_validation(self, builder, message_factory, base_event_data):
        """Test that correlation_id follows proper format requirements."""
        base_state = {'inbox': [], 'outbox': [], 'conversation_history': []}

        # Valid correlation_id formats should work
        valid_correlation_ids = [
            'corr-123',
            'thread-abc-456',
            'msg_correlation_789',
            'uuid-4a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p'
        ]

        for correlation_id in valid_correlation_ids:
            msg = message_factory(
                from_agent='sender-agent',
                to_agent='test-agent',
                correlation_id=correlation_id
            )
            event_data = {
                **base_event_data,
                'message': msg,
                'event_id': 'evt-001'
            }

            # Should process without error
            result = builder.apply_agent_message_sent(event_data, base_state)
            assert len(result['inbox']) == 1
            assert result['inbox'][0].correlation_id == correlation_id

            # Reset state for next test
            base_state = {'inbox': [], 'outbox': [], 'conversation_history': []}

    def test_correlation_id_tracking_across_message_lifecycle(
        self, builder, message_factory, base_event_data
    ):
        """Test that correlation_id is preserved through the complete message lifecycle."""
        correlation_id = 'test-thread-001'
        event_id = 'evt-001'

        # Step 1: Send message (adds to inbox/outbox)
        msg = message_factory(
            from_agent='sender-agent',
            to_agent='test-agent',
            correlation_id=correlation_id
        )

        send_event_data = {
            **base_event_data,
            'message': msg,
            'event_id': event_id
        }

        state = {'inbox': [], 'outbox': [], 'conversation_history': []}
        state = builder.apply_agent_message_sent(send_event_data, state)

        # Verify message is in inbox with correct correlation_id
        assert len(state['inbox']) == 1
        assert state['inbox'][0].correlation_id == correlation_id
        assert state['inbox'][0].event_id == event_id

        # Step 2: Acknowledge message
        ack_event_data = {
            'correlation_id': event_id,
            'from_agent': 'test-agent',
            'acknowledged_at': datetime.now(),
            'current_agent_id': 'test-agent'
        }

        state = builder.apply_agent_message_acknowledged(ack_event_data, state)

        # Verify message is acknowledged but correlation_id preserved
        assert state['inbox'][0].acknowledged is True
        assert state['inbox'][0].correlation_id == correlation_id

        # Step 3: Test outbox message with same correlation_id
        outbox_msg = message_factory(
            from_agent='test-agent',
            to_agent='recipient-agent',
            correlation_id=correlation_id  # Same thread
        )

        outbox_send_event_data = {
            'current_agent_id': 'test-agent',
            'message': outbox_msg,
            'event_id': 'evt-002',
            'sent_at': datetime.now()
        }

        state = builder.apply_agent_message_sent(outbox_send_event_data, state)

        # Verify outbox message has same correlation_id (part of same thread)
        assert len(state['outbox']) == 1
        assert state['outbox'][0].correlation_id == correlation_id

        # Step 4: Complete outbox message
        complete_event_data = {
            'correlation_id': 'evt-002',
            'from_agent': 'test-agent',
            'completed_at': datetime.now(),
            'success': True,
            'current_agent_id': 'test-agent'
        }

        state = builder.apply_agent_message_completed(complete_event_data, state)

        # Verify message moved to conversation_history with correlation_id preserved
        assert len(state['outbox']) == 0
        assert len(state['conversation_history']) == 1
        assert state['conversation_history'][0].correlation_id == correlation_id


class TestCorrelationIdThreadTracking:
    """Test correlation_id thread tracking and consistency."""

    @pytest.fixture
    def builder(self):
        """Provide a MailboxProjectionBuilder instance."""
        return MailboxProjectionBuilder()

    @pytest.fixture
    def multi_thread_state(self, message_factory):
        """Provide state with multiple message threads."""
        now = datetime.now()

        # Thread 1: Customer inquiry
        thread1_msg1 = InboxMessage.from_message(
            message=message_factory(
                from_agent='customer-agent',
                to_agent='support-agent',
                subject='Product Question',
                correlation_id='thread-customer-001'
            ),
            event_id='evt-001',
            received_at=now - timedelta(minutes=30)
        )
        # Mark as acknowledged so thread can be "completed"
        thread1_msg1.acknowledged = True
        thread1_msg1.acknowledged_at = now - timedelta(minutes=28)

        thread1_msg2 = ConversationMessage(
            event_id='evt-002',
            message_id='msg-002',
            from_agent='support-agent',
            to_agent='customer-agent',
            subject='Re: Product Question',
            body='Here is the answer...',
            priority=MessagePriority.NORMAL,
            created_at=now - timedelta(minutes=25),
            sent_at=now - timedelta(minutes=24),
            completed_at=now - timedelta(minutes=20),
            success=True,
            correlation_id='thread-customer-001'  # Same thread
        )

        # Thread 2: Bug report
        thread2_msg1 = OutboxMessage.from_message(
            message=message_factory(
                from_agent='support-agent',
                to_agent='dev-agent',
                subject='Bug Report',
                correlation_id='thread-bug-report-001'
            ),
            event_id='evt-003',
            sent_at=now - timedelta(minutes=15)
        )

        thread2_msg2 = InboxMessage.from_message(
            message=message_factory(
                from_agent='dev-agent',
                to_agent='support-agent',
                subject='Re: Bug Report',
                correlation_id='thread-bug-report-001'  # Same thread
            ),
            event_id='evt-004',
            received_at=now - timedelta(minutes=10)
        )

        return {
            'inbox': [thread1_msg1, thread2_msg2],
            'outbox': [thread2_msg1],
            'conversation_history': [thread1_msg2]
        }

    def test_get_messages_by_correlation_id(self, builder, multi_thread_state):
        """Test helper method to retrieve all messages by correlation_id."""
        # Get all messages from thread-customer-001
        customer_thread_result = builder.get_messages_by_correlation_id(
            multi_thread_state, 'thread-customer-001'
        )

        assert len(customer_thread_result['all']) == 2
        correlation_ids = [msg.correlation_id for msg in customer_thread_result['all']]
        assert all(cid == 'thread-customer-001' for cid in correlation_ids)

        # Verify distribution across message stores
        assert len(customer_thread_result['inbox']) == 1
        assert len(customer_thread_result['outbox']) == 0
        assert len(customer_thread_result['conversation_history']) == 1

        # Get all messages from thread-bug-report-001
        bug_thread_result = builder.get_messages_by_correlation_id(
            multi_thread_state, 'thread-bug-report-001'
        )

        assert len(bug_thread_result['all']) == 2
        correlation_ids = [msg.correlation_id for msg in bug_thread_result['all']]
        assert all(cid == 'thread-bug-report-001' for cid in correlation_ids)

        # Verify distribution across message stores
        assert len(bug_thread_result['inbox']) == 1
        assert len(bug_thread_result['outbox']) == 1
        assert len(bug_thread_result['conversation_history']) == 0

    def test_thread_consistency_validation(self, builder, multi_thread_state):
        """Test validation that all messages in a thread have consistent correlation_id."""
        validation_results = builder.validate_thread_consistency(multi_thread_state)

        # Should find no inconsistencies in our well-formed test data
        assert validation_results['valid'] is True
        assert len(validation_results['inconsistencies']) == 0
        assert validation_results['thread_statistics']['total_threads'] == 2
        assert validation_results['thread_statistics']['total_messages'] == 4

    def test_orphaned_correlation_id_detection(self, builder, message_factory):
        """Test detection of orphaned correlation IDs."""
        now = datetime.now()

        # Create state with orphaned acknowledgment
        orphaned_ack_msg = InboxMessage.from_message(
            message=message_factory(correlation_id='thread-orphaned-001'),
            event_id='evt-orphaned',
            received_at=now
        )
        orphaned_ack_msg.acknowledged = True
        orphaned_ack_msg.acknowledged_at = now + timedelta(minutes=5)

        state = {
            'inbox': [orphaned_ack_msg],
            'outbox': [],
            'conversation_history': []
        }

        # Validate thread completeness
        validation_results = builder.validate_thread_consistency(state)

        # Should detect that there's an acknowledged message without a corresponding sent message
        assert not validation_results['valid']
        assert len(validation_results['inconsistencies']) > 0
        assert validation_results['thread_statistics']['orphaned_threads'] == 1

    def test_get_thread_summary(self, builder, multi_thread_state):
        """Test comprehensive thread summary functionality."""
        # Get summary for customer thread
        customer_summary = builder.get_thread_summary(
            multi_thread_state, 'thread-customer-001'
        )

        assert customer_summary['correlation_id'] == 'thread-customer-001'
        assert customer_summary['message_count'] == 2
        assert len(customer_summary['participants']) == 2
        assert 'customer-agent' in customer_summary['participants']
        assert 'support-agent' in customer_summary['participants']
        assert customer_summary['status'] == 'completed'  # Has conversation history
        assert len(customer_summary['timeline']) == 2

        # Get summary for bug report thread
        bug_summary = builder.get_thread_summary(
            multi_thread_state, 'thread-bug-report-001'
        )

        assert bug_summary['correlation_id'] == 'thread-bug-report-001'
        assert bug_summary['message_count'] == 2
        assert len(bug_summary['participants']) == 2
        assert 'dev-agent' in bug_summary['participants']
        assert 'support-agent' in bug_summary['participants']
        assert bug_summary['status'] == 'active'  # Has pending outbox and inbox
        assert len(bug_summary['pending_actions']) == 2  # One outbox, one unacknowledged inbox

        # Test non-existent thread
        empty_summary = builder.get_thread_summary(
            multi_thread_state, 'non-existent-thread'
        )

        assert empty_summary['correlation_id'] == 'non-existent-thread'
        assert empty_summary['message_count'] == 0
        assert empty_summary['status'] == 'not_found'
        assert len(empty_summary['timeline']) == 0


class TestCorrelationIdEdgeCases:
    """Test edge cases and error handling for correlation_id tracking."""

    @pytest.fixture
    def builder(self):
        """Provide a MailboxProjectionBuilder instance."""
        return MailboxProjectionBuilder()

    def test_missing_correlation_id_handling(self, builder, message_factory):
        """Test handling of messages with missing or None correlation_id."""
        # System correctly preserves None correlation_id without auto-generating
        base_state = {'inbox': [], 'outbox': [], 'conversation_history': []}

        # Create message without explicit correlation_id but with matching to_agent
        msg = message_factory(
            from_agent='sender-agent',
            to_agent='test-agent'
        )  # correlation_id will be None

        event_data = {
            'current_agent_id': 'test-agent',
            'message': msg,
            'event_id': 'evt-001',
            'sent_at': datetime.now(),
            'from_agent': msg.from_agent,
            'to_agent': msg.to_agent
        }

        # Should handle gracefully (None is valid)
        result = builder.apply_agent_message_sent(event_data, base_state)

        # Should have created the message, preserving None correlation_id
        assert len(result['inbox']) == 1
        assert result['inbox'][0].correlation_id is None  # System preserves None
        assert result['inbox'][0].event_id == 'evt-001'  # event_id is still set

    def test_duplicate_correlation_id_in_different_contexts(
        self, builder, message_factory
    ):
        """Test handling of duplicate correlation_ids across different message contexts."""
        correlation_id = 'duplicate-test-001'
        base_state = {'inbox': [], 'outbox': [], 'conversation_history': []}

        # Create first message with correlation_id
        msg1 = message_factory(
            from_agent='agent-1',
            to_agent='agent-2',
            correlation_id=correlation_id
        )

        event_data1 = {
            'current_agent_id': 'agent-2',
            'message': msg1,
            'event_id': 'evt-001',
            'sent_at': datetime.now(),
            'from_agent': 'agent-1',
            'to_agent': 'agent-2'
        }

        state = builder.apply_agent_message_sent(event_data1, base_state)

        # Create second message with same correlation_id but different agents
        msg2 = message_factory(
            from_agent='agent-3',
            to_agent='agent-4',
            correlation_id=correlation_id  # Same correlation_id
        )

        event_data2 = {
            'current_agent_id': 'agent-4',
            'message': msg2,
            'event_id': 'evt-002',
            'sent_at': datetime.now(),
            'from_agent': 'agent-3',
            'to_agent': 'agent-4'
        }

        state = builder.apply_agent_message_sent(event_data2, state)

        # Should allow duplicate correlation_ids (they might be part of the same conversation)
        assert len(state['inbox']) == 2
        assert state['inbox'][0].correlation_id == correlation_id
        assert state['inbox'][1].correlation_id == correlation_id

    def test_correlation_id_mismatch_in_acknowledgment(self, builder, message_factory):
        """Test handling of correlation_id mismatches in acknowledgment events."""
        # Create initial state with a message
        msg = message_factory(
            from_agent='sender-agent',
            to_agent='test-agent',
            correlation_id='original-thread-001'
        )

        send_event_data = {
            'current_agent_id': 'test-agent',
            'message': msg,
            'event_id': 'evt-001',
            'sent_at': datetime.now(),
            'from_agent': msg.from_agent,
            'to_agent': 'test-agent'
        }

        state = {'inbox': [], 'outbox': [], 'conversation_history': []}
        state = builder.apply_agent_message_sent(send_event_data, state)

        # Try to acknowledge with wrong correlation_id
        wrong_ack_event_data = {
            'correlation_id': 'wrong-event-id',  # This should not match evt-001
            'from_agent': 'test-agent',
            'acknowledged_at': datetime.now(),
            'current_agent_id': 'test-agent'
        }

        result = builder.apply_agent_message_acknowledged(wrong_ack_event_data, state)

        # Should not acknowledge any message due to mismatch
        assert result['inbox'][0].acknowledged is False

        # Try with correct correlation_id (should use event_id, not message's correlation_id)
        correct_ack_event_data = {
            'correlation_id': 'evt-001',  # This matches the event_id
            'from_agent': 'test-agent',
            'acknowledged_at': datetime.now(),
            'current_agent_id': 'test-agent'
        }

        result = builder.apply_agent_message_acknowledged(correct_ack_event_data, state)

        # Should acknowledge the message
        assert result['inbox'][0].acknowledged is True