# ABOUTME: WorkflowEvent Pydantic model for workflow event tracking
# ABOUTME: Provides immutable WorkflowEvent dataclass with UUID, timestamp, and validation

"""WorkflowEvent Pydantic model for workflow event tracking.

This module provides the WorkflowEvent Pydantic model with frozen=True for immutability,
designed for tracking workflow events with automatic UUID generation and timestamp handling.

The model includes:
- event_id: UUID field with auto-generation
- workflow_id: Required string identifier for the workflow
- event_type: Required string describing the type of event
- timestamp: datetime field with auto-generation
- data: dict field for event-specific payload data

All string fields are validated to ensure they are not empty or whitespace-only.
The model is frozen to ensure immutability after creation.
"""

from datetime import datetime
from typing import Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class WorkflowEvent(BaseModel):
    """Immutable Pydantic model representing a workflow event.

    This model tracks individual workflow events with automatic UUID and timestamp
    generation. The model is frozen to ensure immutability after creation.

    Attributes:
        event_id: Unique identifier for this event (auto-generated UUID)
        workflow_id: Identifier of the workflow this event belongs to
        event_type: Type/category of the event (e.g., 'workflow.started')
        timestamp: When the event occurred (auto-generated datetime)
        data: Event-specific payload data (dict)

    Example:
        >>> event = WorkflowEvent(
        ...     workflow_id="my-workflow-123",
        ...     event_type="workflow.started",
        ...     data={"message": "Starting workflow"}
        ... )
        >>> print(event.event_id)  # Auto-generated UUID
        >>> print(event.timestamp)  # Auto-generated timestamp
    """

    model_config = {
        "frozen": True,  # Make the model immutable
        "extra": "ignore"  # Ignore extra fields
    }

    event_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this event"
    )
    workflow_id: str = Field(
        ...,
        description="Identifier of the workflow this event belongs to"
    )
    event_type: str = Field(
        ...,
        description="Type/category of the event"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the event occurred"
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Event-specific payload data"
    )

    @field_validator('workflow_id', 'event_type')
    @classmethod
    def validate_required_strings(cls, v: str, info) -> str:
        """Validate that required string fields are not empty or whitespace-only.

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