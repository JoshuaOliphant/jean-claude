# ABOUTME: Message data model for agent mailbox communication
# ABOUTME: Provides Message Pydantic model with fields for inter-agent messaging

"""Message data model for agent mailbox communication.

This module provides the Message Pydantic model used for communication
between agents via the mailbox system. Messages can have different priorities
and can indicate if they're awaiting a response.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class MessagePriority(str, Enum):
    """Enum representing the priority levels for messages.

    Attributes:
        URGENT: High-priority message requiring immediate attention
        NORMAL: Standard priority message (default)
        LOW: Low-priority message that can be handled when convenient
    """

    URGENT = 'urgent'
    NORMAL = 'normal'
    LOW = 'low'


class Message(BaseModel):
    """Model representing a message in the agent mailbox system.

    Messages are used for inter-agent communication, allowing agents to
    send requests, notifications, and responses to each other through
    the mailbox system.

    Attributes:
        id: Unique identifier for the message (auto-generated if not provided)
        from_agent: Identifier of the agent sending the message
        to_agent: Identifier of the agent receiving the message
        type: Type/category of the message (e.g., 'help_request', 'notification')
        subject: Brief subject line of the message
        body: Full content of the message
        priority: Priority level of the message (urgent/normal/low)
        created_at: Timestamp when the message was created
        awaiting_response: Whether this message requires a response
    """

    model_config = {"extra": "ignore"}  # Ignore extra fields

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique message identifier"
    )
    from_agent: str = Field(..., description="Agent sending the message")
    to_agent: str = Field(..., description="Agent receiving the message")
    type: str = Field(..., description="Type/category of the message")
    subject: str = Field(..., description="Subject line of the message")
    body: str = Field(..., description="Full message content")
    priority: MessagePriority = Field(
        default=MessagePriority.NORMAL,
        description="Priority level of the message"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the message was created"
    )
    awaiting_response: bool = Field(
        default=False,
        description="Whether this message requires a response"
    )

    @field_validator('from_agent', 'to_agent', 'type', 'subject', 'body')
    @classmethod
    def validate_required_strings(cls, v: str, info) -> str:
        """Validate that required string fields are not empty.

        Args:
            v: The field value to validate
            info: Validation info containing field name

        Returns:
            The validated field value

        Raises:
            ValueError: If the field is empty or only whitespace
        """
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v
