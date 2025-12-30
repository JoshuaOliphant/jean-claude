# Create SQLite event store schema and initialization

## Description

Create the core SQLite database schema for event sourcing with events and snapshots tables.

Files to create:
- src/jean_claude/core/event_store.py
- src/jean_claude/core/events.py

Schema requirements:
1. events table:
   - sequence_number (INTEGER PRIMARY KEY AUTOINCREMENT)
   - workflow_id (TEXT NOT NULL)
   - event_id (TEXT UNIQUE NOT NULL)
   - event_type (TEXT NOT NULL)
   - timestamp (TEXT NOT NULL)
   - data (JSON NOT NULL)
   - Indexes on: workflow_id, event_type, timestamp

2. snapshots table:
   - workflow_id (TEXT PRIMARY KEY)
   - sequence_number (INTEGER NOT NULL)
   - state (JSON NOT NULL)
   - created_at (TEXT NOT NULL)

Event model (Pydantic):
- WorkflowEvent dataclass with frozen=True
- Fields: event_id (UUID), workflow_id, event_type, timestamp, data (dict)

EventStore class:
- __init__(db_path: Path)
- _init_schema() - Create tables if not exist
- Connection pooling with sqlite3

Reference: docs/ARCHITECTURE.md section 'SQLite Event Store Schema'

Acceptance criteria:
- SQLite database created at specified path
- Tables created with correct schema
- WorkflowEvent Pydantic model with validation
- EventStore class initializes database
- Unit tests verify schema creation

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-2fj
- **Status**: in_progress
- **Created**: 2025-12-29 08:59:12
- **Updated**: 2025-12-30 11:46:00
