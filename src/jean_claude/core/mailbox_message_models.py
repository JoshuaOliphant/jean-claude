# ABOUTME: Mailbox message data classes for projection state
# ABOUTME: Provides InboxMessage, OutboxMessage, and ConversationMessage models

"""Mailbox message data classes for projection state.

This module defines specialized message data classes used by the MailboxProjectionBuilder
to maintain inbox, outbox, and conversation history state. These classes extend the
basic Message model with additional fields and methods needed for mailbox functionality.

Key Classes:
- InboxMessage: Messages received by an agent, with acknowledgment tracking
- OutboxMessage: Messages sent by an agent, with completion tracking
- ConversationMessage: Completed messages moved to conversation history

These classes support the full message lifecycle:
1. Message sent → OutboxMessage created
2. Message received → InboxMessage created
3. Message acknowledged → InboxMessage.acknowledged = True
4. Message completed → OutboxMessage.completed = True
5. Completed message → ConversationMessage created for history
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from .message import Message, MessagePriority


class InboxMessage(BaseModel):
    """Model for messages in an agent's inbox.

    Represents incoming messages that an agent has received. Tracks acknowledgment
    status and timing for managing unread messages and response workflows.

    Attributes:
        event_id: ID of the event that created this inbox entry
        message_id: ID of the underlying message
        from_agent: Agent that sent the message
        to_agent: Agent that received the message
        subject: Message subject line
        body: Message content
        priority: Message priority level
        created_at: When the original message was created
        received_at: When this agent received the message
        acknowledged: Whether the message has been acknowledged
        acknowledged_at: When the message was acknowledged (if applicable)
    """

    model_config = {"extra": "ignore"}

    # Event tracking
    event_id: str = Field(..., description="Event ID that created this inbox entry")

    # Message details
    message_id: str = Field(..., description="Original message ID")
    from_agent: str = Field(..., description="Agent that sent the message")
    to_agent: str = Field(..., description="Agent that received the message")
    subject: str = Field(..., description="Message subject")
    body: str = Field(..., description="Message content")
    priority: MessagePriority = Field(
        default=MessagePriority.NORMAL,
        description="Message priority level"
    )

    # Timing
    created_at: datetime = Field(..., description="When message was originally created")
    received_at: datetime = Field(..., description="When message was received")

    # Status tracking
    acknowledged: bool = Field(
        default=False,
        description="Whether message has been acknowledged"
    )
    acknowledged_at: Optional[datetime] = Field(
        default=None,
        description="When message was acknowledged"
    )

    # Thread tracking
    correlation_id: Optional[str] = Field(
        default=None,
        description="Optional correlation ID to track related messages in a thread"
    )

    @field_validator('event_id', 'message_id', 'from_agent', 'to_agent', 'subject', 'body')
    @classmethod
    def validate_required_strings(cls, v: str, info) -> str:
        """Validate that required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v

    @classmethod
    def from_message(
        cls,
        message: Message,
        event_id: str,
        received_at: datetime
    ) -> 'InboxMessage':
        """Create InboxMessage from a base Message.

        Args:
            message: Base Message to convert
            event_id: Event ID that triggered this inbox entry
            received_at: When the message was received

        Returns:
            InboxMessage instance with message data and inbox-specific fields
        """
        return cls(
            event_id=event_id,
            message_id=message.id,
            from_agent=message.from_agent,
            to_agent=message.to_agent,
            subject=message.subject,
            body=message.body,
            priority=message.priority,
            created_at=message.created_at,
            received_at=received_at,
            correlation_id=message.correlation_id
        )

    def acknowledge(self, acknowledged_at: datetime) -> None:
        """Mark this message as acknowledged.

        Args:
            acknowledged_at: Timestamp when message was acknowledged
        """
        self.acknowledged = True
        self.acknowledged_at = acknowledged_at


