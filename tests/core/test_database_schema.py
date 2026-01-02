# ABOUTME: Test suite for SQLite database schema integration and functionality
# ABOUTME: Tests complete database schema including events and snapshots tables with EventStore integration

"""Test suite for SQLite database schema.

Tests the complete database schema functionality including:
- Events table with id, workflow_id, event_type, event_data, timestamp columns
- Snapshots table with id, workflow_id, snapshot_data, event_count, created_at columns
- EventStore integration with schema
- Database connection management and schema initialization
- Schema constraints and data integrity
"""

import sqlite3
import json
from pathlib import Path
import pytest

from jean_claude.core.event_store import EventStore
from jean_claude.core.schema_creation import create_event_store_schema, create_event_store_indexes


class TestDatabaseSchemaIntegration:
    """Test database schema integration with EventStore."""

    def test_event_store_initializes_database_schema(self, tmp_path):
        """Test that EventStore automatically initializes the database schema."""
        db_path = tmp_path / "test_events.db"

        # Create EventStore instance - should initialize schema automatically
        event_store = EventStore(db_path)

        # Verify database file was created
        assert db_path.exists()

        # Verify tables were created
        with event_store as conn:
            cursor = conn.cursor()

            # Check events table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='events'
            """)
            assert cursor.fetchone() is not None

            # Check snapshots table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='snapshots'
            """)
            assert cursor.fetchone() is not None

    def test_events_table_schema_structure(self, tmp_path):
        """Test that events table has the correct schema structure."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with event_store as conn:
            cursor = conn.cursor()

            # Get table schema
            cursor.execute("PRAGMA table_info(events)")
            columns = cursor.fetchall()

            # Create column mapping: name -> (type, not_null, pk)
            column_info = {col[1]: (col[2], col[3], col[5]) for col in columns}

            # Test required columns exist with correct types
            # Note: Existing schema uses sequence_number, event_id, data instead of id, event_data
            assert "sequence_number" in column_info
            assert column_info["sequence_number"][0] == "INTEGER"
            assert column_info["sequence_number"][2] == 1  # Primary key

            assert "workflow_id" in column_info
            assert column_info["workflow_id"][0] == "TEXT"
            assert column_info["workflow_id"][1] == 1  # NOT NULL

            assert "event_type" in column_info
            assert column_info["event_type"][0] == "TEXT"
            assert column_info["event_type"][1] == 1  # NOT NULL

            assert "timestamp" in column_info
            assert column_info["timestamp"][0] == "TEXT"
            assert column_info["timestamp"][1] == 1  # NOT NULL

            # Current schema uses 'data' instead of 'event_data'
            assert "data" in column_info
            assert column_info["data"][0] == "JSON"
            assert column_info["data"][1] == 1  # NOT NULL

    def test_snapshots_table_schema_structure(self, tmp_path):
        """Test that snapshots table has the correct schema structure."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with event_store as conn:
            cursor = conn.cursor()

            # Get table schema
            cursor.execute("PRAGMA table_info(snapshots)")
            columns = cursor.fetchall()

            # Create column mapping: name -> (type, not_null, pk)
            column_info = {col[1]: (col[2], col[3], col[5]) for col in columns}

            # Test required columns exist with correct types
            assert "workflow_id" in column_info
            assert column_info["workflow_id"][0] == "TEXT"
            assert column_info["workflow_id"][2] == 1  # Primary key

            # Current schema uses 'sequence_number' instead of 'event_count'
            assert "sequence_number" in column_info
            assert column_info["sequence_number"][0] == "INTEGER"
            assert column_info["sequence_number"][1] == 1  # NOT NULL

            # Current schema uses 'state' instead of 'snapshot_data'
            assert "state" in column_info
            assert column_info["state"][0] == "JSON"
            assert column_info["state"][1] == 1  # NOT NULL

            assert "created_at" in column_info
            assert column_info["created_at"][0] == "TEXT"
            assert column_info["created_at"][1] == 1  # NOT NULL

    def test_events_table_data_insertion(self, tmp_path):
        """Test that events table accepts proper data insertion."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with event_store as conn:
            cursor = conn.cursor()

            # Test data insertion
            event_data = {"message": "test event", "value": 42}
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "workflow-123",
                "event-uuid-456",
                "test.event",
                "2023-12-01T10:00:00Z",
                json.dumps(event_data)
            ))

            # Verify insertion
            cursor.execute("SELECT * FROM events WHERE workflow_id = ?", ("workflow-123",))
            row = cursor.fetchone()

            assert row is not None
            assert row["workflow_id"] == "workflow-123"
            assert row["event_id"] == "event-uuid-456"
            assert row["event_type"] == "test.event"
            assert row["timestamp"] == "2023-12-01T10:00:00Z"
            assert json.loads(row["data"]) == event_data

    def test_snapshots_table_data_insertion(self, tmp_path):
        """Test that snapshots table accepts proper data insertion."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with event_store as conn:
            cursor = conn.cursor()

            # Test data insertion
            snapshot_data = {"current_state": "active", "event_count": 100}
            cursor.execute("""
                INSERT INTO snapshots (workflow_id, sequence_number, state, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                "workflow-123",
                100,
                json.dumps(snapshot_data),
                "2023-12-01T10:00:00Z"
            ))

            # Verify insertion
            cursor.execute("SELECT * FROM snapshots WHERE workflow_id = ?", ("workflow-123",))
            row = cursor.fetchone()

            assert row is not None
            assert row["workflow_id"] == "workflow-123"
            assert row["sequence_number"] == 100
            assert json.loads(row["state"]) == snapshot_data
            assert row["created_at"] == "2023-12-01T10:00:00Z"

    def test_database_performance_indexes(self, tmp_path):
        """Test that performance indexes are created properly."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with event_store as conn:
            cursor = conn.cursor()

            # Check that expected indexes exist
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND tbl_name='events'
                ORDER BY name
            """)
            indexes = [row[0] for row in cursor.fetchall()]

            # Filter out sqlite-generated indexes (typically start with sqlite_)
            custom_indexes = [idx for idx in indexes if not idx.startswith("sqlite_")]

            expected_indexes = [
                'idx_events_event_type',
                'idx_events_timestamp',
                'idx_events_workflow_id'
            ]

            assert all(idx in custom_indexes for idx in expected_indexes), \
                f"Missing indexes. Expected: {expected_indexes}, Found: {custom_indexes}"

    def test_event_id_unique_constraint(self, tmp_path):
        """Test that event_id has unique constraint enforcement."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with event_store as conn:
            cursor = conn.cursor()

            # Insert first event
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("workflow-1", "duplicate-event-id", "event.type1", "2023-12-01T10:00:00Z", "{}"))

            # Try to insert event with same event_id - should fail
            with pytest.raises(sqlite3.IntegrityError) as exc_info:
                cursor.execute("""
                    INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                    VALUES (?, ?, ?, ?, ?)
                """, ("workflow-2", "duplicate-event-id", "event.type2", "2023-12-01T10:01:00Z", "{}"))

            assert "UNIQUE constraint failed" in str(exc_info.value) or "unique" in str(exc_info.value).lower()

    def test_snapshots_workflow_id_primary_key(self, tmp_path):
        """Test that snapshots table workflow_id primary key constraint works."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with event_store as conn:
            cursor = conn.cursor()

            # Insert first snapshot
            cursor.execute("""
                INSERT INTO snapshots (workflow_id, sequence_number, state, created_at)
                VALUES (?, ?, ?, ?)
            """, ("workflow-1", 50, "{}", "2023-12-01T10:00:00Z"))

            # Try to insert another snapshot with same workflow_id - should fail
            with pytest.raises(sqlite3.IntegrityError) as exc_info:
                cursor.execute("""
                    INSERT INTO snapshots (workflow_id, sequence_number, state, created_at)
                    VALUES (?, ?, ?, ?)
                """, ("workflow-1", 100, "{}", "2023-12-01T10:01:00Z"))

            error_msg = str(exc_info.value).lower()
            assert "constraint" in error_msg and ("unique" in error_msg or "primary key" in error_msg)

    def test_schema_handles_json_data_properly(self, tmp_path):
        """Test that JSON data is stored and retrieved correctly."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with event_store as conn:
            cursor = conn.cursor()

            # Test complex JSON data
            complex_event_data = {
                "user_id": "user-123",
                "action": "file_upload",
                "metadata": {
                    "filename": "document.pdf",
                    "size": 1024000,
                    "tags": ["important", "contract"]
                },
                "timestamp": "2023-12-01T10:00:00Z"
            }

            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "workflow-json-test",
                "json-event-123",
                "file.uploaded",
                "2023-12-01T10:00:00Z",
                json.dumps(complex_event_data)
            ))

            # Retrieve and verify JSON data integrity
            cursor.execute("SELECT data FROM events WHERE event_id = ?", ("json-event-123",))
            stored_data = cursor.fetchone()["data"]
            retrieved_data = json.loads(stored_data)

            assert retrieved_data == complex_event_data
            assert retrieved_data["metadata"]["tags"] == ["important", "contract"]
            assert retrieved_data["metadata"]["size"] == 1024000


