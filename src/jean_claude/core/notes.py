# ABOUTME: Note data model for agent note-taking system
# ABOUTME: Provides Note Pydantic model for shared notes between agents

"""Note data model for agent note-taking system.

This module provides the Note Pydantic model used by agents to record
observations, decisions, learnings, and other information that should
be shared across agents working on the same workflow.
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class NoteCategory(str, Enum):
    """Enum representing the category of a note.

    Attributes:
        OBSERVATION: Something the agent observed during work
        QUESTION: A question needing clarification or input
        IDEA: A potential improvement or alternative approach
        DECISION: A decision made by the agent
        LEARNING: Something learned while debugging or exploring
        REFLECTION: Analysis of process or performance
        WARNING: A warning or caution for other agents
        ACCOMPLISHMENT: A completed task or milestone
        CONTEXT: Background context or information
        TODO: A task or item to be addressed later
    """

    OBSERVATION = "observation"
    QUESTION = "question"
    IDEA = "idea"
    DECISION = "decision"
    LEARNING = "learning"
    REFLECTION = "reflection"
    WARNING = "warning"
    ACCOMPLISHMENT = "accomplishment"
    CONTEXT = "context"
    TODO = "todo"


class Note(BaseModel):
    """Model representing a note in the agent note-taking system.

    Notes are used by agents to record information that should be shared
    with other agents working on the same workflow. This enables knowledge
    transfer and collaboration between agents.

    Attributes:
        id: Unique identifier for the note (auto-generated if not provided)
        agent_id: Identifier of the agent creating the note
        category: Category of the note (observation, decision, learning, etc.)
        title: Brief title summarizing the note
        content: Full content of the note
        tags: Optional list of tags for categorization and searching
        created_at: Timestamp when the note was created
        related_file: Optional file path related to this note
        related_feature: Optional feature name this note relates to
    """

    model_config = {"extra": "ignore"}  # Ignore extra fields

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique note identifier"
    )
    agent_id: str = Field(..., description="Agent creating the note")
    category: NoteCategory = Field(
        default=NoteCategory.OBSERVATION,
        description="Category of the note"
    )
    title: str = Field(..., description="Brief title for the note")
    content: str = Field(..., description="Full note content")
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the note was created"
    )
    related_file: str | None = Field(
        default=None,
        description="Optional file path related to this note"
    )
    related_feature: str | None = Field(
        default=None,
        description="Optional feature name this note relates to"
    )

    @field_validator("agent_id", "title", "content")
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

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate and clean tags.

        Args:
            v: The list of tags to validate

        Returns:
            Cleaned list of tags with whitespace stripped
        """
        return [tag.strip() for tag in v if tag and tag.strip()]

    def format_for_display(self) -> str:
        """Format the note for human-readable display.

        Returns:
            A formatted string representation of the note
        """
        lines = [
            f"[{self.category.value.upper()}] {self.title}",
            f"Agent: {self.agent_id}",
            f"Time: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if self.tags:
            lines.append(f"Tags: {', '.join(self.tags)}")

        if self.related_file:
            lines.append(f"File: {self.related_file}")

        if self.related_feature:
            lines.append(f"Feature: {self.related_feature}")

        lines.append("")
        lines.append(self.content)

        return "\n".join(lines)
