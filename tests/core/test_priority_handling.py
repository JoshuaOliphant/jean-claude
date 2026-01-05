# ABOUTME: Test suite for message priority handling logic in MailboxProjectionBuilder
# ABOUTME: Tests priority-based inbox sorting and priority-based message retrieval

"""Test suite for message priority handling implementation.

This module tests the priority handling functionality that provides:
- Priority-based sorting of inbox messages (URGENT > HIGH > NORMAL > LOW)
- Priority-based message retrieval methods
- Priority filtering and querying capabilities
- Integration with existing mailbox projection functionality

The tests cover priority sorting, retrieval methods, filtering,
and edge cases for priority handling.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from jean_claude.core.mailbox_projection_builder import MailboxProjectionBuilder
from jean_claude.core.mailbox_message_models import InboxMessage, OutboxMessage, ConversationMessage
from jean_claude.core.message import Message, MessagePriority


# =============================================================================
# Module-Level Fixtures (shared across all test classes)
# =============================================================================

@pytest.fixture
def builder():
    """Provide a MailboxProjectionBuilder instance."""
    return MailboxProjectionBuilder()


@pytest.fixture
def mixed_priority_state(message_factory):
    """Provide state with messages of different priorities."""
    now = datetime.now()

    # Create messages with different priorities
    urgent_msg = InboxMessage.from_message(
        message=message_factory(
            from_agent='system-agent',
            to_agent='support-agent',
            subject='Critical System Alert',
            body='Critical system failure detected',
            priority=MessagePriority.URGENT
        ),
        event_id='evt-urgent-001',
        received_at=now - timedelta(minutes=30)
    )

    normal_msg1 = InboxMessage.from_message(
        message=message_factory(
            from_agent='user-agent',
            to_agent='support-agent',
            subject='Regular Question',
            body='I have a question',
            priority=MessagePriority.NORMAL
        ),
        event_id='evt-normal-001',
        received_at=now - timedelta(minutes=45)  # Older but normal priority
    )

    high_msg = InboxMessage.from_message(
        message=message_factory(
            from_agent='admin-agent',
            to_agent='support-agent',
            subject='Important Update Required',
            body='Important system update needed',
            priority=MessagePriority.HIGH
        ),
        event_id='evt-high-001',
        received_at=now - timedelta(minutes=15)  # Newer but high priority
    )

    low_msg = InboxMessage.from_message(
        message=message_factory(
            from_agent='info-agent',
            to_agent='support-agent',
            subject='Weekly Report',
            body='Here is the weekly report',
            priority=MessagePriority.LOW
        ),
        event_id='evt-low-001',
        received_at=now - timedelta(minutes=5)  # Newest but low priority
    )

    normal_msg2 = InboxMessage.from_message(
        message=message_factory(
            from_agent='another-user-agent',
            to_agent='support-agent',
            subject='Another Question',
            body='Another regular question',
            priority=MessagePriority.NORMAL
        ),
        event_id='evt-normal-002',
        received_at=now - timedelta(minutes=20)  # Between high and urgent
    )

    return {
        'inbox': [urgent_msg, normal_msg1, high_msg, low_msg, normal_msg2],
        'outbox': [],
        'conversation_history': []
    }


@pytest.fixture
def full_priority_state(message_factory):
    """Provide state with priority messages across all stores."""
    now = datetime.now()

    # Inbox messages
    inbox_urgent = InboxMessage.from_message(
        message=message_factory(
            subject='Inbox Urgent',
            priority=MessagePriority.URGENT
        ),
        event_id='inbox-urgent-001',
        received_at=now
    )

    inbox_normal = InboxMessage.from_message(
        message=message_factory(
            subject='Inbox Normal',
            priority=MessagePriority.NORMAL
        ),
        event_id='inbox-normal-001',
        received_at=now
    )

    # Outbox messages
    outbox_high = OutboxMessage.from_message(
        message=message_factory(
            subject='Outbox High',
            priority=MessagePriority.HIGH
        ),
        event_id='outbox-high-001',
        sent_at=now
    )

    outbox_low = OutboxMessage.from_message(
        message=message_factory(
            subject='Outbox Low',
            priority=MessagePriority.LOW
        ),
        event_id='outbox-low-001',
        sent_at=now
    )

    # Conversation history
    history_urgent = ConversationMessage(
        event_id='hist-urgent-001',
        message_id='msg-urgent-hist',
        from_agent='agent-1',
        to_agent='agent-2',
        subject='History Urgent',
        body='Urgent message in history',
        priority=MessagePriority.URGENT,
        created_at=now - timedelta(minutes=60),
        sent_at=now - timedelta(minutes=59),
        completed_at=now - timedelta(minutes=30),
        success=True,
        correlation_id='hist-corr-001'
    )

    history_normal = ConversationMessage(
        event_id='hist-normal-001',
        message_id='msg-normal-hist',
        from_agent='agent-2',
        to_agent='agent-1',
        subject='History Normal',
        body='Normal message in history',
        priority=MessagePriority.NORMAL,
        created_at=now - timedelta(minutes=50),
        sent_at=now - timedelta(minutes=49),
        completed_at=now - timedelta(minutes=25),
        success=True,
        correlation_id='hist-corr-002'
    )

    return {
        'inbox': [inbox_urgent, inbox_normal],
        'outbox': [outbox_high, outbox_low],
        'conversation_history': [history_urgent, history_normal]
    }


class TestPriorityBasedInboxSorting:
    """Test priority-based sorting of inbox messages."""

    # Uses module-level fixtures: builder, mixed_priority_state

    def test_get_unread_inbox_priority_sorting(self, builder, mixed_priority_state):
        """Test that get_unread_inbox returns messages sorted by priority."""
        unread_messages = builder.get_unread_inbox(mixed_priority_state)

        # Should have all messages (all unacknowledged)
        assert len(unread_messages) == 5

        # Check priority order: URGENT > HIGH > NORMAL > LOW
        priorities = [msg.priority for msg in unread_messages]
        expected_priorities = [
            MessagePriority.URGENT,
            MessagePriority.HIGH,
            MessagePriority.NORMAL,
            MessagePriority.NORMAL,
            MessagePriority.LOW
        ]
        assert priorities == expected_priorities

    def test_get_unread_inbox_secondary_sort_by_received_at(self, builder, mixed_priority_state):
        """Test that messages of same priority are sorted by received_at (older first)."""
        unread_messages = builder.get_unread_inbox(mixed_priority_state)

        # Find the two NORMAL priority messages
        normal_messages = [msg for msg in unread_messages if msg.priority == MessagePriority.NORMAL]
        assert len(normal_messages) == 2

        # Check they are sorted by received_at (older first)
        assert normal_messages[0].received_at < normal_messages[1].received_at
        assert normal_messages[0].subject == 'Regular Question'  # Received 45 min ago
        assert normal_messages[1].subject == 'Another Question'  # Received 20 min ago

    def test_get_unread_inbox_filters_acknowledged_messages(self, builder, mixed_priority_state):
        """Test that acknowledged messages are filtered out."""
        # Acknowledge the urgent message
        mixed_priority_state['inbox'][0].acknowledge(datetime.now())

        unread_messages = builder.get_unread_inbox(mixed_priority_state)

        # Should have 4 messages (urgent one acknowledged)
        assert len(unread_messages) == 4

        # First message should now be HIGH priority
        assert unread_messages[0].priority == MessagePriority.HIGH
        assert unread_messages[0].subject == 'Important Update Required'


class TestPriorityBasedRetrieval:
    """Test priority-based message retrieval methods."""

    # Uses module-level fixtures: builder, mixed_priority_state

    def test_get_messages_by_priority(self, builder, mixed_priority_state):
        """Test retrieval of messages by specific priority level."""
        # Test URGENT priority
        urgent_messages = builder.get_messages_by_priority(
            mixed_priority_state, MessagePriority.URGENT
        )
        assert len(urgent_messages) == 1
        assert urgent_messages[0].subject == 'Critical System Alert'

        # Test NORMAL priority
        normal_messages = builder.get_messages_by_priority(
            mixed_priority_state, MessagePriority.NORMAL
        )
        assert len(normal_messages) == 2
        subjects = [msg.subject for msg in normal_messages]
        assert 'Regular Question' in subjects
        assert 'Another Question' in subjects

        # Test LOW priority
        low_messages = builder.get_messages_by_priority(
            mixed_priority_state, MessagePriority.LOW
        )
        assert len(low_messages) == 1
        assert low_messages[0].subject == 'Weekly Report'

    def test_get_high_priority_messages(self, builder, mixed_priority_state):
        """Test retrieval of high priority messages (URGENT and HIGH)."""
        high_priority_messages = builder.get_high_priority_messages(mixed_priority_state)

        assert len(high_priority_messages) == 2
        priorities = [msg.priority for msg in high_priority_messages]
        assert MessagePriority.URGENT in priorities
        assert MessagePriority.HIGH in priorities

        # Check they're sorted by priority
        assert high_priority_messages[0].priority == MessagePriority.URGENT
        assert high_priority_messages[1].priority == MessagePriority.HIGH

    def test_get_low_priority_messages(self, builder, mixed_priority_state):
        """Test retrieval of low priority messages (LOW only)."""
        low_priority_messages = builder.get_low_priority_messages(mixed_priority_state)

        assert len(low_priority_messages) == 1
        assert low_priority_messages[0].priority == MessagePriority.LOW
        assert low_priority_messages[0].subject == 'Weekly Report'

    def test_get_messages_above_priority(self, builder, mixed_priority_state):
        """Test retrieval of messages above a certain priority threshold."""
        # Get messages above NORMAL (should include URGENT and HIGH)
        above_normal = builder.get_messages_above_priority(
            mixed_priority_state, MessagePriority.NORMAL
        )
        assert len(above_normal) == 2
        priorities = [msg.priority for msg in above_normal]
        assert MessagePriority.URGENT in priorities
        assert MessagePriority.HIGH in priorities

        # Get messages above LOW (should include URGENT, HIGH, and NORMAL)
        above_low = builder.get_messages_above_priority(
            mixed_priority_state, MessagePriority.LOW
        )
        assert len(above_low) == 4

        # Get messages above URGENT (should be empty)
        above_urgent = builder.get_messages_above_priority(
            mixed_priority_state, MessagePriority.URGENT
        )
        assert len(above_urgent) == 0


class TestPriorityHandlingWithOutboxAndHistory:
    """Test priority handling across outbox and conversation history."""

    # Uses module-level fixtures: builder, full_priority_state

    def test_get_all_messages_by_priority_across_stores(self, builder, full_priority_state):
        """Test priority-based retrieval across all message stores."""
        # Test URGENT across all stores
        urgent_all = builder.get_messages_by_priority(
            full_priority_state, MessagePriority.URGENT, include_all_stores=True
        )
        assert len(urgent_all) == 2  # One in inbox, one in history
        subjects = [msg.subject for msg in urgent_all]
        assert 'Inbox Urgent' in subjects
        assert 'History Urgent' in subjects

        # Test NORMAL across all stores
        normal_all = builder.get_messages_by_priority(
            full_priority_state, MessagePriority.NORMAL, include_all_stores=True
        )
        assert len(normal_all) == 2  # One in inbox, one in history

    def test_get_outbox_messages_by_priority(self, builder, full_priority_state):
        """Test priority-based retrieval from outbox specifically."""
        outbox_high = builder.get_outbox_messages_by_priority(
            full_priority_state, MessagePriority.HIGH
        )
        assert len(outbox_high) == 1
        assert outbox_high[0].subject == 'Outbox High'

        outbox_low = builder.get_outbox_messages_by_priority(
            full_priority_state, MessagePriority.LOW
        )
        assert len(outbox_low) == 1
        assert outbox_low[0].subject == 'Outbox Low'

        # Test priority not in outbox
        outbox_urgent = builder.get_outbox_messages_by_priority(
            full_priority_state, MessagePriority.URGENT
        )
        assert len(outbox_urgent) == 0

    def test_get_conversation_messages_by_priority(self, builder, full_priority_state):
        """Test priority-based retrieval from conversation history."""
        history_urgent = builder.get_conversation_messages_by_priority(
            full_priority_state, MessagePriority.URGENT
        )
        assert len(history_urgent) == 1
        assert history_urgent[0].subject == 'History Urgent'

        history_normal = builder.get_conversation_messages_by_priority(
            full_priority_state, MessagePriority.NORMAL
        )
        assert len(history_normal) == 1
        assert history_normal[0].subject == 'History Normal'


class TestPriorityStatisticsAndAnalysis:
    """Test priority-based statistics and analysis."""

    # Uses module-level fixtures: builder, full_priority_state

    def test_get_priority_distribution(self, builder, full_priority_state):
        """Test priority distribution analysis."""
        distribution = builder.get_priority_distribution(full_priority_state)

        # Check overall distribution
        assert distribution['total_messages'] == 6
        assert distribution['by_priority'][MessagePriority.URGENT] == 2
        assert distribution['by_priority'][MessagePriority.HIGH] == 1
        assert distribution['by_priority'][MessagePriority.NORMAL] == 2
        assert distribution['by_priority'][MessagePriority.LOW] == 1

        # Check store-specific distribution
        assert distribution['by_store']['inbox'][MessagePriority.URGENT] == 1
        assert distribution['by_store']['outbox'][MessagePriority.HIGH] == 1
        assert distribution['by_store']['conversation_history'][MessagePriority.URGENT] == 1

    def test_get_priority_summary(self, builder, full_priority_state):
        """Test priority summary statistics."""
        summary = builder.get_priority_summary(full_priority_state)

        assert summary['total_messages'] == 6
        assert summary['urgent_count'] == 2
        assert summary['high_priority_count'] == 3  # URGENT + HIGH
        assert summary['low_priority_count'] == 1
        assert summary['priority_percentage'][MessagePriority.URGENT] == pytest.approx(33.33, rel=1e-2)
        assert summary['priority_percentage'][MessagePriority.NORMAL] == pytest.approx(33.33, rel=1e-2)

    def test_has_urgent_messages(self, builder, full_priority_state):
        """Test quick check for urgent messages."""
        assert builder.has_urgent_messages(full_priority_state) is True

        # Test with state that has no urgent messages
        no_urgent_state = {
            'inbox': [],
            'outbox': full_priority_state['outbox'],  # Only HIGH and LOW
            'conversation_history': [full_priority_state['conversation_history'][1]]  # Only NORMAL
        }

        assert builder.has_urgent_messages(no_urgent_state) is False

    def test_get_next_priority_message(self, builder, full_priority_state):
        """Test getting the next highest priority unread message."""
        next_message = builder.get_next_priority_message(full_priority_state)

        # Should return the URGENT message from inbox (unread)
        assert next_message is not None
        assert next_message.priority == MessagePriority.URGENT
        assert next_message.subject == 'Inbox Urgent'

        # Acknowledge the urgent message and test again
        full_priority_state['inbox'][0].acknowledge(datetime.now())

        next_message = builder.get_next_priority_message(full_priority_state)

        # Should now return the NORMAL message from inbox (next highest unread)
        assert next_message is not None
        assert next_message.priority == MessagePriority.NORMAL
        assert next_message.subject == 'Inbox Normal'


class TestPriorityEdgeCases:
    """Test edge cases and error handling for priority functionality."""

    # Uses module-level fixtures: builder, mixed_priority_state

    def test_priority_handling_with_empty_state(self, builder):
        """Test priority handling methods with empty state."""
        empty_state = {'inbox': [], 'outbox': [], 'conversation_history': []}

        # All retrieval methods should return empty lists
        assert len(builder.get_messages_by_priority(empty_state, MessagePriority.URGENT)) == 0
        assert len(builder.get_high_priority_messages(empty_state)) == 0
        assert len(builder.get_low_priority_messages(empty_state)) == 0

        # Statistics methods should handle empty state
        distribution = builder.get_priority_distribution(empty_state)
        assert distribution['total_messages'] == 0

        summary = builder.get_priority_summary(empty_state)
        assert summary['total_messages'] == 0
        assert summary['urgent_count'] == 0

        # Boolean checks should return False
        assert builder.has_urgent_messages(empty_state) is False

        # Next priority message should be None
        assert builder.get_next_priority_message(empty_state) is None

    def test_priority_handling_with_all_acknowledged_messages(self, builder, mixed_priority_state):
        """Test priority handling when all inbox messages are acknowledged."""
        # Acknowledge all inbox messages
        for msg in mixed_priority_state['inbox']:
            msg.acknowledge(datetime.now())

        # Unread-specific methods should return empty
        unread_messages = builder.get_unread_inbox(mixed_priority_state)
        assert len(unread_messages) == 0

        next_message = builder.get_next_priority_message(mixed_priority_state)
        assert next_message is None

        # But general priority methods should still work
        all_urgent = builder.get_messages_by_priority(
            mixed_priority_state, MessagePriority.URGENT
        )
        assert len(all_urgent) == 1  # Still finds the acknowledged urgent message

    def test_priority_comparison_edge_cases(self, builder, message_factory):
        """Test priority comparison edge cases."""
        now = datetime.now()

        # Messages with same priority but different timestamps
        msg1 = InboxMessage.from_message(
            message=message_factory(
                subject='First Normal',
                priority=MessagePriority.NORMAL
            ),
            event_id='evt-001',
            received_at=now - timedelta(hours=1)  # Older
        )

        msg2 = InboxMessage.from_message(
            message=message_factory(
                subject='Second Normal',
                priority=MessagePriority.NORMAL
            ),
            event_id='evt-002',
            received_at=now  # Newer
        )

        state = {
            'inbox': [msg2, msg1],  # Newer first in list
            'outbox': [],
            'conversation_history': []
        }

        # Should be sorted by priority first, then by received_at (older first)
        unread_messages = builder.get_unread_inbox(state)
        assert len(unread_messages) == 2
        assert unread_messages[0].subject == 'First Normal'  # Older message first
        assert unread_messages[1].subject == 'Second Normal'