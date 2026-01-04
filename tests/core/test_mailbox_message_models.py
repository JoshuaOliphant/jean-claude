# ABOUTME: Tests for mailbox message data class models
# ABOUTME: Tests InboxMessage, OutboxMessage, and ConversationMessage data classes

"""Tests for mailbox message data classes.

This module tests the specialized message data classes used by the
MailboxProjectionBuilder for maintaining inbox, outbox, and conversation
history state.

Key Test Categories:
- InboxMessage model creation and validation
- OutboxMessage model creation and validation
- ConversationMessage model creation and validation
- Field validation and defaults
- Serialization and deserialization
- Integration with existing Message model
"""

import pytest
from datetime import datetime
from uuid import uuid4

from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.mailbox_message_models import (
    InboxMessage,
    OutboxMessage,
    ConversationMessage
)


class TestInboxMessageModel:
    """Test InboxMessage data class."""

    def test_inbox_message_creation_from_message(self, sample_message):
        """Test creating InboxMessage from base Message."""
        inbox_msg = InboxMessage.from_message(
            message=sample_message,
            event_id="evt-123",
            received_at=datetime.now()
        )

        # Check required fields
        assert inbox_msg.event_id == "evt-123"
        assert inbox_msg.message_id == sample_message.id
        assert inbox_msg.from_agent == sample_message.from_agent
        assert inbox_msg.to_agent == sample_message.to_agent
        assert inbox_msg.subject == sample_message.subject
        assert inbox_msg.body == sample_message.body
        assert inbox_msg.priority == sample_message.priority
        assert inbox_msg.created_at == sample_message.created_at
        assert isinstance(inbox_msg.received_at, datetime)
        assert inbox_msg.acknowledged is False  # default
        assert inbox_msg.acknowledged_at is None  # default

    def test_inbox_message_direct_creation(self):
        """Test creating InboxMessage with all fields."""
        now = datetime.now()
        ack_time = datetime.now()

        inbox_msg = InboxMessage(
            event_id="evt-456",
            message_id="msg-789",
            from_agent="sender",
            to_agent="receiver",
            subject="Test Subject",
            body="Test body content",
            priority=MessagePriority.URGENT,
            created_at=now,
            received_at=now,
            acknowledged=True,
            acknowledged_at=ack_time
        )

        assert inbox_msg.event_id == "evt-456"
        assert inbox_msg.message_id == "msg-789"
        assert inbox_msg.from_agent == "sender"
        assert inbox_msg.to_agent == "receiver"
        assert inbox_msg.subject == "Test Subject"
        assert inbox_msg.body == "Test body content"
        assert inbox_msg.priority == MessagePriority.URGENT
        assert inbox_msg.created_at == now
        assert inbox_msg.received_at == now
        assert inbox_msg.acknowledged is True
        assert inbox_msg.acknowledged_at == ack_time

    def test_inbox_message_acknowledge_method(self, sample_message):
        """Test acknowledging an inbox message."""
        inbox_msg = InboxMessage.from_message(
            message=sample_message,
            event_id="evt-123",
            received_at=datetime.now()
        )

        # Initially not acknowledged
        assert inbox_msg.acknowledged is False
        assert inbox_msg.acknowledged_at is None

        # Acknowledge the message
        acknowledge_time = datetime.now()
        inbox_msg.acknowledge(acknowledge_time)

        assert inbox_msg.acknowledged is True
        assert inbox_msg.acknowledged_at == acknowledge_time

    def test_inbox_message_validation_required_fields(self):
        """Test validation of required fields."""
        with pytest.raises(ValueError, match="event_id cannot be empty"):
            InboxMessage(
                event_id="",
                message_id="msg-123",
                from_agent="sender",
                to_agent="receiver",
                subject="Test",
                body="Test body",
                priority=MessagePriority.NORMAL,
                created_at=datetime.now(),
                received_at=datetime.now()
            )


