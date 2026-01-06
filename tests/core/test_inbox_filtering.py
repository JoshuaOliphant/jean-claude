# ABOUTME: Test suite for inbox filtering helper methods
# ABOUTME: Tests get_unread_inbox() method to filter inbox messages by acknowledged=False and priority-based sorting

"""Test suite for inbox filtering helper methods.

This module tests the get_unread_inbox() helper method implementation that provides
filtering functionality for inbox messages based on acknowledgment status and
priority-based sorting.

Key Test Categories:
- Filtering unacknowledged messages (acknowledged=False)
- Priority-based sorting (URGENT > HIGH > NORMAL > LOW)
- Integration with existing inbox state structure
- Edge cases for empty inboxes and various message combinations
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List

from jean_claude.core.mailbox_projection_builder import MailboxProjectionBuilder
from jean_claude.core.mailbox_message_models import InboxMessage
from jean_claude.core.message import MessagePriority


class TestInboxFilteringHelpers:
    """Test the get_unread_inbox helper method implementation."""

    @pytest.fixture
    def builder(self):
        """Provide a MailboxProjectionBuilder instance."""
        return MailboxProjectionBuilder()

    @pytest.fixture
    def base_time(self):
        """Provide base datetime for consistent testing."""
        return datetime.now()

    @pytest.fixture
    def sample_inbox_messages(self, base_time):
        """Provide sample inbox messages with different priorities and acknowledgment status."""
        messages = []

        # Unacknowledged messages with different priorities
        messages.append(InboxMessage(
            event_id="evt-1",
            message_id="msg-1",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Urgent Unread",
            body="Urgent message body",
            priority=MessagePriority.URGENT,
            created_at=base_time,
            received_at=base_time,
            acknowledged=False,
            acknowledged_at=None
        ))

        messages.append(InboxMessage(
            event_id="evt-2",
            message_id="msg-2",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Normal Unread",
            body="Normal priority message",
            priority=MessagePriority.NORMAL,
            created_at=base_time,
            received_at=base_time + timedelta(minutes=1),
            acknowledged=False,
            acknowledged_at=None
        ))

        messages.append(InboxMessage(
            event_id="evt-3",
            message_id="msg-3",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="High Unread",
            body="High priority message",
            priority=MessagePriority.HIGH,
            created_at=base_time,
            received_at=base_time + timedelta(minutes=2),
            acknowledged=False,
            acknowledged_at=None
        ))

        # Acknowledged message that should be filtered out
        messages.append(InboxMessage(
            event_id="evt-4",
            message_id="msg-4",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Urgent Acknowledged",
            body="Acknowledged urgent message",
            priority=MessagePriority.URGENT,
            created_at=base_time,
            received_at=base_time + timedelta(minutes=3),
            acknowledged=True,
            acknowledged_at=base_time + timedelta(minutes=5)
        ))

        messages.append(InboxMessage(
            event_id="evt-5",
            message_id="msg-5",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Low Unread",
            body="Low priority message",
            priority=MessagePriority.LOW,
            created_at=base_time,
            received_at=base_time + timedelta(minutes=4),
            acknowledged=False,
            acknowledged_at=None
        ))

        return messages

    @pytest.fixture
    def state_with_mixed_inbox(self, sample_inbox_messages):
        """Provide mailbox state with mixed acknowledged/unacknowledged messages."""
        return {
            'inbox': sample_inbox_messages,
            'outbox': [],
            'conversation_history': []
        }

    def test_get_unread_inbox_filters_unacknowledged_only(
        self, builder, state_with_mixed_inbox
    ):
        """Test that get_unread_inbox only returns unacknowledged messages."""
        unread_messages = builder.get_unread_inbox(state_with_mixed_inbox)

        # Should have 4 unacknowledged messages (excluding the acknowledged urgent one)
        assert len(unread_messages) == 4

        # All returned messages should be unacknowledged
        for message in unread_messages:
            assert message.acknowledged is False
            assert message.acknowledged_at is None

    def test_get_unread_inbox_sorts_by_priority(
        self, builder, state_with_mixed_inbox
    ):
        """Test that get_unread_inbox sorts messages by priority (URGENT > HIGH > NORMAL > LOW)."""
        unread_messages = builder.get_unread_inbox(state_with_mixed_inbox)

        # Verify priority sorting order
        priorities = [msg.priority for msg in unread_messages]
        expected_priorities = [
            MessagePriority.URGENT,   # evt-1: Urgent Unread
            MessagePriority.HIGH,     # evt-3: High Unread
            MessagePriority.NORMAL,   # evt-2: Normal Unread
            MessagePriority.LOW       # evt-5: Low Unread
        ]
        assert priorities == expected_priorities

        # Verify specific messages are in correct order
        subjects = [msg.subject for msg in unread_messages]
        expected_subjects = [
            "Urgent Unread",
            "High Unread",
            "Normal Unread",
            "Low Unread"
        ]
        assert subjects == expected_subjects

    def test_get_unread_inbox_empty_inbox_returns_empty_list(self, builder):
        """Test that get_unread_inbox returns empty list for empty inbox."""
        empty_state = {
            'inbox': [],
            'outbox': [],
            'conversation_history': []
        }

        unread_messages = builder.get_unread_inbox(empty_state)
        assert unread_messages == []

    def test_get_unread_inbox_all_acknowledged_returns_empty_list(
        self, builder, base_time
    ):
        """Test that get_unread_inbox returns empty list when all messages are acknowledged."""
        acknowledged_message = InboxMessage(
            event_id="evt-ack",
            message_id="msg-ack",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Acknowledged Message",
            body="This message has been acknowledged",
            priority=MessagePriority.NORMAL,
            created_at=base_time,
            received_at=base_time,
            acknowledged=True,
            acknowledged_at=base_time + timedelta(minutes=1)
        )

        state = {
            'inbox': [acknowledged_message],
            'outbox': [],
            'conversation_history': []
        }

        unread_messages = builder.get_unread_inbox(state)
        assert unread_messages == []

    def test_get_unread_inbox_multiple_same_priority_maintains_stable_order(
        self, builder, base_time
    ):
        """Test that messages with same priority maintain stable order (by received_at)."""
        # Create multiple normal priority messages at different times
        normal_msg_1 = InboxMessage(
            event_id="evt-n1",
            message_id="msg-n1",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Normal First",
            body="First normal message",
            priority=MessagePriority.NORMAL,
            created_at=base_time,
            received_at=base_time,
            acknowledged=False
        )

        normal_msg_2 = InboxMessage(
            event_id="evt-n2",
            message_id="msg-n2",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Normal Second",
            body="Second normal message",
            priority=MessagePriority.NORMAL,
            created_at=base_time,
            received_at=base_time + timedelta(minutes=1),
            acknowledged=False
        )

        state = {
            'inbox': [normal_msg_2, normal_msg_1],  # Reverse order in state
            'outbox': [],
            'conversation_history': []
        }

        unread_messages = builder.get_unread_inbox(state)

        # Should maintain received_at order for same priority (oldest first)
        assert len(unread_messages) == 2
        assert unread_messages[0].subject == "Normal First"
        assert unread_messages[1].subject == "Normal Second"

    def test_get_unread_inbox_handles_missing_state_keys_gracefully(self, builder):
        """Test that get_unread_inbox handles malformed state gracefully."""
        # Test with missing inbox key
        malformed_state = {
            'outbox': [],
            'conversation_history': []
        }

        unread_messages = builder.get_unread_inbox(malformed_state)
        assert unread_messages == []

    def test_get_unread_inbox_preserves_original_state(
        self, builder, state_with_mixed_inbox
    ):
        """Test that get_unread_inbox does not modify the original state."""
        original_inbox_length = len(state_with_mixed_inbox['inbox'])
        original_first_message = state_with_mixed_inbox['inbox'][0]

        unread_messages = builder.get_unread_inbox(state_with_mixed_inbox)

        # Original state should be unchanged
        assert len(state_with_mixed_inbox['inbox']) == original_inbox_length
        assert state_with_mixed_inbox['inbox'][0] is original_first_message

        # Returned list should be independent
        assert unread_messages is not state_with_mixed_inbox['inbox']