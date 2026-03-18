# ABOUTME: Test suite for message priority handling logic in MailboxProjectionBuilder
# ABOUTME: Tests priority-based inbox sorting and priority-based message retrieval

"""Test suite for message priority handling implementation.

Tests priority-based sorting, retrieval, filtering, statistics,
and edge cases for the MailboxProjectionBuilder.
"""

import pytest
from datetime import datetime, timedelta

from jean_claude.core.mailbox_projection_builder import MailboxProjectionBuilder
from jean_claude.core.mailbox_message_models import InboxMessage, OutboxMessage, ConversationMessage
from jean_claude.core.message import Message, MessagePriority


@pytest.fixture
def builder():
    return MailboxProjectionBuilder()


@pytest.fixture
def mixed_priority_state(message_factory):
    """State with inbox messages of different priorities."""
    now = datetime.now()
    msgs = []
    for subj, from_a, priority, mins_ago in [
        ('Critical System Alert', 'system-agent', MessagePriority.URGENT, 30),
        ('Regular Question', 'user-agent', MessagePriority.NORMAL, 45),
        ('Important Update Required', 'admin-agent', MessagePriority.HIGH, 15),
        ('Weekly Report', 'info-agent', MessagePriority.LOW, 5),
        ('Another Question', 'another-user', MessagePriority.NORMAL, 20),
    ]:
        msgs.append(InboxMessage.from_message(
            message=message_factory(from_agent=from_a, to_agent='support-agent',
                                    subject=subj, body=subj, priority=priority),
            event_id=f'evt-{subj[:8].lower().replace(" ", "-")}',
            received_at=now - timedelta(minutes=mins_ago)
        ))
    return {'inbox': msgs, 'outbox': [], 'conversation_history': []}


@pytest.fixture
def full_priority_state(message_factory):
    """State with priority messages across inbox, outbox, and history."""
    now = datetime.now()
    inbox = [
        InboxMessage.from_message(
            message=message_factory(subject='Inbox Urgent', priority=MessagePriority.URGENT),
            event_id='inbox-urgent', received_at=now),
        InboxMessage.from_message(
            message=message_factory(subject='Inbox Normal', priority=MessagePriority.NORMAL),
            event_id='inbox-normal', received_at=now),
    ]
    outbox = [
        OutboxMessage.from_message(
            message=message_factory(subject='Outbox High', priority=MessagePriority.HIGH),
            event_id='outbox-high', sent_at=now),
        OutboxMessage.from_message(
            message=message_factory(subject='Outbox Low', priority=MessagePriority.LOW),
            event_id='outbox-low', sent_at=now),
    ]
    history = [
        ConversationMessage(
            event_id='hist-urgent', message_id='msg-u', from_agent='a1', to_agent='a2',
            subject='History Urgent', body='Urgent', priority=MessagePriority.URGENT,
            created_at=now - timedelta(minutes=60), sent_at=now - timedelta(minutes=59),
            completed_at=now - timedelta(minutes=30), success=True, correlation_id='c1'),
        ConversationMessage(
            event_id='hist-normal', message_id='msg-n', from_agent='a2', to_agent='a1',
            subject='History Normal', body='Normal', priority=MessagePriority.NORMAL,
            created_at=now - timedelta(minutes=50), sent_at=now - timedelta(minutes=49),
            completed_at=now - timedelta(minutes=25), success=True, correlation_id='c2'),
    ]
    return {'inbox': inbox, 'outbox': outbox, 'conversation_history': history}


class TestPriorityBasedInboxSorting:
    """Test priority-based sorting of inbox messages."""

    def test_unread_inbox_sorted_by_priority_then_time(self, builder, mixed_priority_state):
        """Test unread inbox sorts by priority (URGENT>HIGH>NORMAL>LOW) then by time."""
        unread = builder.get_unread_inbox(mixed_priority_state)
        assert len(unread) == 5

        priorities = [msg.priority for msg in unread]
        assert priorities == [MessagePriority.URGENT, MessagePriority.HIGH,
                              MessagePriority.NORMAL, MessagePriority.NORMAL, MessagePriority.LOW]

        # Same-priority messages sorted by time (older first)
        normals = [m for m in unread if m.priority == MessagePriority.NORMAL]
        assert normals[0].received_at < normals[1].received_at
        assert normals[0].subject == 'Regular Question'

    def test_acknowledged_messages_filtered_out(self, builder, mixed_priority_state):
        """Test acknowledged messages don't appear in unread inbox."""
        mixed_priority_state['inbox'][0].acknowledge(datetime.now())
        unread = builder.get_unread_inbox(mixed_priority_state)
        assert len(unread) == 4
        assert unread[0].priority == MessagePriority.HIGH


