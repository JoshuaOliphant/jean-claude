# ABOUTME: SQLite database schema creation for event store
# ABOUTME: Creates events and snapshots tables with proper data types and constraints

"""SQLite database schema creation for event store.

This module provides functionality to create the SQLite database schema for the event store,
including the events table and snapshots table with proper data types, constraints, and indexes.

The schema includes:
- Events table: stores workflow events with sequence number, metadata, and JSON data
- Snapshots table: stores workflow state snapshots for optimization

All table creation is idempotent and can be safely called multiple times.
"""

import sqlite3
from pathlib import Path
from typing import Union


def create_event_store_schema(db_path: Union[str, Path]) -> None:
    """Create the event store database schema with events and snapshots tables.

    Creates the SQLite database schema for the event store, including:
    - Events table with sequence_number (PK), workflow_id, event_id (unique),
      event_type, timestamp, and data (JSON)
    - Snapshots table with workflow_id (PK), sequence_number, state (JSON), and created_at

    The function is idempotent and can be safely called multiple times. If the tables
    already exist, no changes are made to the schema or existing data.

    Args:
        db_path: Path to the SQLite database file (string or Path object)

    Raises:
        OSError: If the database file cannot be created or accessed
        sqlite3.Error: If there's an error creating the database schema

    Example:
        >>> create_event_store_schema("/path/to/eventstore.db")
        >>> create_event_store_schema(Path("./data/events.db"))
    """
    # Convert to Path object for consistent handling
    if isinstance(db_path, str):
        db_path = Path(db_path)

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Connect to database (creates file if it doesn't exist)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                sequence_number INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                event_id TEXT UNIQUE NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                data JSON NOT NULL
            )
        """)

        # Create snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                workflow_id TEXT PRIMARY KEY,
                sequence_number INTEGER NOT NULL,
                state JSON NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Commit the changes
        conn.commit()

    except Exception as e:
        # Re-raise with context about what we were trying to do
        if conn:
            conn.close()
        raise sqlite3.Error(f"Failed to create event store schema at {db_path}: {e}") from e

    finally:
        # Ensure connection is closed
        if conn:
            conn.close()


def create_event_store_indexes(db_path: Union[str, Path]) -> None:
    """Create performance indexes for the event store database.

    Creates indexes on the events table for commonly queried columns:
    - idx_events_workflow_id: Index on workflow_id for filtering by workflow
    - idx_events_event_type: Index on event_type for filtering by event type
    - idx_events_timestamp: Index on timestamp for time-based queries and ordering

    The function is idempotent and can be safely called multiple times. If the indexes
    already exist, no changes are made to the database.

    Args:
        db_path: Path to the SQLite database file (string or Path object)

    Raises:
        OSError: If the database file cannot be accessed
        sqlite3.Error: If there's an error creating the indexes

    Example:
        >>> create_event_store_indexes("/path/to/eventstore.db")
        >>> create_event_store_indexes(Path("./data/events.db"))
    """
    # Convert to Path object for consistent handling
    if isinstance(db_path, str):
        db_path = Path(db_path)

    conn = None
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create index on workflow_id for filtering by workflow
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_workflow_id
            ON events (workflow_id)
        """)

        # Create index on event_type for filtering by event type
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_event_type
            ON events (event_type)
        """)

        # Create index on timestamp for time-based queries and ordering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp
            ON events (timestamp)
        """)

        # Commit the changes
        conn.commit()

    except Exception as e:
        # Re-raise with context about what we were trying to do
        if conn:
            conn.close()
        raise sqlite3.Error(f"Failed to create event store indexes at {db_path}: {e}") from e

    finally:
        # Ensure connection is closed
        if conn:
            conn.close()