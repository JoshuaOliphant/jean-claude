# ABOUTME: Test suite for outbox filtering helper methods
# ABOUTME: Tests get_pending_outbox() method to filter outbox messages by completed=False and sort by sent_at timestamp

"""Test suite for outbox filtering helper methods.

This module tests the get_pending_outbox() helper method implementation that provides
filtering functionality for outbox messages based on completion status and
timestamp-based sorting.

Key Test Categories:
- Filtering uncompleted messages (completed=False)
- Timestamp-based sorting (oldest sent_at first)
- Integration with existing outbox state structure
- Edge cases for empty outboxes and various message combinations
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List

from jean_claude.core.mailbox_projection_builder import MailboxProjectionBuilder
from jean_claude.core.mailbox_message_models import OutboxMessage
from jean_claude.core.message import MessagePriority


class TestOutboxFilteringHelpers:
    """Test the get_pending_outbox helper method implementation."""

    @pytest.fixture
    def builder(self):
        """Provide a MailboxProjectionBuilder instance."""
        return MailboxProjectionBuilder()

    @pytest.fixture
    def base_time(self):
        """Provide base datetime for consistent testing."""
        return datetime.now()

    @pytest.fixture
    def sample_outbox_messages(self, base_time):
        """Provide sample outbox messages with different completion statuses and timestamps."""
        messages = []

        # Uncompleted messages with different timestamps (oldest to newest)
        messages.append(OutboxMessage(
            event_id="evt-1",
            message_id="msg-1",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="First Pending",
            body="Oldest pending message",
            priority=MessagePriority.NORMAL,
            created_at=base_time,
            sent_at=base_time,  # Oldest
            completed=False
        ))

        messages.append(OutboxMessage(
            event_id="evt-2",
            message_id="msg-2",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Second Pending",
            body="Second oldest pending message",
            priority=MessagePriority.URGENT,
            created_at=base_time,
            sent_at=base_time + timedelta(minutes=1),
            completed=False
        ))

        # Completed message that should be filtered out
        messages.append(OutboxMessage(
            event_id="evt-3",
            message_id="msg-3",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Completed Message",
            body="This message has been completed",
            priority=MessagePriority.HIGH,
            created_at=base_time,
            sent_at=base_time + timedelta(minutes=2),
            completed=True,
            completed_at=base_time + timedelta(minutes=5),
            success=True
        ))

        messages.append(OutboxMessage(
            event_id="evt-4",
            message_id="msg-4",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Third Pending",
            body="Newest pending message",
            priority=MessagePriority.LOW,
            created_at=base_time,
            sent_at=base_time + timedelta(minutes=3),  # Newest
            completed=False
        ))

        return messages

    @pytest.fixture
    def state_with_mixed_outbox(self, sample_outbox_messages):
        """Provide mailbox state with mixed completed/uncompleted messages."""
        return {
            'inbox': [],
            'outbox': sample_outbox_messages,
            'conversation_history': []
        }

    def test_get_pending_outbox_filters_uncompleted_only(
        self, builder, state_with_mixed_outbox
    ):
        """Test that get_pending_outbox only returns uncompleted messages."""
        pending_messages = builder.get_pending_outbox(state_with_mixed_outbox)

        # Should have 3 uncompleted messages (excluding the completed one)
        assert len(pending_messages) == 3

        # All returned messages should be uncompleted
        for message in pending_messages:
            assert message.completed is False
            assert message.completed_at is None

    def test_get_pending_outbox_sorts_by_sent_at_timestamp(
        self, builder, state_with_mixed_outbox
    ):
        """Test that get_pending_outbox sorts messages by sent_at timestamp (oldest first)."""
        pending_messages = builder.get_pending_outbox(state_with_mixed_outbox)

        # Verify timestamp sorting order (oldest first)
        subjects = [msg.subject for msg in pending_messages]
        expected_subjects = [
            "First Pending",    # evt-1: base_time (oldest)
            "Second Pending",   # evt-2: base_time + 1 min
            "Third Pending"     # evt-4: base_time + 3 min (newest)
        ]
        assert subjects == expected_subjects

        # Verify timestamps are in ascending order
        timestamps = [msg.sent_at for msg in pending_messages]
        assert timestamps == sorted(timestamps)

    def test_get_pending_outbox_empty_outbox_returns_empty_list(self, builder):
        """Test that get_pending_outbox returns empty list for empty outbox."""
        empty_state = {
            'inbox': [],
            'outbox': [],
            'conversation_history': []
        }

        pending_messages = builder.get_pending_outbox(empty_state)
        assert pending_messages == []

    def test_get_pending_outbox_all_completed_returns_empty_list(
        self, builder, base_time
    ):
        """Test that get_pending_outbox returns empty list when all messages are completed."""
        completed_message = OutboxMessage(
            event_id="evt-comp",
            message_id="msg-comp",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Completed Message",
            body="This message has been completed",
            priority=MessagePriority.NORMAL,
            created_at=base_time,
            sent_at=base_time,
            completed=True,
            completed_at=base_time + timedelta(minutes=1),
            success=True
        )

        state = {
            'inbox': [],
            'outbox': [completed_message],
            'conversation_history': []
        }

        pending_messages = builder.get_pending_outbox(state)
        assert pending_messages == []

    def test_get_pending_outbox_multiple_same_timestamp_maintains_stable_order(
        self, builder, base_time
    ):
        """Test that messages with same timestamp maintain stable order."""
        # Create multiple messages at the same timestamp
        same_time = base_time + timedelta(minutes=5)

        msg_1 = OutboxMessage(
            event_id="evt-s1",
            message_id="msg-s1",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Same Time First",
            body="First message at same time",
            priority=MessagePriority.NORMAL,
            created_at=base_time,
            sent_at=same_time,
            completed=False
        )

        msg_2 = OutboxMessage(
            event_id="evt-s2",
            message_id="msg-s2",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Same Time Second",
            body="Second message at same time",
            priority=MessagePriority.HIGH,
            created_at=base_time,
            sent_at=same_time,
            completed=False
        )

        state = {
            'inbox': [],
            'outbox': [msg_2, msg_1],  # Reverse order in state
            'conversation_history': []
        }

        pending_messages = builder.get_pending_outbox(state)

        # Should maintain stable order (original order for same timestamp)
        assert len(pending_messages) == 2
        assert pending_messages[0].subject == "Same Time Second"
        assert pending_messages[1].subject == "Same Time First"

    def test_get_pending_outbox_handles_missing_state_keys_gracefully(self, builder):
        """Test that get_pending_outbox handles malformed state gracefully."""
        # Test with missing outbox key
        malformed_state = {
            'inbox': [],
            'conversation_history': []
        }

        pending_messages = builder.get_pending_outbox(malformed_state)
        assert pending_messages == []

    def test_get_pending_outbox_preserves_original_state(
        self, builder, state_with_mixed_outbox
    ):
        """Test that get_pending_outbox does not modify the original state."""
        original_outbox_length = len(state_with_mixed_outbox['outbox'])
        original_first_message = state_with_mixed_outbox['outbox'][0]

        pending_messages = builder.get_pending_outbox(state_with_mixed_outbox)

        # Original state should be unchanged
        assert len(state_with_mixed_outbox['outbox']) == original_outbox_length
        assert state_with_mixed_outbox['outbox'][0] is original_first_message

        # Returned list should be independent
        assert pending_messages is not state_with_mixed_outbox['outbox']

    def test_get_pending_outbox_mixed_priorities_sorted_by_timestamp_only(
        self, builder, base_time
    ):
        """Test that get_pending_outbox sorts by timestamp regardless of priority."""
        # Create messages with different priorities but specific timestamp order
        urgent_later = OutboxMessage(
            event_id="evt-urgent",
            message_id="msg-urgent",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Urgent but Later",
            body="Urgent message sent later",
            priority=MessagePriority.URGENT,
            created_at=base_time,
            sent_at=base_time + timedelta(minutes=2),  # Later
            completed=False
        )

        low_earlier = OutboxMessage(
            event_id="evt-low",
            message_id="msg-low",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Low but Earlier",
            body="Low priority message sent earlier",
            priority=MessagePriority.LOW,
            created_at=base_time,
            sent_at=base_time,  # Earlier
            completed=False
        )

        state = {
            'inbox': [],
            'outbox': [urgent_later, low_earlier],
            'conversation_history': []
        }

        pending_messages = builder.get_pending_outbox(state)

        # Should be ordered by timestamp, not priority
        assert len(pending_messages) == 2
        assert pending_messages[0].subject == "Low but Earlier"
        assert pending_messages[1].subject == "Urgent but Later"
        assert pending_messages[0].priority == MessagePriority.LOW
        assert pending_messages[1].priority == MessagePriority.URGENT