class TestPriorityBasedRetrieval:
    """Test priority-based message retrieval methods."""

    def test_get_messages_by_priority_and_threshold(self, builder, mixed_priority_state):
        """Test retrieval by priority level and above-threshold queries."""
        # By specific priority
        assert len(builder.get_messages_by_priority(mixed_priority_state, MessagePriority.URGENT)) == 1
        assert len(builder.get_messages_by_priority(mixed_priority_state, MessagePriority.NORMAL)) == 2
        assert len(builder.get_messages_by_priority(mixed_priority_state, MessagePriority.LOW)) == 1

        # High/Low convenience methods
        high = builder.get_high_priority_messages(mixed_priority_state)
        assert len(high) == 2
        assert high[0].priority == MessagePriority.URGENT
        assert high[1].priority == MessagePriority.HIGH

        assert len(builder.get_low_priority_messages(mixed_priority_state)) == 1

        # Above threshold
        assert len(builder.get_messages_above_priority(mixed_priority_state, MessagePriority.NORMAL)) == 2
        assert len(builder.get_messages_above_priority(mixed_priority_state, MessagePriority.LOW)) == 4
        assert len(builder.get_messages_above_priority(mixed_priority_state, MessagePriority.URGENT)) == 0


class TestPriorityAcrossStores:
    """Test priority handling across inbox, outbox, and history."""

    def test_priority_retrieval_across_all_stores(self, builder, full_priority_state):
        """Test priority-based retrieval across inbox, outbox, and conversation history."""
        # All stores
        urgent_all = builder.get_messages_by_priority(full_priority_state, MessagePriority.URGENT, include_all_stores=True)
        assert len(urgent_all) == 2
        subjects = [m.subject for m in urgent_all]
        assert 'Inbox Urgent' in subjects and 'History Urgent' in subjects

        # Outbox-specific
        assert len(builder.get_outbox_messages_by_priority(full_priority_state, MessagePriority.HIGH)) == 1
        assert len(builder.get_outbox_messages_by_priority(full_priority_state, MessagePriority.URGENT)) == 0

        # History-specific
        assert len(builder.get_conversation_messages_by_priority(full_priority_state, MessagePriority.URGENT)) == 1
        assert len(builder.get_conversation_messages_by_priority(full_priority_state, MessagePriority.NORMAL)) == 1


class TestPriorityStatistics:
    """Test priority distribution and summary statistics."""

    def test_distribution_and_summary(self, builder, full_priority_state):
        """Test priority distribution and summary statistics."""
        dist = builder.get_priority_distribution(full_priority_state)
        assert dist['total_messages'] == 6
        assert dist['by_priority'][MessagePriority.URGENT] == 2
        assert dist['by_priority'][MessagePriority.HIGH] == 1
        assert dist['by_priority'][MessagePriority.NORMAL] == 2
        assert dist['by_priority'][MessagePriority.LOW] == 1
        assert dist['by_store']['inbox'][MessagePriority.URGENT] == 1

        summary = builder.get_priority_summary(full_priority_state)
        assert summary['total_messages'] == 6
        assert summary['urgent_count'] == 2
        assert summary['high_priority_count'] == 3
        assert summary['low_priority_count'] == 1

    def test_has_urgent_and_next_priority(self, builder, full_priority_state):
        """Test has_urgent_messages and get_next_priority_message."""
        assert builder.has_urgent_messages(full_priority_state) is True

        next_msg = builder.get_next_priority_message(full_priority_state)
        assert next_msg.priority == MessagePriority.URGENT
        assert next_msg.subject == 'Inbox Urgent'

        full_priority_state['inbox'][0].acknowledge(datetime.now())
        next_msg2 = builder.get_next_priority_message(full_priority_state)
        assert next_msg2.priority == MessagePriority.NORMAL


class TestPriorityEdgeCases:
    """Test edge cases for priority functionality."""

    def test_empty_state_edge_cases(self, builder):
        """Test all priority methods with empty state."""
        empty = {'inbox': [], 'outbox': [], 'conversation_history': []}
        assert len(builder.get_messages_by_priority(empty, MessagePriority.URGENT)) == 0
        assert len(builder.get_high_priority_messages(empty)) == 0
        assert len(builder.get_low_priority_messages(empty)) == 0
        assert builder.get_priority_distribution(empty)['total_messages'] == 0
        assert builder.get_priority_summary(empty)['urgent_count'] == 0
        assert builder.has_urgent_messages(empty) is False
        assert builder.get_next_priority_message(empty) is None

    def test_all_acknowledged_edge_case(self, builder, mixed_priority_state):
        """Test when all messages are acknowledged."""
        for msg in mixed_priority_state['inbox']:
            msg.acknowledge(datetime.now())

        assert len(builder.get_unread_inbox(mixed_priority_state)) == 0
        assert builder.get_next_priority_message(mixed_priority_state) is None
        # General priority methods still find acknowledged messages
        assert len(builder.get_messages_by_priority(mixed_priority_state, MessagePriority.URGENT)) == 1

    def test_same_priority_different_timestamps(self, builder, message_factory):
        """Test same-priority messages sorted by time (older first)."""
        now = datetime.now()
        state = {
            'inbox': [
                InboxMessage.from_message(
                    message=message_factory(subject='Second Normal', priority=MessagePriority.NORMAL),
                    event_id='e2', received_at=now),
                InboxMessage.from_message(
                    message=message_factory(subject='First Normal', priority=MessagePriority.NORMAL),
                    event_id='e1', received_at=now - timedelta(hours=1)),
            ],
            'outbox': [], 'conversation_history': []
        }
        unread = builder.get_unread_inbox(state)
        assert unread[0].subject == 'First Normal'
        assert unread[1].subject == 'Second Normal'
