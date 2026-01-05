# ABOUTME: Comprehensive integration tests for MailboxProjectionBuilder end-to-end message flow
# ABOUTME: Tests complete message lifecycle through all projection states and transitions

"""Comprehensive integration tests for MailboxProjectionBuilder.

This test module provides end-to-end testing that verifies the complete message flow
through all projection states and transitions. Rather than testing individual methods,
these integration tests ensure that the entire mailbox projection system works together
correctly.

Test Coverage:
- Complete message lifecycle from sent → acknowledged → completed
- Cross-agent message flow validation
- Priority-based message handling
- Correlation ID tracking across message states
- State transitions and consistency
- Edge cases and error scenarios
- Multi-agent conversation flows
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from jean_claude.core.mailbox_projection_builder import MailboxProjectionBuilder
from jean_claude.core.mailbox_message_models import InboxMessage, OutboxMessage, ConversationMessage
from jean_claude.core.message import Message, MessagePriority


class TestMailboxProjectionIntegrationEndToEnd:
    """Test complete end-to-end message lifecycle flows."""

    @pytest.fixture
    def builder(self):
        """Provide a MailboxProjectionBuilder instance."""
        return MailboxProjectionBuilder()

    @pytest.fixture
    def initial_state(self, builder):
        """Provide clean initial state."""
        return builder.get_initial_state()

    @pytest.fixture
    def agent_id(self):
        """Current agent ID for testing."""
        return "agent-1"

    @pytest.fixture
    def other_agent_id(self):
        """Other agent ID for testing."""
        return "agent-2"

    def test_complete_message_lifecycle_sent_to_acknowledged_to_completed(
        self, builder, initial_state, agent_id, other_agent_id, message_factory
    ):
        """Test complete message lifecycle: sent → acknowledged → completed."""
        # Create a message from other_agent to current agent
        message = message_factory(
            from_agent=other_agent_id,
            to_agent=agent_id,
            subject="Important Task",
            body="Please complete this important task.",
            priority=MessagePriority.HIGH,
            correlation_id="corr-123"
        )

        # Step 1: Message sent - should appear in inbox
        sent_event_data = {
            "event_id": "evt-1",
            "message": message,
            "sent_at": datetime.now(),
            "current_agent_id": agent_id,
            "correlation_id": message.correlation_id
        }
        state1 = builder.apply_agent_message_sent(sent_event_data, initial_state)

        # Verify message is in inbox
        assert len(state1['inbox']) == 1
        assert len(state1['outbox']) == 0
        assert len(state1['conversation_history']) == 0

        inbox_msg = state1['inbox'][0]
        assert isinstance(inbox_msg, InboxMessage)
        assert inbox_msg.from_agent == other_agent_id
        assert inbox_msg.to_agent == agent_id
        assert inbox_msg.subject == "Important Task"
        assert inbox_msg.priority == MessagePriority.HIGH
        assert not inbox_msg.acknowledged
        assert inbox_msg.correlation_id == "corr-123"

        # Step 2: Message acknowledged
        ack_event_data = {
            "correlation_id": "evt-1",  # Must match event_id from sent event, not message.correlation_id
            "from_agent": agent_id,
            "acknowledged_at": datetime.now(),
            "current_agent_id": agent_id
        }
        state2 = builder.apply_agent_message_acknowledged(ack_event_data, state1)

        # Verify message marked as acknowledged
        assert len(state2['inbox']) == 1
        assert state2['inbox'][0].acknowledged
        assert state2['inbox'][0].acknowledged_at is not None

        # Step 3: Agent replies (creates outbox message)
        reply_message = message_factory(
            from_agent=agent_id,
            to_agent=other_agent_id,
            subject="Re: Important Task",
            body="Task completed successfully.",
            correlation_id="corr-123"
        )

        reply_event_data = {
            "event_id": "evt-2",
            "message": reply_message,
            "sent_at": datetime.now(),
            "current_agent_id": agent_id,
            "correlation_id": "corr-123"
        }
        state3 = builder.apply_agent_message_sent(reply_event_data, state2)

        # Verify reply is in outbox
        assert len(state3['inbox']) == 1
        assert len(state3['outbox']) == 1
        assert len(state3['conversation_history']) == 0

        outbox_msg = state3['outbox'][0]
        assert isinstance(outbox_msg, OutboxMessage)
        assert outbox_msg.from_agent == agent_id
        assert outbox_msg.to_agent == other_agent_id
        assert outbox_msg.subject == "Re: Important Task"
        assert not outbox_msg.completed

        # Step 4: Reply completed
        completion_event_data = {
            "correlation_id": "evt-2",  # Must match event_id from reply event, not message.correlation_id
            "from_agent": agent_id,
            "result": "success",
            "completed_at": datetime.now(),
            "success": True,
            "current_agent_id": agent_id
        }
        state4 = builder.apply_agent_message_completed(completion_event_data, state3)

        # Verify reply moved to conversation history
        assert len(state4['inbox']) == 1  # Original message still in inbox
        assert len(state4['outbox']) == 0  # Reply moved out of outbox
        assert len(state4['conversation_history']) == 1  # Reply in conversation history

        conv_msg = state4['conversation_history'][0]
        assert isinstance(conv_msg, ConversationMessage)
        assert conv_msg.from_agent == agent_id
        assert conv_msg.to_agent == other_agent_id
        assert conv_msg.subject == "Re: Important Task"
        assert conv_msg.success is True  # ConversationMessage has 'success' field, not 'result'

    def test_multi_agent_conversation_flow_with_priority_handling(
        self, builder, initial_state, message_factory
    ):
        """Test complex multi-agent conversation with priority-based handling."""
        coordinator_id = "coordinator"
        agent1_id = "agent-1"
        agent2_id = "agent-2"

        # High priority urgent message from coordinator to agent-1
        urgent_msg = message_factory(
            from_agent=coordinator_id,
            to_agent=agent1_id,
            type="urgent_request",
            subject="Critical Issue",
            body="System down, need immediate attention",
            priority=MessagePriority.URGENT,
            awaiting_response=True,
            correlation_id="urgent-001"
        )

        # Normal priority message from agent-2 to agent-1
        normal_msg = message_factory(
            from_agent=agent2_id,
            to_agent=agent1_id,
            type="info",
            subject="Daily Update",
            body="Here's today's status update",
            priority=MessagePriority.NORMAL,
            correlation_id="daily-001"
        )

        # Send both messages
        state = initial_state

        urgent_event = {
            "event_id": "evt-urgent",
            "message": urgent_msg,
            "sent_at": datetime.now(),
            "current_agent_id": agent1_id,
            "correlation_id": "urgent-001"
        }
        state = builder.apply_agent_message_sent(urgent_event, state)

        normal_event = {
            "event_id": "evt-normal",
            "message": normal_msg,
            "sent_at": datetime.now(),
            "current_agent_id": agent1_id,
            "correlation_id": "daily-001"
        }
        state = builder.apply_agent_message_sent(normal_event, state)

        # Verify both messages received
        assert len(state['inbox']) == 2

        # Test priority-based retrieval
        unread_messages = builder.get_unread_inbox(state)
        assert len(unread_messages) == 2

        # Higher priority should come first
        assert unread_messages[0].priority == MessagePriority.URGENT
        assert unread_messages[0].subject == "Critical Issue"
        assert unread_messages[1].priority == MessagePriority.NORMAL
        assert unread_messages[1].subject == "Daily Update"

        # Acknowledge urgent message first
        urgent_ack = {
            "correlation_id": "evt-urgent",  # Must match event_id, not message.correlation_id
            "from_agent": agent1_id,
            "acknowledged_at": datetime.now(),
            "current_agent_id": agent1_id
        }
        state = builder.apply_agent_message_acknowledged(urgent_ack, state)

        # Test get_messages_by_priority functionality
        urgent_messages = builder.get_messages_by_priority(state, MessagePriority.URGENT)
        assert len(urgent_messages) == 1
        assert urgent_messages[0].acknowledged

        high_priority_messages = builder.get_high_priority_messages(state)
        assert len(high_priority_messages) == 1  # Only URGENT message

        # Send response to urgent request
        response_msg = message_factory(
            from_agent=agent1_id,
            to_agent=coordinator_id,
            type="response",
            subject="Re: Critical Issue",
            body="Issue resolved, system is back online",
            priority=MessagePriority.URGENT,
            correlation_id="urgent-001"
        )

        response_event = {
            "event_id": "evt-response",
            "message": response_msg,
            "sent_at": datetime.now(),
            "current_agent_id": agent1_id,
            "correlation_id": "urgent-001"
        }
        state = builder.apply_agent_message_sent(response_event, state)

        # Verify response in outbox
        pending_outbox = builder.get_pending_outbox(state)
        assert len(pending_outbox) == 1
        assert pending_outbox[0].subject == "Re: Critical Issue"

        # Complete the response
        completion_event = {
            "correlation_id": "evt-response",  # Must match event_id, not message.correlation_id
            "from_agent": agent1_id,
            "result": "success",
            "completed_at": datetime.now(),
            "success": True,
            "current_agent_id": agent1_id
        }
        state = builder.apply_agent_message_completed(completion_event, state)

        # Verify conversation tracking
        conversation = builder.get_conversation(state)
        assert len(conversation) == 1
        assert conversation[0].subject == "Re: Critical Issue"

        # Test conversation filtering by agent
        coordinator_conversation = builder.get_conversation(state, coordinator_id)
        assert len(coordinator_conversation) == 1

        agent2_conversation = builder.get_conversation(state, agent2_id)
        assert len(agent2_conversation) == 0

    def test_correlation_id_thread_tracking_and_validation(
        self, builder, initial_state, message_factory
    ):
        """Test correlation ID tracking across message threads."""
        agent1_id = "agent-1"
        agent2_id = "agent-2"
        thread_id = "thread-feature-123"

        # Start a feature discussion thread
        initial_msg = message_factory(
            from_agent=agent1_id,
            to_agent=agent2_id,
            subject="Feature Discussion",
            body="Let's discuss the new feature requirements",
            correlation_id=thread_id
        )

        # Send initial message
        state = initial_state
        event1 = {
            "event_id": "evt-1",
            "message": initial_msg,
            "sent_at": datetime.now(),
            "current_agent_id": agent1_id,
            "correlation_id": thread_id
        }
        state = builder.apply_agent_message_sent(event1, state)

        # Verify thread tracking
        thread_messages = builder.get_messages_by_correlation_id(state, thread_id)
        assert len(thread_messages['all']) == 1  # get_messages_by_correlation_id returns dict with 'all' key
        assert thread_messages['outbox'][0].subject == "Feature Discussion"  # Message is in outbox

        # Continue thread with reply (simulate agent-2 responding)
        reply_msg = message_factory(
            from_agent=agent2_id,
            to_agent=agent1_id,
            subject="Re: Feature Discussion",
            body="I have some thoughts on the requirements",
            correlation_id=thread_id
        )

        event2 = {
            "event_id": "evt-2",
            "message": reply_msg,
            "sent_at": datetime.now(),
            "current_agent_id": agent1_id,
            "correlation_id": thread_id
        }
        # Simulate this going to agent-1's inbox
        state = builder.apply_agent_message_sent(event2, state)

        # Test thread consistency validation
        validation = builder.validate_thread_consistency(state)  # Method takes only state, no thread_id
        assert validation['valid']  # Method returns dict with 'valid' key

        # Test thread summary
        thread_summary = builder.get_thread_summary(state, thread_id)
        assert thread_summary['message_count'] >= 2
        assert thread_summary['correlation_id'] == thread_id

        # Complete first message
        completion1 = {
            "correlation_id": "evt-1",  # Must match event_id, not message.correlation_id
            "from_agent": agent1_id,
            "result": "success",
            "completed_at": datetime.now(),
            "success": True,
            "current_agent_id": agent1_id
        }
        state = builder.apply_agent_message_completed(completion1, state)

        # Verify thread still tracked after completion
        thread_messages_after = builder.get_messages_by_correlation_id(state, thread_id)
        assert len(thread_messages_after['all']) >= 1  # get_messages_by_correlation_id returns dict with 'all' key

    def test_state_transitions_and_consistency_validation(
        self, builder, initial_state, message_factory
    ):
        """Test state transitions maintain consistency."""
        agent_id = "test-agent"

        # Start with empty state
        assert builder.get_unread_inbox(initial_state) == []
        assert builder.get_pending_outbox(initial_state) == []
        assert builder.get_conversation(initial_state) == []

        # Add message to inbox
        message = message_factory(
            from_agent="sender",
            to_agent=agent_id,
            subject="Test Message"
        )

        sent_event = {
            "event_id": "evt-1",
            "message": message,
            "sent_at": datetime.now(),
            "current_agent_id": agent_id,
            "correlation_id": "test-corr"
        }
        state1 = builder.apply_agent_message_sent(sent_event, initial_state)

        # Verify state consistency after each transition
        assert len(state1['inbox']) == 1
        assert len(state1['outbox']) == 0
        assert len(state1['conversation_history']) == 0

        # Acknowledge message
        ack_event = {
            "correlation_id": "evt-1",  # Must match event_id, not message.correlation_id
            "from_agent": agent_id,
            "acknowledged_at": datetime.now(),
            "current_agent_id": agent_id
        }
        state2 = builder.apply_agent_message_acknowledged(ack_event, state1)

        # Verify acknowledgment doesn't break state structure
        assert len(state2['inbox']) == 1
        assert state2['inbox'][0].acknowledged
        assert len(state2['outbox']) == 0
        assert len(state2['conversation_history']) == 0

        # Test that original state remains unchanged (immutability)
        assert not state1['inbox'][0].acknowledged
        assert len(initial_state['inbox']) == 0

    def test_cross_agent_message_isolation_and_routing(
        self, builder, initial_state, message_factory
    ):
        """Test messages are properly isolated between agents."""
        agent1_id = "agent-1"
        agent2_id = "agent-2"
        agent3_id = "agent-3"

        # Message from agent-2 to agent-1
        msg1 = message_factory(
            from_agent=agent2_id,
            to_agent=agent1_id,
            subject="Message for Agent 1"
        )

        # Message from agent-3 to agent-2
        msg2 = message_factory(
            from_agent=agent3_id,
            to_agent=agent2_id,
            subject="Message for Agent 2"
        )

        # Message from agent-1 to agent-3
        msg3 = message_factory(
            from_agent=agent1_id,
            to_agent=agent3_id,
            subject="Message for Agent 3"
        )

        # Apply from agent-1 perspective
        state = initial_state

        # Should receive msg1 in inbox (to agent-1)
        event1 = {"event_id": "e1", "message": msg1, "sent_at": datetime.now(), "current_agent_id": agent1_id, "correlation_id": "c1"}
        state = builder.apply_agent_message_sent(event1, state)

        # Should not receive msg2 (not for agent-1)
        event2 = {"event_id": "e2", "message": msg2, "sent_at": datetime.now(), "current_agent_id": agent1_id, "correlation_id": "c2"}
        state = builder.apply_agent_message_sent(event2, state)

        # Should send msg3 to outbox (from agent-1)
        event3 = {"event_id": "e3", "message": msg3, "sent_at": datetime.now(), "current_agent_id": agent1_id, "correlation_id": "c3"}
        state = builder.apply_agent_message_sent(event3, state)

        # Verify proper routing
        assert len(state['inbox']) == 1  # Only msg1
        assert state['inbox'][0].subject == "Message for Agent 1"
        assert state['inbox'][0].from_agent == agent2_id

        assert len(state['outbox']) == 1  # Only msg3
        assert state['outbox'][0].subject == "Message for Agent 3"
        assert state['outbox'][0].to_agent == agent3_id

        # Test acknowledgment isolation (agent-1 can't acknowledge msg2)
        wrong_ack = {
            "correlation_id": "e2",  # Must match event_id even when testing no-op
            "from_agent": agent1_id,
            "acknowledged_at": datetime.now(),
            "current_agent_id": agent1_id
        }
        # This should be a no-op since msg2 isn't in agent-1's inbox
        state_after_wrong_ack = builder.apply_agent_message_acknowledged(wrong_ack, state)
        assert state_after_wrong_ack == state  # No change

    def test_edge_cases_and_error_scenarios(
        self, builder, initial_state, message_factory
    ):
        """Test handling of edge cases and error scenarios."""
        agent_id = "test-agent"

        # Test acknowledging non-existent message
        fake_ack = {
            "correlation_id": "fake",
            "from_agent": agent_id,
            "acknowledged_at": datetime.now(),
            "current_agent_id": agent_id
        }
        state1 = builder.apply_agent_message_acknowledged(fake_ack, initial_state)
        assert state1 == initial_state  # No change

        # Test completing non-existent message
        fake_completion = {
            "correlation_id": "fake",
            "from_agent": agent_id,
            "result": "success",
            "completed_at": datetime.now(),
            "success": True,
            "current_agent_id": agent_id
        }
        state2 = builder.apply_agent_message_completed(fake_completion, initial_state)
        assert state2 == initial_state  # No change

        # Test with missing required fields
        incomplete_event = {
            "event_id": "evt-1",
            # Missing message and correlation_id
        }
        state3 = builder.apply_agent_message_sent(incomplete_event, initial_state)
        # Should handle gracefully, likely no change
        assert len(state3['inbox']) == 0
        assert len(state3['outbox']) == 0

        # Test with malformed state
        malformed_state = {
            'inbox': None,  # Should be list
            'outbox': [],
            'conversation_history': []
        }
        # Helper methods should handle gracefully
        assert builder.get_unread_inbox(malformed_state) == []
        assert builder.get_pending_outbox(malformed_state) == []

    def test_message_filtering_and_retrieval_integration(
        self, builder, message_factory
    ):
        """Test comprehensive message filtering and retrieval."""
        agent_id = "test-agent"

        # Create diverse set of messages
        messages = [
            message_factory(
                from_agent="urgent-sender",
                to_agent=agent_id,
                subject="Critical Alert",
                priority=MessagePriority.URGENT,
                correlation_id="urgent-1"
            ),
            message_factory(
                from_agent="normal-sender",
                to_agent=agent_id,
                subject="Regular Update",
                priority=MessagePriority.NORMAL,
                correlation_id="normal-1"
            ),
            message_factory(
                from_agent="low-sender",
                to_agent=agent_id,
                subject="Info Notice",
                priority=MessagePriority.LOW,
                correlation_id="low-1"
            ),
            message_factory(
                from_agent=agent_id,
                to_agent="recipient",
                subject="My Response",
                priority=MessagePriority.HIGH,
                correlation_id="my-response-1"
            )
        ]

        # Build state with all messages
        state = builder.get_initial_state()
        for i, msg in enumerate(messages):
            event = {
                "event_id": f"evt-{i}",
                "message": msg,
                "sent_at": datetime.now(),
                "current_agent_id": agent_id,
                "correlation_id": msg.correlation_id
            }
            state = builder.apply_agent_message_sent(event, state)

        # Test comprehensive filtering
        assert len(state['inbox']) == 3  # First 3 messages
        assert len(state['outbox']) == 1   # Last message

        # Test priority filtering
        urgent_msgs = builder.get_messages_by_priority(state, MessagePriority.URGENT)
        assert len(urgent_msgs) == 1
        assert urgent_msgs[0].subject == "Critical Alert"

        high_priority_msgs = builder.get_high_priority_messages(state)
        assert len(high_priority_msgs) == 1  # Only URGENT counts as high

        # Test unread filtering (all should be unread initially)
        unread = builder.get_unread_inbox(state)
        assert len(unread) == 3

        # Test priority distribution
        priority_dist = builder.get_priority_distribution(state)
        assert priority_dist['by_priority'][MessagePriority.URGENT] >= 1  # Access 'by_priority' dict
        assert priority_dist['by_priority'][MessagePriority.NORMAL] >= 1
        assert priority_dist['by_priority'][MessagePriority.LOW] >= 1

        # Test urgent message detection
        assert builder.has_urgent_messages(state)

        # Acknowledge some messages and test filtering
        ack_urgent = {
            "correlation_id": "evt-0",  # Must match event_id, not message.correlation_id
            "from_agent": agent_id,
            "acknowledged_at": datetime.now(),
            "current_agent_id": agent_id
        }
        state = builder.apply_agent_message_acknowledged(ack_urgent, state)

        unread_after_ack = builder.get_unread_inbox(state)
        assert len(unread_after_ack) == 2  # One acknowledged

        # Test getting next priority message
        next_priority = builder.get_next_priority_message(state)
        assert next_priority is not None
        assert next_priority.priority in [MessagePriority.NORMAL, MessagePriority.LOW]