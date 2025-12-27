# ABOUTME: InboxCount data model for tracking unread messages
# ABOUTME: Provides InboxCount Pydantic model with methods to manage unread count

"""InboxCount data model for tracking unread messages.

This module provides the InboxCount Pydantic model used for tracking
the number of unread messages in an agent's mailbox. It includes methods
to increment, decrement, and update the timestamp.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class InboxCount(BaseModel):
    """Model representing the count of unread messages in an inbox.

    This model tracks the number of unread messages and when the inbox
    was last checked. It provides methods to increment/decrement the
    unread count and update the timestamp.

    Attributes:
        unread: Number of unread messages (must be non-negative)
        last_checked: Timestamp when the inbox was last checked
    """

    model_config = {"extra": "ignore"}  # Ignore extra fields

    unread: int = Field(
        default=0,
        description="Number of unread messages",
        ge=0  # Greater than or equal to 0
    )
    last_checked: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the inbox was last checked"
    )

    @field_validator('unread')
    @classmethod
    def validate_unread_non_negative(cls, v: int) -> int:
        """Validate that unread count is non-negative.

        Args:
            v: The unread count value to validate

        Returns:
            The validated unread count

        Raises:
            ValueError: If the unread count is negative
        """
        if v < 0:
            raise ValueError("unread count cannot be negative")
        return v

    def increment(self) -> 'InboxCount':
        """Increment the unread count by 1 and update the timestamp.

        Returns:
            Self for method chaining
        """
        self.unread += 1
        self.last_checked = datetime.now()
        return self

    def decrement(self) -> 'InboxCount':
        """Decrement the unread count by 1 (minimum 0) and update the timestamp.

        The unread count will not go below 0. If already at 0, it stays at 0.

        Returns:
            Self for method chaining
        """
        if self.unread > 0:
            self.unread -= 1
        self.last_checked = datetime.now()
        return self

    def update_timestamp(self) -> 'InboxCount':
        """Update the last_checked timestamp to the current time.

        Returns:
            Self for method chaining
        """
        self.last_checked = datetime.now()
        return self