class TestOutboxMessageModel:
    """Test OutboxMessage data class."""

    def test_outbox_message_creation_from_message(self, sample_message):
        """Test creating OutboxMessage from base Message."""
        outbox_msg = OutboxMessage.from_message(
            message=sample_message,
            event_id="evt-123",
            sent_at=datetime.now()
        )

        # Check required fields
        assert outbox_msg.event_id == "evt-123"
        assert outbox_msg.message_id == sample_message.id
        assert outbox_msg.from_agent == sample_message.from_agent
        assert outbox_msg.to_agent == sample_message.to_agent
        assert outbox_msg.subject == sample_message.subject
        assert outbox_msg.body == sample_message.body
        assert outbox_msg.priority == sample_message.priority
        assert outbox_msg.created_at == sample_message.created_at
        assert isinstance(outbox_msg.sent_at, datetime)
        assert outbox_msg.completed is False  # default
        assert outbox_msg.completed_at is None  # default
        assert outbox_msg.success is None  # default

    def test_outbox_message_direct_creation(self):
        """Test creating OutboxMessage with all fields."""
        now = datetime.now()
        complete_time = datetime.now()

        outbox_msg = OutboxMessage(
            event_id="evt-456",
            message_id="msg-789",
            from_agent="sender",
            to_agent="receiver",
            subject="Test Subject",
            body="Test body content",
            priority=MessagePriority.LOW,
            created_at=now,
            sent_at=now,
            completed=True,
            completed_at=complete_time,
            success=True
        )

        assert outbox_msg.event_id == "evt-456"
        assert outbox_msg.message_id == "msg-789"
        assert outbox_msg.from_agent == "sender"
        assert outbox_msg.to_agent == "receiver"
        assert outbox_msg.subject == "Test Subject"
        assert outbox_msg.body == "Test body content"
        assert outbox_msg.priority == MessagePriority.LOW
        assert outbox_msg.created_at == now
        assert outbox_msg.sent_at == now
        assert outbox_msg.completed is True
        assert outbox_msg.completed_at == complete_time
        assert outbox_msg.success is True

    def test_outbox_message_complete_method(self, sample_message):
        """Test completing an outbox message."""
        outbox_msg = OutboxMessage.from_message(
            message=sample_message,
            event_id="evt-123",
            sent_at=datetime.now()
        )

        # Initially not completed
        assert outbox_msg.completed is False
        assert outbox_msg.completed_at is None
        assert outbox_msg.success is None

        # Complete the message successfully
        complete_time = datetime.now()
        outbox_msg.complete(success=True, completed_at=complete_time)

        assert outbox_msg.completed is True
        assert outbox_msg.completed_at == complete_time
        assert outbox_msg.success is True

    def test_outbox_message_fail_method(self, sample_message):
        """Test failing an outbox message."""
        outbox_msg = OutboxMessage.from_message(
            message=sample_message,
            event_id="evt-123",
            sent_at=datetime.now()
        )

        # Complete the message with failure
        complete_time = datetime.now()
        outbox_msg.complete(success=False, completed_at=complete_time)

        assert outbox_msg.completed is True
        assert outbox_msg.completed_at == complete_time
        assert outbox_msg.success is False


class TestConversationMessageModel:
    """Test ConversationMessage data class."""

    def test_conversation_message_creation_from_outbox(self, sample_message):
        """Test creating ConversationMessage from OutboxMessage."""
        sent_time = datetime.now()
        complete_time = datetime.now()

        outbox_msg = OutboxMessage.from_message(
            message=sample_message,
            event_id="evt-123",
            sent_at=sent_time
        )
        outbox_msg.complete(success=True, completed_at=complete_time)

        conv_msg = ConversationMessage.from_outbox_message(
            outbox_message=outbox_msg,
            correlation_id="corr-456"
        )

        # Check all fields transferred
        assert conv_msg.event_id == "evt-123"
        assert conv_msg.message_id == sample_message.id
        assert conv_msg.from_agent == sample_message.from_agent
        assert conv_msg.to_agent == sample_message.to_agent
        assert conv_msg.subject == sample_message.subject
        assert conv_msg.body == sample_message.body
        assert conv_msg.priority == sample_message.priority
        assert conv_msg.created_at == sample_message.created_at
        assert conv_msg.sent_at == sent_time
        assert conv_msg.completed_at == complete_time
        assert conv_msg.success is True
        assert conv_msg.correlation_id == "corr-456"

    def test_conversation_message_direct_creation(self):
        """Test creating ConversationMessage with all fields."""
        now = datetime.now()
        sent_time = datetime.now()
        complete_time = datetime.now()

        conv_msg = ConversationMessage(
            event_id="evt-789",
            message_id="msg-456",
            from_agent="sender",
            to_agent="receiver",
            subject="Conversation Test",
            body="Conversation body content",
            priority=MessagePriority.URGENT,
            created_at=now,
            sent_at=sent_time,
            completed_at=complete_time,
            success=True,
            correlation_id="corr-123"
        )

        assert conv_msg.event_id == "evt-789"
        assert conv_msg.message_id == "msg-456"
        assert conv_msg.from_agent == "sender"
        assert conv_msg.to_agent == "receiver"
        assert conv_msg.subject == "Conversation Test"
        assert conv_msg.body == "Conversation body content"
        assert conv_msg.priority == MessagePriority.URGENT
        assert conv_msg.created_at == now
        assert conv_msg.sent_at == sent_time
        assert conv_msg.completed_at == complete_time
        assert conv_msg.success is True
        assert conv_msg.correlation_id == "corr-123"

    def test_conversation_message_validation_required_fields(self):
        """Test validation of required fields."""
        with pytest.raises(ValueError, match="correlation_id cannot be empty"):
            ConversationMessage(
                event_id="evt-123",
                message_id="msg-456",
                from_agent="sender",
                to_agent="receiver",
                subject="Test",
                body="Test body",
                priority=MessagePriority.NORMAL,
                created_at=datetime.now(),
                sent_at=datetime.now(),
                completed_at=datetime.now(),
                success=True,
                correlation_id=""
            )