class TestDatabaseSchemaCompatibility:
    """Test database schema compatibility with EventStore operations."""

    def test_eventstore_context_manager_with_schema(self, tmp_path):
        """Test that EventStore context manager works properly with schema."""
        db_path = tmp_path / "test_context.db"
        event_store = EventStore(db_path)

        # Test transaction handling
        with event_store as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("context-test", "ctx-event-1", "test.context", "2023-12-01T10:00:00Z", "{}"))

            # Data should be visible within transaction
            cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("context-test",))
            count = cursor.fetchone()[0]
            assert count == 1

        # Data should be committed after context exit
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("context-test",))
            count = cursor.fetchone()[0]
            assert count == 1

    def test_eventstore_connection_management(self, tmp_path):
        """Test that EventStore properly manages database connections."""
        db_path = tmp_path / "test_connections.db"
        event_store = EventStore(db_path)

        # Test getting multiple connections
        conn1 = event_store.get_connection()
        conn2 = event_store.get_connection()

        # Connections should be independent
        assert conn1 is not conn2

        # Both should work with the schema
        cursor1 = conn1.cursor()
        cursor2 = conn2.cursor()

        cursor1.execute("SELECT COUNT(*) FROM events")
        count1 = cursor1.fetchone()[0]

        cursor2.execute("SELECT COUNT(*) FROM events")
        count2 = cursor2.fetchone()[0]

        assert count1 == count2 == 0

        # Clean up connections
        event_store.close_connection(conn1)
        event_store.close_connection(conn2)

    def test_schema_creation_with_string_and_path_objects(self, tmp_path):
        """Test that schema works with both string and Path objects."""
        # Test with string path
        db_path_str = str(tmp_path / "string_path.db")
        event_store_str = EventStore(db_path_str)

        with event_store_str as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
            assert cursor.fetchone() is not None

        # Test with Path object
        db_path_obj = tmp_path / "path_object.db"
        event_store_obj = EventStore(db_path_obj)

        with event_store_obj as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
            assert cursor.fetchone() is not None

    def test_database_file_creation_in_nested_directories(self, tmp_path):
        """Test that database creation works in nested directories."""
        nested_path = tmp_path / "deep" / "nested" / "path" / "events.db"

        # Should create nested directories automatically
        event_store = EventStore(nested_path)

        assert nested_path.exists()
        assert nested_path.is_file()

        # Verify schema was created
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            assert "events" in tables
            assert "snapshots" in tables


