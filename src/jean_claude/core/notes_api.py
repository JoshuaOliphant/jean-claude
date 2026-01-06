# ABOUTME: Notes API class providing high-level note-taking operations via SQLite
# ABOUTME: Pure event sourcing - all notes stored as events in .jc/events.db

"""Notes API for agent note-taking system.

This module provides the Notes class, which offers a high-level API for
agent note-taking using pure event sourcing. All notes are stored as events
in the SQLite event store and queried directly from the database.

Architecture:
- Notes are persisted as agent.note.* events in .jc/events.db
- SQLite WAL mode provides durability and crash recovery
- No separate JSONL files - events are the single source of truth
- All queries go directly to SQLite with proper indexing
"""

import builtins
import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from jean_claude.core.notes import Note, NoteCategory

if TYPE_CHECKING:
    from jean_claude.core.events import EventLogger, EventType


class Notes:
    """High-level API for agent note-taking using event sourcing.

    The Notes class provides a simple, unified interface for all note-taking
    operations. All notes are stored as events in SQLite and queried directly
    from the event store, eliminating the need for separate storage layers.

    Typical usage:
        >>> from jean_claude.core.events import EventLogger
        >>>
        >>> # Initialize notes for a workflow
        >>> event_logger = EventLogger(project_root)
        >>> notes = Notes(
        ...     workflow_id="my-workflow",
        ...     project_root=project_root,
        ...     event_logger=event_logger
        ... )
        >>>
        >>> # Add a note (writes to SQLite)
        >>> notes.add(
        ...     agent_id="coder-agent",
        ...     title="Found issue with auth",
        ...     content="The auth module has a race condition...",
        ...     category=NoteCategory.LEARNING
        ... )
        >>>
        >>> # Read all notes (queries SQLite)
        >>> all_notes = notes.list()
        >>>
        >>> # Read notes by category
        >>> learnings = notes.list(category=NoteCategory.LEARNING)
        >>>
        >>> # Search notes
        >>> results = notes.search("authentication")

    Attributes:
        workflow_id: The unique identifier for this workflow
        project_root: Path to the project root directory
        event_logger: EventLogger instance for writing events
    """

    def __init__(
        self,
        workflow_id: str,
        project_root: Path,
        event_logger: "EventLogger"
    ):
        """Initialize the Notes API.

        Args:
            workflow_id: The unique identifier for the workflow
            project_root: Path to the project root directory
            event_logger: EventLogger instance for writing events

        Raises:
            ValueError: If workflow_id is empty or only whitespace
            TypeError: If workflow_id is None or event_logger is None
        """
        if workflow_id is None:
            raise TypeError("workflow_id cannot be None")

        if not workflow_id or not workflow_id.strip():
            raise ValueError("workflow_id cannot be empty")

        if event_logger is None:
            raise TypeError("event_logger cannot be None")

        self._workflow_id = workflow_id
        self._project_root = Path(project_root)
        self._event_logger = event_logger
        self._events_db = self._project_root / ".jc" / "events.db"

    @property
    def workflow_id(self) -> str:
        """Get the workflow_id for this notes instance."""
        return self._workflow_id

    def add(
        self,
        agent_id: str,
        title: str,
        content: str,
        category: NoteCategory = NoteCategory.OBSERVATION,
        tags: list[str] | None = None,
        related_file: str | None = None,
        related_feature: str | None = None,
    ) -> Note:
        """Add a new note via event sourcing.

        This method creates a new Note and emits it as an event to the
        SQLite event store. The note will be available immediately for
        querying via list() and search().

        Args:
            agent_id: Identifier of the agent creating the note
            title: Brief title for the note
            content: Full content of the note
            category: Category of the note (default: OBSERVATION)
            tags: Optional list of tags for categorization
            related_file: Optional file path related to this note
            related_feature: Optional feature name this note relates to

        Returns:
            The created Note object

        Raises:
            ValueError: If required fields are empty

        Example:
            >>> notes = Notes(
            ...     workflow_id="my-workflow",
            ...     project_root=Path.cwd(),
            ...     event_logger=EventLogger(Path.cwd())
            ... )
            >>> note = notes.add(
            ...     agent_id="coder-agent",
            ...     title="Discovered API pattern",
            ...     content="The codebase uses repository pattern...",
            ...     category=NoteCategory.LEARNING,
            ...     tags=["architecture", "api"]
            ... )
        """
        # Create Note object for validation and return value
        note = Note(
            agent_id=agent_id,
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            related_file=related_file,
            related_feature=related_feature,
        )

        # Map category to event type
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

        # Emit event (writes to SQLite)
        self._event_logger.emit(
            workflow_id=self.workflow_id,
            event_type=event_type_map[category],
            data={
                "agent_id": agent_id,
                "title": title,
                "content": content,
                "category": category.value,
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
        """List notes with optional filtering via SQLite query.

        Args:
            agent_id: Optional filter by agent ID
            category: Optional filter by note category
            tag: Optional filter by tag
            limit: Optional maximum number of notes to return

        Returns:
            A list of Note objects matching the filters

        Example:
            >>> notes = Notes(workflow_id="my-workflow", ...)
            >>> all_notes = notes.list()
            >>> learnings = notes.list(category=NoteCategory.LEARNING)
            >>> recent = notes.list(limit=5)
        """
        if not self._events_db.exists():
            return []

        conn = sqlite3.connect(self._events_db)
        cursor = conn.cursor()

        # Build query with filters
        query = """
            SELECT data, timestamp
            FROM events
            WHERE workflow_id = ?
              AND event_type LIKE 'agent.note.%'
        """
        params: list = [self._workflow_id]

        if category:
            query += " AND event_type = ?"
            params.append(f"agent.note.{category.value}")

        query += " ORDER BY timestamp DESC"

        if limit and limit > 0:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)

        notes = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row[0])

                # Apply additional filters (agent_id, tag) in Python
                if agent_id and data.get("agent_id") != agent_id:
                    continue

                if tag and tag not in data.get("tags", []):
                    continue

                # Create Note object from event data
                note = Note(
                    agent_id=data["agent_id"],
                    title=data["title"],
                    content=data.get("content", ""),
                    category=NoteCategory(data.get("category", "observation")),
                    tags=data.get("tags", []),
                    related_file=data.get("related_file"),
                    related_feature=data.get("related_feature"),
                )
                notes.append(note)
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip malformed events
                continue

        conn.close()
        return notes

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
            >>> notes = Notes(workflow_id="my-workflow", ...)
            >>> results = notes.search("authentication bug")
        """
        all_notes = self.list()

        query_lower = query.lower()
        matching_notes = []

        for note in all_notes:
            if search_title and query_lower in note.title.lower():
                matching_notes.append(note)
            elif search_content and query_lower in note.content.lower():
                matching_notes.append(note)

        return matching_notes

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