class TestMessageModelsIntegration:
    """Test integration between different message models."""

    def test_message_flow_inbox_to_outbox_to_conversation(self, sample_message):
        """Test complete flow from inbox to outbox to conversation."""
        now = datetime.now()

        # 1. Create inbox message
        inbox_msg = InboxMessage.from_message(
            message=sample_message,
            event_id="evt-inbox",
            received_at=now
        )

        # 2. Acknowledge inbox message
        ack_time = datetime.now()
        inbox_msg.acknowledge(ack_time)
        assert inbox_msg.acknowledged is True

        # 3. Create related outbox message (response)
        response_msg = Message(
            from_agent=sample_message.to_agent,  # swap agents
            to_agent=sample_message.from_agent,
            type="response",
            subject=f"Re: {sample_message.subject}",
            body="Response to your message"
        )

        outbox_msg = OutboxMessage.from_message(
            message=response_msg,
            event_id="evt-outbox",
            sent_at=datetime.now()
        )

        # 4. Complete outbox message
        complete_time = datetime.now()
        outbox_msg.complete(success=True, completed_at=complete_time)

        # 5. Move to conversation history
        conv_msg = ConversationMessage.from_outbox_message(
            outbox_message=outbox_msg,
            correlation_id=inbox_msg.event_id  # Link back to original
        )

        # Verify the flow
        assert conv_msg.correlation_id == inbox_msg.event_id
        assert conv_msg.from_agent == inbox_msg.to_agent
        assert conv_msg.to_agent == inbox_msg.from_agent
        assert conv_msg.success is True

    def test_serialization_and_deserialization(self, sample_message):
        """Test that all message models can be serialized and deserialized."""
        # Test InboxMessage
        inbox_msg = InboxMessage.from_message(
            message=sample_message,
            event_id="evt-123",
            received_at=datetime.now()
        )
        inbox_dict = inbox_msg.model_dump()
        inbox_restored = InboxMessage(**inbox_dict)
        assert inbox_restored.event_id == inbox_msg.event_id
        assert inbox_restored.message_id == inbox_msg.message_id

        # Test OutboxMessage
        outbox_msg = OutboxMessage.from_message(
            message=sample_message,
            event_id="evt-456",
            sent_at=datetime.now()
        )
        outbox_dict = outbox_msg.model_dump()
        outbox_restored = OutboxMessage(**outbox_dict)
        assert outbox_restored.event_id == outbox_msg.event_id
        assert outbox_restored.message_id == outbox_msg.message_id

        # Test ConversationMessage
        outbox_msg.complete(success=True, completed_at=datetime.now())
        conv_msg = ConversationMessage.from_outbox_message(
            outbox_message=outbox_msg,
            correlation_id="corr-789"
        )
        conv_dict = conv_msg.model_dump()
        conv_restored = ConversationMessage(**conv_dict)
        assert conv_restored.event_id == conv_msg.event_id
        assert conv_restored.correlation_id == conv_msg.correlation_id

    def test_message_models_with_different_priorities(self, message_factory):
        """Test message models work with different priority levels."""
        priorities = [MessagePriority.LOW, MessagePriority.NORMAL, MessagePriority.URGENT]

        for priority in priorities:
            msg = message_factory(priority=priority)

            # Test with InboxMessage
            inbox_msg = InboxMessage.from_message(
                message=msg,
                event_id=f"evt-{priority.value}",
                received_at=datetime.now()
            )
            assert inbox_msg.priority == priority

            # Test with OutboxMessage
            outbox_msg = OutboxMessage.from_message(
                message=msg,
                event_id=f"evt-out-{priority.value}",
                sent_at=datetime.now()
            )
            assert outbox_msg.priority == priority