# ABOUTME: Event logging infrastructure for workflow and agent activities
# ABOUTME: Provides base models for events with SQLite and JSONL persistence

"""Event logging infrastructure.

This module provides the core event logging functionality for tracking workflow
and agent activities. Events are the fundamental unit of observability in the
system, capturing everything from workflow lifecycle changes to individual agent
tool usage.

Key components:

1. **Event Model**: Pydantic-based Event class with auto-generated UUIDs and
   timestamps, used to represent all system events.

2. **EventType Enum**: Namespaced event types organized by category (workflow.*,
   feature.*, agent.*) for easy filtering and querying.

3. **Dual Persistence**: Events are written to both SQLite (for querying) and
   JSONL files (for streaming/tailing) via SQLiteEventWriter and JSONLEventWriter.

4. **EventLogger**: High-level interface that combines both writers, providing
   both sync (emit) and async (emit_async) methods, plus querying capabilities.

Events are persisted to:
- SQLite: {project_root}/.jc/events.db (queryable across workflows)
- JSONL: {project_root}/agents/{workflow_id}/events.jsonl (per-workflow streaming)

This dual-write strategy ensures events are both queryable (SQLite) and
streamable/tail-able (JSONL) for different use cases.
"""

import json
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import UUID, uuid4

import anyio
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Enumeration of all event types in the system.

    Event types are namespaced by category:
    - workflow.*: Workflow lifecycle events
    - feature.*: Feature/task progress events
    - agent.*: Agent activity and tooling events
    """

    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PHASE_CHANGED = "workflow.phase_changed"
    WORKFLOW_COMPLETED = "workflow.completed"

    # Feature events
    FEATURE_PLANNED = "feature.planned"
    FEATURE_STARTED = "feature.started"
    FEATURE_COMPLETED = "feature.completed"
    FEATURE_FAILED = "feature.failed"

    # Agent events
    AGENT_TOOL_USE = "agent.tool_use"
    AGENT_TEST_RESULT = "agent.test_result"
    AGENT_ERROR = "agent.error"


class Event(BaseModel):
    """Base event model for all workflow and agent events.

    Events are the fundamental unit of observability in the system.
    Each event captures a single occurrence with metadata and payload.

    Attributes:
        id: Unique identifier for this event (auto-generated UUID)
        timestamp: When the event occurred (auto-generated)
        workflow_id: Identifier of the workflow this event belongs to
        event_type: Type of event from EventType enum
        data: Event-specific payload data (flexible dict)
    """

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.now)
    workflow_id: str
    event_type: EventType
    data: dict


class SQLiteEventWriter:
    """Writes events to a SQLite database.

    The SQLiteEventWriter persists events to a SQLite database with the following schema:
    - id TEXT PRIMARY KEY: Unique event identifier (UUID as string)
    - timestamp TEXT: ISO format timestamp
    - workflow_id TEXT: Workflow identifier
    - event_type TEXT: Type of event (from EventType enum)
    - data TEXT: JSON-serialized event data

    The database file and parent directories are created automatically on first use.

    Attributes:
        db_path: Path to the SQLite database file (typically .jc/events.db)
    """

    def __init__(self, db_path: Path):
        """Initialize the SQLite event writer.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._schema_initialized = False

    def _ensure_schema(self) -> None:
        """Ensure the database schema exists.

        Creates the parent directory if needed and initializes the events table.
        This method is idempotent and can be called multiple times safely.
        """
        # Create parent directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect and create table if it doesn't exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                workflow_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                data TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()
        self._schema_initialized = True

    def write_event(self, event: Event) -> None:
        """Write an event to the database.

        The event is serialized to the database schema with:
        - id as string representation of UUID
        - timestamp as ISO format string
        - workflow_id as-is
        - event_type as string value
        - data as JSON string

        Args:
            event: The event to write
        """
        # Ensure schema exists before writing
        if not self._schema_initialized:
            self._ensure_schema()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO events (id, timestamp, workflow_id, event_type, data)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(event.id),
                event.timestamp.isoformat(),
                event.workflow_id,
                event.event_type.value,
                json.dumps(event.data),
            ),
        )

        conn.commit()
        conn.close()

    async def write_event_async(self, event: Event) -> None:
        """Write an event to the database asynchronously.

        This method performs the same operation as write_event but runs the
        database operations in a worker thread to avoid blocking the async event loop.

        Args:
            event: The event to write
        """
        # Run the database write in a thread to avoid blocking
        # The sync write_event method will handle schema initialization
        await anyio.to_thread.run_sync(self.write_event, event)


