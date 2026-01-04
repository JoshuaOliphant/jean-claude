# ABOUTME: Pydantic schemas for agent messaging event data structures
# ABOUTME: Provides structured schemas for agent.message.sent event payload validation

"""Pydantic schemas for agent messaging event data structures.

This module provides Pydantic schemas for validating the data payloads
of agent messaging events. These schemas ensure that event data has the
correct structure and types when events are created and stored.

The schemas defined here correspond to the agent messaging event types:
- AgentMessageSentData: Schema for agent.message.sent event data
- AgentMessageAcknowledgedData: Schema for agent.message.acknowledged event data
- AgentMessageCompletedData: Schema for agent.message.completed event data

These schemas are used with the Event model from events.py to create
strongly-typed event instances with validated data payloads.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class MessageType(str, Enum):
    """Enum representing the types of messages that can be sent between agents.

    Attributes:
        HELP_REQUEST: Request for assistance from another agent
        NOTIFICATION: Information-only message (no response expected)
        TASK_ASSIGNMENT: Assignment of a task to another agent
        STATUS_UPDATE: Update on the progress of a task or operation
        RESPONSE: Response to a previous message or request
    """

    HELP_REQUEST = 'help_request'
    NOTIFICATION = 'notification'
    TASK_ASSIGNMENT = 'task_assignment'
    STATUS_UPDATE = 'status_update'
    RESPONSE = 'response'


class MessagePriority(str, Enum):
    """Enum representing the priority levels for agent messages.

    Attributes:
        URGENT: High-priority message requiring immediate attention
        NORMAL: Standard priority message (default)
        LOW: Low-priority message that can be handled when convenient
    """

    URGENT = 'urgent'
    NORMAL = 'normal'
    LOW = 'low'


class AgentMessageSentData(BaseModel):
    """Pydantic schema for agent.message.sent event data.

    This schema validates the data payload for agent.message.sent events,
    which are emitted when an agent sends a message to another agent through
    the messaging system.

    Attributes:
        from_agent: Identifier of the agent sending the message
        to_agent: Identifier of the agent receiving the message
        content: The actual content/body of the message
        priority: Priority level of the message (urgent/normal/low)
        correlation_id: Unique identifier for tracking this message and responses
        awaiting_response: Whether this message requires a response from the recipient
        message_type: Type/category of the message (help_request, notification, etc.)
    """

    model_config = {"extra": "forbid"}  # Strict validation - no extra fields allowed

    from_agent: str = Field(
        ...,
        description="Identifier of the agent sending the message"
    )
    to_agent: str = Field(
        ...,
        description="Identifier of the agent receiving the message"
    )
    content: str = Field(
        ...,
        description="The actual content/body of the message"
    )
    priority: MessagePriority = Field(
        default=MessagePriority.NORMAL,
        description="Priority level of the message"
    )
    correlation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for tracking this message and responses"
    )
    awaiting_response: bool = Field(
        default=False,
        description="Whether this message requires a response from the recipient"
    )
    message_type: MessageType = Field(
        ...,
        description="Type/category of the message"
    )

    @field_validator('from_agent', 'to_agent', 'content')
    @classmethod
    def validate_required_strings(cls, v: str, info) -> str:
        """Validate that required string fields are not empty or just whitespace.

        Args:
            v: The field value to validate
            info: Validation info containing field name

        Returns:
            The validated field value with stripped whitespace

        Raises:
            ValueError: If the field is empty or only whitespace
        """
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty or whitespace-only")
        return v.strip()

    @field_validator('from_agent', 'to_agent')
    @classmethod
    def validate_agent_identifiers(cls, v: str, info) -> str:
        """Validate that agent identifiers follow expected format.

        Agent identifiers should not contain certain characters that could
        cause issues in file paths or URLs.

        Args:
            v: The agent identifier to validate
            info: Validation info containing field name

        Returns:
            The validated agent identifier

        Raises:
            ValueError: If the identifier contains invalid characters
        """
        invalid_chars = set('\\/:*?"<>|')
        if any(char in v for char in invalid_chars):
            invalid_found = [char for char in invalid_chars if char in v]
            raise ValueError(
                f"{info.field_name} cannot contain characters: {', '.join(invalid_found)}"
            )
        return v

    @field_validator('correlation_id')
    @classmethod
    def validate_correlation_id(cls, v: str) -> str:
        """Validate correlation ID format and uniqueness requirements.

        Args:
            v: The correlation ID to validate

        Returns:
            The validated correlation ID

        Raises:
            ValueError: If the correlation ID is invalid
        """
        if not v or not v.strip():
            raise ValueError("correlation_id cannot be empty")

        # Basic length check to ensure it's reasonable
        if len(v.strip()) < 3:
            raise ValueError("correlation_id must be at least 3 characters")

        return v.strip()


class AgentMessageAcknowledgedData(BaseModel):
    """Pydantic schema for agent.message.acknowledged event data.

    This schema validates the data payload for agent.message.acknowledged events,
    which are emitted when an agent acknowledges receipt of a message.

    Attributes:
        correlation_id: ID of the original message being acknowledged
        from_agent: Identifier of the agent who sent the acknowledgment
        acknowledged_at: Timestamp when the message was acknowledged
    """

    model_config = {"extra": "forbid"}

    correlation_id: str = Field(
        ...,
        description="ID of the original message being acknowledged",
        min_length=1
    )
    from_agent: str = Field(
        ...,
        description="Identifier of the agent who sent the acknowledgment",
        min_length=1
    )
    acknowledged_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the message was acknowledged"
    )

    @field_validator('correlation_id', 'from_agent')
    @classmethod
    def validate_required_strings(cls, v: str, info) -> str:
        """Validate that required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty or whitespace-only")
        return v.strip()


class AgentMessageCompletedData(BaseModel):
    """Pydantic schema for agent.message.completed event data.

    This schema validates the data payload for agent.message.completed events,
    which are emitted when an agent completes processing a message request.

    Attributes:
        correlation_id: ID of the original message being completed
        from_agent: Identifier of the agent who completed the message
        result: The result or outcome of processing the message
        success: Whether the message was processed successfully
    """

    model_config = {"extra": "forbid"}

    correlation_id: str = Field(
        ...,
        description="ID of the original message being completed",
        min_length=1
    )
    from_agent: str = Field(
        ...,
        description="Identifier of the agent who completed the message",
        min_length=1
    )
    result: str = Field(
        ...,
        description="The result or outcome of processing the message",
        min_length=1
    )
    success: bool = Field(
        ...,
        description="Whether the message was processed successfully"
    )

    @field_validator('correlation_id', 'from_agent', 'result')
    @classmethod
    def validate_required_strings(cls, v: str, info) -> str:
        """Validate that required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty or whitespace-only")
        return v.strip()