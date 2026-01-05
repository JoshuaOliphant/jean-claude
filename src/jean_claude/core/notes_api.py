# ABOUTME: Notes API class providing high-level note-taking operations
# ABOUTME: Integrates note writer/reader for complete shared notes management

"""Notes API for agent note-taking system.

This module provides the Notes class, which offers a high-level API for
agent note-taking. It integrates note writing/reading into a simple,
cohesive interface for sharing knowledge between agents.
"""

import builtins
from pathlib import Path
from typing import TYPE_CHECKING

from jean_claude.core.note_reader import read_notes, search_notes
from jean_claude.core.note_writer import write_note
from jean_claude.core.notes import Note, NoteCategory
from jean_claude.core.notes_paths import NotesPaths

if TYPE_CHECKING:
    from jean_claude.core.events import EventLogger, EventType


class Notes:
    """High-level API for agent note-taking.

    The Notes class provides a simple, unified interface for all note-taking
    operations including adding notes, reading notes, and searching notes.
    It enables knowledge sharing between agents working on the same workflow.

    Typical usage:
        >>> # Initialize notes for a workflow
        >>> notes = Notes(workflow_id="my-workflow")
        >>>
        >>> # Add a note
        >>> notes.add(
        ...     agent_id="coder-agent",
        ...     title="Found issue with auth",
        ...     content="The auth module has a race condition...",
        ...     category=NoteCategory.LEARNING
        ... )
        >>>
        >>> # Read all notes
        >>> all_notes = notes.list()
        >>>
        >>> # Read notes by category
        >>> learnings = notes.list(category=NoteCategory.LEARNING)
        >>>
        >>> # Search notes
        >>> results = notes.search("authentication")

    Attributes:
        workflow_id: The unique identifier for this workflow
        paths: NotesPaths object containing all file paths
    """

    def __init__(self, workflow_id: str, base_dir: Path | None = None):
        """Initialize the Notes API.

        Args:
            workflow_id: The unique identifier for the workflow
            base_dir: Optional base directory for the notes. If not provided,
                     uses the default location.

        Raises:
            ValueError: If workflow_id is empty or only whitespace
            TypeError: If workflow_id is None
        """
        # NotesPaths will validate the workflow_id
        self._paths = NotesPaths(workflow_id=workflow_id, base_dir=base_dir)

    @property
    def workflow_id(self) -> str:
        """Get the workflow_id for this notes instance."""
        return self._paths.workflow_id

    @property
    def paths(self) -> NotesPaths:
        """Get the NotesPaths object for this notes instance."""
        return self._paths

    def add(
        self,
        agent_id: str,
        title: str,
        content: str,
        category: NoteCategory = NoteCategory.OBSERVATION,
        tags: list[str] | None = None,
        related_file: str | None = None,
        related_feature: str | None = None,
        event_logger: "EventLogger | None" = None,
    ) -> Note:
        """Add a new note.

        This method creates a new Note with the provided information and
        writes it to the shared notes file. If an event_logger is provided,
        it will also emit an event for event sourcing.

        Args:
            agent_id: Identifier of the agent creating the note
            title: Brief title for the note
            content: Full content of the note
            category: Category of the note (default: OBSERVATION)
            tags: Optional list of tags for categorization
            related_file: Optional file path related to this note
            related_feature: Optional feature name this note relates to
            event_logger: Optional EventLogger for event emission

        Returns:
            The created Note object

        Raises:
            ValueError: If required fields are empty
            PermissionError: If the file cannot be written
            OSError: If there are other I/O errors

        Example:
            >>> notes = Notes(workflow_id="my-workflow")
            >>> note = notes.add(
            ...     agent_id="coder-agent",
            ...     title="Discovered API pattern",
            ...     content="The codebase uses repository pattern...",
            ...     category=NoteCategory.LEARNING,
            ...     tags=["architecture", "api"]
            ... )
        """
        note = Note(
            agent_id=agent_id,
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            related_file=related_file,
            related_feature=related_feature,
        )

        write_note(note, self._paths)

        # Emit event if logger provided
        if event_logger:
            from jean_claude.core.events import EventType

            event_type_map = {
                NoteCategory.OBSERVATION: EventType.AGENT_NOTE_OBSERVATION,
                NoteCategory.QUESTION: EventType.AGENT_NOTE_QUESTION,
                NoteCategory.IDEA: EventType.AGENT_NOTE_IDEA,
                NoteCategory.DECISION: EventType.AGENT_NOTE_DECISION,
                NoteCategory.LEARNING: EventType.AGENT_NOTE_LEARNING,
                NoteCategory.REFLECTION: EventType.AGENT_NOTE_REFLECTION,
                NoteCategory.WARNING: EventType.AGENT_NOTE_WARNING,
                NoteCategory.ACCOMPLISHMENT: EventType.AGENT_NOTE_ACCOMPLISHMENT,
                NoteCategory.CONTEXT: EventType.AGENT_NOTE_CONTEXT,
                NoteCategory.TODO: EventType.AGENT_NOTE_TODO,
            }

            event_logger.emit(
                workflow_id=self.workflow_id,
                event_type=event_type_map[category],
                data={
                    "agent_id": agent_id,
                    "title": title,
                    "content": content,
                    "tags": tags or [],
                    "related_file": str(related_file) if related_file else None,
                    "related_feature": related_feature,
                },
            )

        return note

    def add_observation(
        self,
        agent_id: str,
        title: str,
        content: str,
        **kwargs
    ) -> Note:
        """Convenience method to add an observation note."""
        return self.add(
            agent_id=agent_id,
            title=title,
            content=content,
            category=NoteCategory.OBSERVATION,
            **kwargs
        )

    def add_learning(
        self,
        agent_id: str,
        title: str,
        content: str,
        **kwargs
    ) -> Note:
        """Convenience method to add a learning note."""
        return self.add(
            agent_id=agent_id,
            title=title,
            content=content,
            category=NoteCategory.LEARNING,
            **kwargs
        )

    def add_decision(
        self,
        agent_id: str,
        title: str,
        content: str,
        **kwargs
    ) -> Note:
        """Convenience method to add a decision note."""
        return self.add(
            agent_id=agent_id,
            title=title,
            content=content,
            category=NoteCategory.DECISION,
            **kwargs
        )

    def add_warning(
        self,
        agent_id: str,
        title: str,
        content: str,
        **kwargs
    ) -> Note:
        """Convenience method to add a warning note."""
        return self.add(
            agent_id=agent_id,
            title=title,
            content=content,
            category=NoteCategory.WARNING,
            **kwargs
        )

    def add_accomplishment(
        self,
        agent_id: str,
        title: str,
        content: str,
        **kwargs
    ) -> Note:
        """Convenience method to add an accomplishment note."""
        return self.add(
            agent_id=agent_id,
            title=title,
            content=content,
            category=NoteCategory.ACCOMPLISHMENT,
            **kwargs
        )

    def add_todo(
        self,
        agent_id: str,
        title: str,
        content: str,
        **kwargs
    ) -> Note:
        """Convenience method to add a todo note."""
        return self.add(
            agent_id=agent_id,
            title=title,
            content=content,
            category=NoteCategory.TODO,
            **kwargs
        )

    def list(
        self,
        agent_id: str | None = None,
        category: NoteCategory | None = None,
        tag: str | None = None,
        limit: int | None = None,
    ) -> list[Note]:
        """List notes with optional filtering.

        Args:
            agent_id: Optional filter by agent ID
            category: Optional filter by note category
            tag: Optional filter by tag
            limit: Optional maximum number of notes to return

        Returns:
            A list of Note objects matching the filters

        Example:
            >>> notes = Notes(workflow_id="my-workflow")
            >>> all_notes = notes.list()
            >>> learnings = notes.list(category=NoteCategory.LEARNING)
            >>> recent = notes.list(limit=5)
        """
        return read_notes(
            self._paths,
            agent_id=agent_id,
            category=category,
            tag=tag,
            limit=limit,
        )

    def search(
        self,
        query: str,
        search_content: bool = True,
        search_title: bool = True,
    ) -> builtins.list[Note]:
        """Search notes by text query.

        Args:
            query: The text query to search for (case-insensitive)
            search_content: Whether to search in note content
            search_title: Whether to search in note title

        Returns:
            A list of Note objects matching the query

        Example:
            >>> notes = Notes(workflow_id="my-workflow")
            >>> results = notes.search("authentication bug")
        """
        return search_notes(
            self._paths,
            query=query,
            search_content=search_content,
            search_title=search_title,
        )

    def get_summary(self) -> str:
        """Get a summary of all notes.

        Returns a formatted string summarizing all notes organized
        by category.

        Returns:
            A formatted summary string
        """
        all_notes = self.list()

        if not all_notes:
            return "No notes found."

        lines = [f"Notes Summary ({len(all_notes)} total)\n"]

        # Group by category
        by_category: dict[NoteCategory, list[Note]] = {}
        for note in all_notes:
            if note.category not in by_category:
                by_category[note.category] = []
            by_category[note.category].append(note)

        # Output by category
        for category in NoteCategory:
            if category in by_category:
                category_notes = by_category[category]
                lines.append(f"\n## {category.value.upper()} ({len(category_notes)})")
                for note in category_notes:
                    lines.append(f"  - [{note.agent_id}] {note.title}")

        return "\n".join(lines)

    def format_for_context(self, limit: int | None = None) -> str:
        """Format notes for inclusion in agent context.

        This method formats notes in a way that's suitable for including
        in an agent's context/prompt, providing relevant information
        without overwhelming the context.

        Args:
            limit: Maximum number of notes to include

        Returns:
            A formatted string suitable for agent context
        """
        notes = self.list(limit=limit)

        if not notes:
            return "No shared notes available."

        lines = ["## Shared Notes\n"]

        for note in notes:
            lines.append(f"### [{note.category.value}] {note.title}")
            lines.append(f"*Agent: {note.agent_id} | "
                        f"{note.created_at.strftime('%Y-%m-%d %H:%M')}*")
            if note.tags:
                lines.append(f"Tags: {', '.join(note.tags)}")
            lines.append("")
            lines.append(note.content)
            lines.append("")

        return "\n".join(lines)
