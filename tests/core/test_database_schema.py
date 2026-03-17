# ABOUTME: Test suite for SQLite database schema integration and functionality
# ABOUTME: Tests complete database schema including events and snapshots tables with EventStore integration

"""Test suite for SQLite database schema.

Tests the complete database schema functionality including:
- Events and snapshots table structure and constraints
- Data insertion and JSON handling
- Performance indexes
- Schema error handling
"""

import sqlite3
import json
from pathlib import Path
import pytest

from jean_claude.core.event_store import EventStore


class TestDatabaseSchemaIntegration:
    """Test database schema integration with EventStore."""

    def test_event_store_initializes_tables_and_indexes(self, tmp_path):
        """Test that EventStore creates events/snapshots tables and performance indexes."""
        event_store = EventStore(tmp_path / "test.db")

        with event_store as conn:
            cursor = conn.cursor()

            # Check both tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('events', 'snapshots')")
            tables = {row[0] for row in cursor.fetchall()}
            assert tables == {'events', 'snapshots'}

            # Check indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='events' ORDER BY name")
            indexes = [row[0] for row in cursor.fetchall()]
            custom_indexes = [idx for idx in indexes if not idx.startswith("sqlite_")]
            for expected in ['idx_events_event_type', 'idx_events_timestamp', 'idx_events_workflow_id']:
                assert expected in custom_indexes

    def test_events_table_schema_structure(self, tmp_path):
        """Test that events table has correct column types and constraints."""
        event_store = EventStore(tmp_path / "test.db")

        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(events)")
            columns = cursor.fetchall()
            column_info = {col[1]: (col[2], col[3], col[5]) for col in columns}

            assert "sequence_number" in column_info
            assert column_info["sequence_number"][0] == "INTEGER"
            assert column_info["sequence_number"][2] == 1  # PK

            assert "workflow_id" in column_info
            assert column_info["workflow_id"][1] == 1  # NOT NULL

            assert "event_type" in column_info
            assert column_info["event_type"][1] == 1  # NOT NULL

            assert "data" in column_info
            assert column_info["data"][1] == 1  # NOT NULL

    def test_snapshots_table_schema_structure(self, tmp_path):
        """Test that snapshots table has correct column types and constraints."""
        event_store = EventStore(tmp_path / "test.db")

        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(snapshots)")
            columns = cursor.fetchall()
            column_info = {col[1]: (col[2], col[3], col[5]) for col in columns}

            assert "workflow_id" in column_info
            assert column_info["workflow_id"][2] == 1  # PK

            assert "sequence_number" in column_info
            assert column_info["sequence_number"][1] == 1  # NOT NULL

            assert "state" in column_info
            assert column_info["state"][1] == 1  # NOT NULL

            assert "created_at" in column_info
            assert column_info["created_at"][1] == 1  # NOT NULL

    def test_data_insertion_and_json_handling(self, tmp_path):
        """Test events and snapshots table data insertion with JSON round-trip."""
        event_store = EventStore(tmp_path / "test.db")

        with event_store as conn:
            cursor = conn.cursor()

            # Insert event with complex JSON
            event_data = {"user_id": "user-123", "metadata": {"tags": ["important"], "size": 1024000}}
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("w-123", "e-456", "test.event", "2023-12-01T10:00:00Z", json.dumps(event_data)))

            cursor.execute("SELECT * FROM events WHERE workflow_id = ?", ("w-123",))
            row = cursor.fetchone()
            assert row is not None
            assert row["workflow_id"] == "w-123"
            assert json.loads(row["data"]) == event_data

            # Insert snapshot
            snap_data = {"current_state": "active", "event_count": 100}
            cursor.execute("""
                INSERT INTO snapshots (workflow_id, sequence_number, state, created_at)
                VALUES (?, ?, ?, ?)
            """, ("w-123", 100, json.dumps(snap_data), "2023-12-01T10:00:00Z"))

            cursor.execute("SELECT * FROM snapshots WHERE workflow_id = ?", ("w-123",))
            snap_row = cursor.fetchone()
            assert snap_row is not None
            assert json.loads(snap_row["state"]) == snap_data

    def test_unique_constraints(self, tmp_path):
        """Test event_id uniqueness and snapshots workflow_id primary key."""
        event_store = EventStore(tmp_path / "test.db")

        with event_store as conn:
            cursor = conn.cursor()

            # event_id unique constraint
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("w-1", "dup-id", "type1", "2023-12-01T10:00:00Z", "{}"))
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute("""
                    INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                    VALUES (?, ?, ?, ?, ?)
                """, ("w-2", "dup-id", "type2", "2023-12-01T10:01:00Z", "{}"))

        # snapshots workflow_id PK (need new connection after integrity error)
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO snapshots (workflow_id, sequence_number, state, created_at)
                VALUES (?, ?, ?, ?)
            """, ("w-1", 50, "{}", "2023-12-01T10:00:00Z"))
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute("""
                    INSERT INTO snapshots (workflow_id, sequence_number, state, created_at)
                    VALUES (?, ?, ?, ?)
                """, ("w-1", 100, "{}", "2023-12-01T10:01:00Z"))


class TestDatabaseSchemaCompatibility:
    """Test database schema compatibility with EventStore operations."""

    def test_eventstore_context_manager_transaction_handling(self, tmp_path):
        """Test context manager commits and persists data across connections."""
        event_store = EventStore(tmp_path / "test.db")

        with event_store as conn:
            conn.cursor().execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("ctx-test", "ctx-e-1", "test.context", "2023-12-01T10:00:00Z", "{}"))

        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("ctx-test",))
            assert cursor.fetchone()[0] == 1

    def test_schema_creation_with_string_and_path_objects(self, tmp_path):
        """Test schema works with both string and Path objects."""
        for path in [str(tmp_path / "s.db"), tmp_path / "p.db"]:
            store = EventStore(path)
            with store as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
                assert cursor.fetchone() is not None

    def test_database_file_creation_in_nested_directories(self, tmp_path):
        """Test database creation works in nested directories."""
        nested_path = tmp_path / "deep" / "nested" / "path" / "events.db"
        event_store = EventStore(nested_path)
        assert nested_path.exists()

        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert "events" in tables
            assert "snapshots" in tables


class TestDatabaseSchemaErrorHandling:
    """Test database schema error handling and edge cases."""

    def test_invalid_and_empty_paths(self):
        """Test that invalid, empty, and None paths are rejected."""
        with pytest.raises((ValueError, TypeError, OSError, sqlite3.Error)):
            EventStore("/root/impossible/readonly/path/db.sqlite")
        with pytest.raises(ValueError):
            EventStore("")
        with pytest.raises(ValueError):
            EventStore("   ")
        with pytest.raises(ValueError):
            EventStore(None)
        with pytest.raises(TypeError):
            EventStore(123)

    def test_database_corruption_resilience(self, tmp_path):
        """Test that corrupted database files are handled gracefully."""
        db_path = tmp_path / "corrupt.db"
        with open(db_path, "w") as f:
            f.write("This is not a valid SQLite database file")

        with pytest.raises(sqlite3.Error):
            EventStore(db_path)