class JSONLEventWriter:
    """Writes events to a JSONL (JSON Lines) file.

    The JSONLEventWriter appends events to a JSONL file, where each line contains
    a single JSON object representing one event. This format is ideal for streaming
    and tailing, as new events can be immediately read by other processes.

    Events are written in JSON mode (with UUIDs and datetimes as strings) to ensure
    full JSON compatibility. Each write is immediately flushed to disk to support
    real-time monitoring via `tail -f`.

    Attributes:
        jsonl_path: Path to the JSONL file (typically agents/{workflow_id}/events.jsonl)
    """

    def __init__(self, jsonl_path: Path):
        """Initialize the JSONL event writer.

        Args:
            jsonl_path: Path to the JSONL file where events will be written
        """
        self.jsonl_path = Path(jsonl_path)

    def write_event(self, event: Event) -> None:
        """Write an event to the JSONL file.

        The event is serialized to JSON format with:
        - id as string representation of UUID
        - timestamp as ISO format string
        - workflow_id as-is
        - event_type as string value
        - data as nested JSON object

        The file is opened in append mode and flushed after each write to ensure
        that events are immediately visible to other processes (e.g., for tailing).
        Parent directories are created automatically if they don't exist.

        Args:
            event: The event to write
        """
        # Create parent directories if they don't exist
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize event to JSON-compatible dict
        event_dict = event.model_dump(mode="json")

        # Append to file with newline
        with open(self.jsonl_path, 'a') as f:
            f.write(json.dumps(event_dict) + '\n')
            f.flush()  # Ensure data is written immediately for streaming/tailing

    async def write_event_async(self, event: Event) -> None:
        """Write an event to the JSONL file asynchronously.

        This method performs the same operation as write_event but uses anyio
        for async file I/O to avoid blocking the async event loop.

        Args:
            event: The event to write
        """
        # Create parent directories if they don't exist using anyio.Path
        await anyio.Path(self.jsonl_path.parent).mkdir(parents=True, exist_ok=True)

        # Serialize event to JSON-compatible dict
        event_dict = event.model_dump(mode="json")

        # Append to file asynchronously using anyio.Path
        async with await anyio.open_file(self.jsonl_path, 'a') as f:
            await f.write(json.dumps(event_dict) + '\n')
            await f.flush()  # Ensure data is written immediately for streaming/tailing