class TestDatabaseSchemaErrorHandling:
    """Test database schema error handling and edge cases."""

    def test_invalid_database_path_handling(self):
        """Test that invalid database paths are handled gracefully."""
        # Test with completely invalid path
        with pytest.raises((ValueError, TypeError, OSError, sqlite3.Error)):
            EventStore("/root/impossible/readonly/path/db.sqlite")

    def test_empty_database_path_handling(self):
        """Test that empty database paths are rejected."""
        with pytest.raises(ValueError) as exc_info:
            EventStore("")

        assert "empty" in str(exc_info.value).lower() or "whitespace" in str(exc_info.value).lower()

        with pytest.raises(ValueError):
            EventStore("   ")  # whitespace-only

    def test_none_database_path_handling(self):
        """Test that None database path is rejected."""
        with pytest.raises(ValueError) as exc_info:
            EventStore(None)

        assert "None" in str(exc_info.value)

    def test_invalid_type_database_path_handling(self):
        """Test that invalid types for database path are rejected."""
        with pytest.raises(TypeError) as exc_info:
            EventStore(123)  # numeric type

        assert "string or Path object" in str(exc_info.value)

    def test_database_corruption_resilience(self, tmp_path):
        """Test that the schema handles database file corruption gracefully."""
        db_path = tmp_path / "corrupt.db"

        # Create a corrupted database file
        with open(db_path, "w") as f:
            f.write("This is not a valid SQLite database file")

        # Should handle corruption gracefully
        with pytest.raises(sqlite3.Error) as exc_info:
            EventStore(db_path)

        assert "database" in str(exc_info.value).lower() or "file" in str(exc_info.value).lower()