class OutboxMessage(BaseModel):
    """Model for messages in an agent's outbox.

    Represents outgoing messages that an agent has sent. Tracks completion
    status and success/failure for managing pending messages and response workflows.

    Attributes:
        event_id: ID of the event that created this outbox entry
        message_id: ID of the underlying message
        from_agent: Agent that sent the message
        to_agent: Agent that will receive the message
        subject: Message subject line
        body: Message content
        priority: Message priority level
        created_at: When the original message was created
        sent_at: When the message was sent
        completed: Whether the message processing is complete
        completed_at: When the message was completed (if applicable)
        success: Whether the message was successfully processed (if completed)
    """

    model_config = {"extra": "ignore"}

    # Event tracking
    event_id: str = Field(..., description="Event ID that created this outbox entry")

    # Message details
    message_id: str = Field(..., description="Original message ID")
    from_agent: str = Field(..., description="Agent that sent the message")
    to_agent: str = Field(..., description="Agent that will receive the message")
    subject: str = Field(..., description="Message subject")
    body: str = Field(..., description="Message content")
    priority: MessagePriority = Field(
        default=MessagePriority.NORMAL,
        description="Message priority level"
    )

    # Timing
    created_at: datetime = Field(..., description="When message was originally created")
    sent_at: datetime = Field(..., description="When message was sent")

    # Status tracking
    completed: bool = Field(
        default=False,
        description="Whether message processing is complete"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When message was completed"
    )
    success: Optional[bool] = Field(
        default=None,
        description="Whether message was successfully processed"
    )

    # Thread tracking
    correlation_id: Optional[str] = Field(
        default=None,
        description="Optional correlation ID to track related messages in a thread"
    )

    @field_validator('event_id', 'message_id', 'from_agent', 'to_agent', 'subject', 'body')
    @classmethod
    def validate_required_strings(cls, v: str, info) -> str:
        """Validate that required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v

    @classmethod
    def from_message(
        cls,
        message: Message,
        event_id: str,
        sent_at: datetime
    ) -> 'OutboxMessage':
        """Create OutboxMessage from a base Message.

        Args:
            message: Base Message to convert
            event_id: Event ID that triggered this outbox entry
            sent_at: When the message was sent

        Returns:
            OutboxMessage instance with message data and outbox-specific fields
        """
        return cls(
            event_id=event_id,
            message_id=message.id,
            from_agent=message.from_agent,
            to_agent=message.to_agent,
            subject=message.subject,
            body=message.body,
            priority=message.priority,
            created_at=message.created_at,
            sent_at=sent_at,
            correlation_id=message.correlation_id
        )

    def complete(self, success: bool, completed_at: datetime) -> None:
        """Mark this message as completed.

        Args:
            success: Whether the message was successfully processed
            completed_at: Timestamp when message was completed
        """
        self.completed = True
        self.success = success
        self.completed_at = completed_at


class ConversationMessage(BaseModel):
    """Model for messages in conversation history.

    Represents completed messages that have been moved to conversation history.
    Contains the full message lifecycle from creation through completion, along
    with correlation tracking for linking related messages.

    Attributes:
        event_id: ID of the original event that created the message
        message_id: ID of the underlying message
        from_agent: Agent that sent the message
        to_agent: Agent that received the message
        subject: Message subject line
        body: Message content
        priority: Message priority level
        created_at: When the original message was created
        sent_at: When the message was sent
        completed_at: When the message was completed
        success: Whether the message was successfully processed
        correlation_id: ID for correlating related messages in conversation
    """

    model_config = {"extra": "ignore"}

    # Event tracking
    event_id: str = Field(..., description="Original event ID")

    # Message details
    message_id: str = Field(..., description="Original message ID")
    from_agent: str = Field(..., description="Agent that sent the message")
    to_agent: str = Field(..., description="Agent that received the message")
    subject: str = Field(..., description="Message subject")
    body: str = Field(..., description="Message content")
    priority: MessagePriority = Field(
        default=MessagePriority.NORMAL,
        description="Message priority level"
    )

    # Full timing lifecycle
    created_at: datetime = Field(..., description="When message was originally created")
    sent_at: datetime = Field(..., description="When message was sent")
    completed_at: datetime = Field(..., description="When message was completed")

    # Final status
    success: bool = Field(..., description="Whether message was successfully processed")

    # Conversation tracking
    correlation_id: str = Field(
        ...,
        description="Correlation ID for linking related messages"
    )

    @field_validator('event_id', 'message_id', 'from_agent', 'to_agent', 'subject', 'body', 'correlation_id')
    @classmethod
    def validate_required_strings(cls, v: str, info) -> str:
        """Validate that required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v

    @classmethod
    def from_outbox_message(
        cls,
        outbox_message: OutboxMessage,
        correlation_id: str = None
    ) -> 'ConversationMessage':
        """Create ConversationMessage from a completed OutboxMessage.

        Args:
            outbox_message: Completed OutboxMessage to convert
            correlation_id: Optional correlation ID override for conversation tracking.
                          If not provided, uses outbox_message's correlation_id.

        Returns:
            ConversationMessage instance with complete message lifecycle

        Raises:
            ValueError: If outbox_message is not completed
        """
        if not outbox_message.completed:
            raise ValueError("Cannot create ConversationMessage from incomplete OutboxMessage")

        if outbox_message.success is None:
            raise ValueError("OutboxMessage must have success status set")

        # Use provided correlation_id or fall back to outbox_message's correlation_id
        final_correlation_id = correlation_id or outbox_message.correlation_id
        if not final_correlation_id:
            raise ValueError("Correlation ID is required for ConversationMessage")

        return cls(
            event_id=outbox_message.event_id,
            message_id=outbox_message.message_id,
            from_agent=outbox_message.from_agent,
            to_agent=outbox_message.to_agent,
            subject=outbox_message.subject,
            body=outbox_message.body,
            priority=outbox_message.priority,
            created_at=outbox_message.created_at,
            sent_at=outbox_message.sent_at,
            completed_at=outbox_message.completed_at,
            success=outbox_message.success,
            correlation_id=final_correlation_id
        )