class EventLogger:
    """High-level event logger that writes to both SQLite and JSONL destinations.

    The EventLogger provides a unified interface for emitting events that are
    automatically persisted to both:
    - SQLite database at {project_root}/.jc/events.db (for querying)
    - JSONL file at {project_root}/agents/{workflow_id}/events.jsonl (for streaming)

    This dual-write strategy ensures events are both queryable (SQLite) and
    streamable/tail-able (JSONL) for different use cases.

    Attributes:
        project_root: Root directory of the project where events will be stored
        sqlite_writer: Writer for SQLite database persistence
    """

    def __init__(self, project_root: Path):
        """Initialize the event logger.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        # Initialize SQLite writer with standard path
        db_path = self.project_root / ".jc" / "events.db"
        self.sqlite_writer = SQLiteEventWriter(db_path)

    def emit(self, workflow_id: str, event_type: EventType | str, data: dict) -> None:
        """Emit an event to both SQLite and JSONL destinations.

        This method creates a new Event instance and writes it to both storage
        destinations in parallel (conceptually - currently sequential writes,
        but could be parallelized in the future).

        Args:
            workflow_id: Identifier of the workflow this event belongs to
            event_type: Type of event (EventType enum or string value)
            data: Event-specific payload data

        Example:
            >>> logger = EventLogger(Path("/project"))
            >>> logger.emit(
            ...     workflow_id="my-workflow",
            ...     event_type=EventType.WORKFLOW_STARTED,
            ...     data={"message": "Starting workflow"}
            ... )
        """
        # Create the event instance
        event = Event(
            workflow_id=workflow_id,
            event_type=event_type,
            data=data
        )

        # Write to SQLite
        self.sqlite_writer.write_event(event)

        # Write to JSONL (per-workflow file)
        jsonl_path = self.project_root / "agents" / workflow_id / "events.jsonl"
        jsonl_writer = JSONLEventWriter(jsonl_path)
        jsonl_writer.write_event(event)

    async def emit_async(self, workflow_id: str, event_type: EventType | str, data: dict) -> None:
        """Emit an event to both SQLite and JSONL destinations asynchronously.

        This method creates a new Event instance and writes it to both storage
        destinations using async I/O operations. This is the async version of emit()
        and should be used in async contexts for better performance.

        Args:
            workflow_id: Identifier of the workflow this event belongs to
            event_type: Type of event (EventType enum or string value)
            data: Event-specific payload data

        Example:
            >>> logger = EventLogger(Path("/project"))
            >>> await logger.emit_async(
            ...     workflow_id="my-workflow",
            ...     event_type=EventType.WORKFLOW_STARTED,
            ...     data={"message": "Starting workflow"}
            ... )
        """
        # Create the event instance
        event = Event(
            workflow_id=workflow_id,
            event_type=event_type,
            data=data
        )

        # Write to SQLite asynchronously
        await self.sqlite_writer.write_event_async(event)

        # Write to JSONL asynchronously (per-workflow file)
        jsonl_path = self.project_root / "agents" / workflow_id / "events.jsonl"
        jsonl_writer = JSONLEventWriter(jsonl_path)
        await jsonl_writer.write_event_async(event)

    def get_workflow_events(
        self,
        workflow_id: str,
        event_types: list[str] | None = None
    ) -> list[Event]:
        """Query events for a specific workflow from the SQLite database.

        Returns events filtered by workflow_id and optionally by event_type,
        ordered by timestamp in ascending (chronological) order.

        Args:
            workflow_id: The workflow to query events for
            event_types: Optional list of event type strings to filter by
                        (e.g., ["workflow.started", "workflow.completed"])

        Returns:
            List of Event objects ordered by timestamp ascending (oldest first)

        Example:
            >>> logger = EventLogger(Path("/project"))
            >>> # Get all events for a workflow
            >>> events = logger.get_workflow_events("my-workflow")
            >>> # Get only specific event types
            >>> events = logger.get_workflow_events(
            ...     "my-workflow",
            ...     event_types=["feature.started", "feature.completed"]
            ... )
        """
        # Ensure schema exists
        if not self.sqlite_writer._schema_initialized:
            self.sqlite_writer._ensure_schema()

        conn = sqlite3.connect(self.sqlite_writer.db_path)
        cursor = conn.cursor()

        # Build query based on whether we're filtering by event_type
        if event_types is None:
            # Get all events for this workflow
            cursor.execute(
                """
                SELECT id, timestamp, workflow_id, event_type, data
                FROM events
                WHERE workflow_id = ?
                ORDER BY timestamp ASC
                """,
                (workflow_id,)
            )
        else:
            # Get events filtered by event_type
            placeholders = ",".join("?" * len(event_types))
            query = f"""
                SELECT id, timestamp, workflow_id, event_type, data
                FROM events
                WHERE workflow_id = ? AND event_type IN ({placeholders})
                ORDER BY timestamp ASC
            """
            cursor.execute(query, (workflow_id, *event_types))

        rows = cursor.fetchall()
        conn.close()

        # Convert rows to Event objects
        events = []
        for row in rows:
            event = Event(
                id=UUID(row[0]),
                timestamp=datetime.fromisoformat(row[1]),
                workflow_id=row[2],
                event_type=row[3],
                data=json.loads(row[4])
            )
            events.append(event)

        return events

    def get_recent_events(
        self,
        limit: int = 100,
        event_types: list[str] | None = None
    ) -> list[Event]:
        """Query the most recent events across all workflows from the SQLite database.

        Returns events optionally filtered by event_type, ordered by timestamp
        in descending (reverse chronological) order, limited to the most recent N events.

        Args:
            limit: Maximum number of events to return (default: 100)
            event_types: Optional list of event type strings to filter by
                        (e.g., ["workflow.started", "workflow.completed"])

        Returns:
            List of Event objects ordered by timestamp descending (newest first),
            limited to the specified number of events

        Example:
            >>> logger = EventLogger(Path("/project"))
            >>> # Get 50 most recent events
            >>> events = logger.get_recent_events(limit=50)
            >>> # Get 20 most recent feature events
            >>> events = logger.get_recent_events(
            ...     limit=20,
            ...     event_types=["feature.started", "feature.completed"]
            ... )
        """
        # Ensure schema exists
        if not self.sqlite_writer._schema_initialized:
            self.sqlite_writer._ensure_schema()

        conn = sqlite3.connect(self.sqlite_writer.db_path)
        cursor = conn.cursor()

        # Build query based on whether we're filtering by event_type
        if event_types is None:
            # Get all recent events
            cursor.execute(
                """
                SELECT id, timestamp, workflow_id, event_type, data
                FROM events
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )
        else:
            # Get recent events filtered by event_type
            placeholders = ",".join("?" * len(event_types))
            query = f"""
                SELECT id, timestamp, workflow_id, event_type, data
                FROM events
                WHERE event_type IN ({placeholders})
                ORDER BY timestamp DESC
                LIMIT ?
            """
            cursor.execute(query, (*event_types, limit))

        rows = cursor.fetchall()
        conn.close()

        # Convert rows to Event objects
        events = []
        for row in rows:
            event = Event(
                id=UUID(row[0]),
                timestamp=datetime.fromisoformat(row[1]),
                workflow_id=row[2],
                event_type=row[3],
                data=json.loads(row[4])
            )
            events.append(event)

        return events
