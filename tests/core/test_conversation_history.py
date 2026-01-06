# ABOUTME: Test suite for conversation history helper methods
# ABOUTME: Tests get_conversation() method to return conversation_history messages in chronological order with optional filtering by agent

"""Test suite for conversation history helper methods.

This module tests the get_conversation() helper method implementation that provides
filtering and sorting functionality for conversation history messages based on
agent filtering and chronological ordering.

Key Test Categories:
- Chronological ordering by completed_at timestamp
- Agent-based filtering (optional)
- Integration with existing conversation_history state structure
- Edge cases for empty histories and various message combinations
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from jean_claude.core.mailbox_projection_builder import MailboxProjectionBuilder
from jean_claude.core.mailbox_message_models import ConversationMessage
from jean_claude.core.message import MessagePriority


class TestConversationHistoryHelpers:
    """Test the get_conversation helper method implementation."""

    @pytest.fixture
    def builder(self):
        """Provide a MailboxProjectionBuilder instance."""
        return MailboxProjectionBuilder()

    @pytest.fixture
    def base_time(self):
        """Provide base datetime for consistent testing."""
        return datetime.now()

    @pytest.fixture
    def sample_conversation_messages(self, base_time):
        """Provide sample conversation messages with different timestamps and agents."""
        messages = []

        # Mixed conversation messages with different completion times
        messages.append(ConversationMessage(
            event_id="evt-1",
            message_id="msg-1",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="First Conversation",
            body="First message in history",
            priority=MessagePriority.NORMAL,
            created_at=base_time,
            sent_at=base_time + timedelta(minutes=1),
            completed_at=base_time + timedelta(minutes=10),  # Middle completion time
            success=True,
            correlation_id="corr-1"
        ))

        messages.append(ConversationMessage(
            event_id="evt-2",
            message_id="msg-2",
            from_agent="agent-2",
            to_agent="agent-1",
            subject="Second Conversation",
            body="Response message",
            priority=MessagePriority.HIGH,
            created_at=base_time + timedelta(minutes=5),
            sent_at=base_time + timedelta(minutes=6),
            completed_at=base_time + timedelta(minutes=5),  # Earliest completion time
            success=True,
            correlation_id="corr-2"
        ))

        messages.append(ConversationMessage(
            event_id="evt-3",
            message_id="msg-3",
            from_agent="agent-1",
            to_agent="agent-3",
            subject="Third Conversation",
            body="Message to third agent",
            priority=MessagePriority.URGENT,
            created_at=base_time + timedelta(minutes=15),
            sent_at=base_time + timedelta(minutes=16),
            completed_at=base_time + timedelta(minutes=20),  # Latest completion time
            success=False,
            correlation_id="corr-3"
        ))

        messages.append(ConversationMessage(
            event_id="evt-4",
            message_id="msg-4",
            from_agent="agent-3",
            to_agent="agent-2",
            subject="Fourth Conversation",
            body="Message between agent-3 and agent-2",
            priority=MessagePriority.LOW,
            created_at=base_time + timedelta(minutes=12),
            sent_at=base_time + timedelta(minutes=13),
            completed_at=base_time + timedelta(minutes=15),  # Second latest completion time
            success=True,
            correlation_id="corr-4"
        ))

        return messages

    @pytest.fixture
    def state_with_conversation_history(self, sample_conversation_messages):
        """Provide mailbox state with conversation history."""
        return {
            'inbox': [],
            'outbox': [],
            'conversation_history': sample_conversation_messages
        }

    def test_get_conversation_returns_all_messages_in_chronological_order(
        self, builder, state_with_conversation_history
    ):
        """Test that get_conversation returns all messages sorted by completed_at timestamp."""
        conversation = builder.get_conversation(state_with_conversation_history)

        # Should have all 4 messages
        assert len(conversation) == 4

        # Should be ordered by completed_at (earliest first)
        subjects = [msg.subject for msg in conversation]
        expected_subjects = [
            "Second Conversation",   # completed at base_time + 5 min (earliest)
            "First Conversation",    # completed at base_time + 10 min
            "Fourth Conversation",   # completed at base_time + 15 min
            "Third Conversation"     # completed at base_time + 20 min (latest)
        ]
        assert subjects == expected_subjects

        # Verify timestamps are in ascending order
        timestamps = [msg.completed_at for msg in conversation]
        assert timestamps == sorted(timestamps)

    def test_get_conversation_filters_by_agent_sender(
        self, builder, state_with_conversation_history
    ):
        """Test that get_conversation filters by agent (either from_agent or to_agent) when specified."""
        conversation = builder.get_conversation(state_with_conversation_history, agent="agent-1")

        # Should have 3 messages involving agent-1 (either as sender or recipient)
        assert len(conversation) == 3

        # All returned messages should involve agent-1 (either as sender or recipient)
        for message in conversation:
            assert message.from_agent == "agent-1" or message.to_agent == "agent-1"

        # Should still be in chronological order by completed_at
        subjects = [msg.subject for msg in conversation]
        expected_subjects = [
            "Second Conversation",   # agent-2 → agent-1, completed at base_time + 5 min
            "First Conversation",   # agent-1 → agent-2, completed at base_time + 10 min
            "Third Conversation"    # agent-1 → agent-3, completed at base_time + 20 min
        ]
        assert subjects == expected_subjects

    def test_get_conversation_filters_by_agent_recipient(
        self, builder, state_with_conversation_history
    ):
        """Test that get_conversation filters by agent involvement (either from_agent or to_agent)."""
        conversation = builder.get_conversation(state_with_conversation_history, agent="agent-2")

        # Should have 3 messages involving agent-2 (either as sender or recipient)
        assert len(conversation) == 3

        # All returned messages should involve agent-2 (either as sender or recipient)
        for message in conversation:
            assert message.from_agent == "agent-2" or message.to_agent == "agent-2"

        # Should still be in chronological order
        subjects = [msg.subject for msg in conversation]
        expected_subjects = [
            "Second Conversation",   # agent-2 → agent-1, completed at base_time + 5 min
            "First Conversation",    # agent-1 → agent-2, completed at base_time + 10 min
            "Fourth Conversation"    # agent-3 → agent-2, completed at base_time + 15 min
        ]
        assert subjects == expected_subjects

    def test_get_conversation_filters_by_agent_either_direction(
        self, builder, state_with_conversation_history
    ):
        """Test that get_conversation filters messages where agent appears in either from_agent or to_agent."""
        # The method should match messages where the specified agent is EITHER sender OR recipient
        conversation = builder.get_conversation(state_with_conversation_history, agent="agent-2")

        # Should have 3 messages involving agent-2 (as sender or recipient)
        assert len(conversation) == 3

        # All returned messages should involve agent-2
        for message in conversation:
            assert message.from_agent == "agent-2" or message.to_agent == "agent-2"

        # Should be in chronological order
        subjects = [msg.subject for msg in conversation]
        expected_subjects = [
            "Second Conversation",   # agent-2 → agent-1, completed at base_time + 5 min
            "First Conversation",    # agent-1 → agent-2, completed at base_time + 10 min
            "Fourth Conversation"    # agent-3 → agent-2, completed at base_time + 15 min
        ]
        assert subjects == expected_subjects

    def test_get_conversation_empty_history_returns_empty_list(self, builder):
        """Test that get_conversation returns empty list for empty conversation history."""
        empty_state = {
            'inbox': [],
            'outbox': [],
            'conversation_history': []
        }

        conversation = builder.get_conversation(empty_state)
        assert conversation == []

        # Also test with agent filter
        conversation_filtered = builder.get_conversation(empty_state, agent="agent-1")
        assert conversation_filtered == []

    def test_get_conversation_no_matching_agent_returns_empty_list(
        self, builder, state_with_conversation_history
    ):
        """Test that get_conversation returns empty list when no messages match the agent filter."""
        conversation = builder.get_conversation(state_with_conversation_history, agent="agent-99")
        assert conversation == []

    def test_get_conversation_handles_missing_state_keys_gracefully(self, builder):
        """Test that get_conversation handles malformed state gracefully."""
        # Test with missing conversation_history key
        malformed_state = {
            'inbox': [],
            'outbox': []
        }

        conversation = builder.get_conversation(malformed_state)
        assert conversation == []

        # Also test with agent filter
        conversation_filtered = builder.get_conversation(malformed_state, agent="agent-1")
        assert conversation_filtered == []

    def test_get_conversation_preserves_original_state(
        self, builder, state_with_conversation_history
    ):
        """Test that get_conversation does not modify the original state."""
        original_history_length = len(state_with_conversation_history['conversation_history'])
        original_first_message = state_with_conversation_history['conversation_history'][0]

        conversation = builder.get_conversation(state_with_conversation_history)

        # Original state should be unchanged
        assert len(state_with_conversation_history['conversation_history']) == original_history_length
        assert state_with_conversation_history['conversation_history'][0] is original_first_message

        # Returned list should be independent
        assert conversation is not state_with_conversation_history['conversation_history']

    def test_get_conversation_multiple_same_timestamp_maintains_stable_order(
        self, builder, base_time
    ):
        """Test that messages with same completed_at timestamp maintain stable order."""
        # Create multiple messages at the same completion timestamp
        same_time = base_time + timedelta(minutes=10)

        msg_1 = ConversationMessage(
            event_id="evt-s1",
            message_id="msg-s1",
            from_agent="agent-1",
            to_agent="agent-2",
            subject="Same Time First",
            body="First message at same completion time",
            priority=MessagePriority.NORMAL,
            created_at=base_time,
            sent_at=base_time + timedelta(minutes=1),
            completed_at=same_time,
            success=True,
            correlation_id="corr-s1"
        )

        msg_2 = ConversationMessage(
            event_id="evt-s2",
            message_id="msg-s2",
            from_agent="agent-2",
            to_agent="agent-1",
            subject="Same Time Second",
            body="Second message at same completion time",
            priority=MessagePriority.HIGH,
            created_at=base_time + timedelta(minutes=2),
            sent_at=base_time + timedelta(minutes=3),
            completed_at=same_time,
            success=True,
            correlation_id="corr-s2"
        )

        state = {
            'inbox': [],
            'outbox': [],
            'conversation_history': [msg_2, msg_1]  # Reverse order in state
        }

        conversation = builder.get_conversation(state)

        # Should maintain stable order (original order for same timestamp)
        assert len(conversation) == 2
        assert conversation[0].subject == "Same Time Second"
        assert conversation[1].subject == "Same Time First"

    def test_get_conversation_mixed_success_and_failure_messages(
        self, builder, state_with_conversation_history
    ):
        """Test that get_conversation includes both successful and failed messages."""
        conversation = builder.get_conversation(state_with_conversation_history)

        # Should include both successful and failed messages
        success_values = [msg.success for msg in conversation]
        assert True in success_values  # Has successful messages
        assert False in success_values  # Has failed messages

        # Verify the failed message is included and in correct position
        failed_messages = [msg for msg in conversation if not msg.success]
        assert len(failed_messages) == 1
        assert failed_messages[0].subject == "Third Conversation"