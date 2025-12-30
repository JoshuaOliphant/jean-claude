# ABOUTME: Test suite for SQLite database schema creation
# ABOUTME: Tests events and snapshots table creation with proper data types and constraints

"""Test suite for SQLite database schema creation.

Tests the database schema creation functionality including:
- Events table with sequence_number, workflow_id, event_id, event_type, timestamp, data
- Snapshots table with workflow_id, sequence_number, state, created_at
- Proper data types and constraints
- Idempotent schema creation (can be called multiple times safely)
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

# Import will fail until we implement the schema creation - that's expected in TDD
try:
    from jean_claude.core.schema_creation import create_event_store_schema
except ImportError:
    # Allow tests to be written before implementation
    create_event_store_schema = None


@pytest.mark.skipif(create_event_store_schema is None, reason="schema creation not implemented yet")
class TestEventStoreSchemaCreation:
    """Test database schema creation for event store."""

    def test_creates_events_table_with_correct_schema(self, tmp_path):
        """Test that create_event_store_schema creates events table with correct columns and types."""
        db_path = tmp_path / "test.db"

        create_event_store_schema(db_path)

        # Verify the table was created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check that events table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='events'
        """)
        assert cursor.fetchone() is not None

        # Check the schema of events table
        cursor.execute("PRAGMA table_info(events)")
        columns = cursor.fetchall()

        # Expected columns: (cid, name, type, notnull, dflt_value, pk)
        column_info = {col[1]: (col[2], col[3], col[5]) for col in columns}  # name: (type, not_null, pk)

        assert "sequence_number" in column_info
        assert column_info["sequence_number"][0] == "INTEGER"
        assert column_info["sequence_number"][2] == 1  # Primary key

        assert "workflow_id" in column_info
        assert column_info["workflow_id"][0] == "TEXT"
        assert column_info["workflow_id"][1] == 1  # NOT NULL

        assert "event_id" in column_info
        assert column_info["event_id"][0] == "TEXT"
        assert column_info["event_id"][1] == 1  # NOT NULL

        assert "event_type" in column_info
        assert column_info["event_type"][0] == "TEXT"
        assert column_info["event_type"][1] == 1  # NOT NULL

        assert "timestamp" in column_info
        assert column_info["timestamp"][0] == "TEXT"
        assert column_info["timestamp"][1] == 1  # NOT NULL

        assert "data" in column_info
        assert column_info["data"][0] == "JSON"
        assert column_info["data"][1] == 1  # NOT NULL

        conn.close()

    def test_creates_snapshots_table_with_correct_schema(self, tmp_path):
        """Test that create_event_store_schema creates snapshots table with correct columns and types."""
        db_path = tmp_path / "test.db"

        create_event_store_schema(db_path)

        # Verify the table was created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check that snapshots table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='snapshots'
        """)
        assert cursor.fetchone() is not None

        # Check the schema of snapshots table
        cursor.execute("PRAGMA table_info(snapshots)")
        columns = cursor.fetchall()

        # Expected columns: (cid, name, type, notnull, dflt_value, pk)
        column_info = {col[1]: (col[2], col[3], col[5]) for col in columns}  # name: (type, not_null, pk)

        assert "workflow_id" in column_info
        assert column_info["workflow_id"][0] == "TEXT"
        assert column_info["workflow_id"][2] == 1  # Primary key

        assert "sequence_number" in column_info
        assert column_info["sequence_number"][0] == "INTEGER"
        assert column_info["sequence_number"][1] == 1  # NOT NULL

        assert "state" in column_info
        assert column_info["state"][0] == "JSON"
        assert column_info["state"][1] == 1  # NOT NULL

        assert "created_at" in column_info
        assert column_info["created_at"][0] == "TEXT"
        assert column_info["created_at"][1] == 1  # NOT NULL

        conn.close()

    def test_schema_creation_is_idempotent(self, tmp_path):
        """Test that schema creation can be called multiple times safely."""
        db_path = tmp_path / "test.db"

        # Create schema the first time
        create_event_store_schema(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert test data to verify it's preserved
        cursor.execute("""
            INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
        """, ("test-workflow", "event-123", "test.event", "2023-01-01T12:00:00", "{}"))

        cursor.execute("""
            INSERT INTO snapshots (workflow_id, sequence_number, state, created_at)
            VALUES (?, ?, ?, ?)
        """, ("test-workflow", 1, "{}", "2023-01-01T12:00:00"))

        conn.commit()
        conn.close()

        # Create schema again - should not fail or affect existing data
        create_event_store_schema(db_path)

        # Verify data is still there
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM events")
        events_count = cursor.fetchone()[0]
        assert events_count == 1

        cursor.execute("SELECT COUNT(*) FROM snapshots")
        snapshots_count = cursor.fetchone()[0]
        assert snapshots_count == 1

        conn.close()

    def test_creates_database_file_if_not_exists(self, tmp_path):
        """Test that schema creation creates the database file if it doesn't exist."""
        db_path = tmp_path / "new_database.db"

        assert not db_path.exists()

        create_event_store_schema(db_path)

        assert db_path.exists()
        assert db_path.is_file()

    def test_accepts_path_object_and_string(self, tmp_path):
        """Test that schema creation accepts both Path objects and strings."""
        # Test with Path object
        db_path_obj = tmp_path / "path_obj.db"
        create_event_store_schema(db_path_obj)
        assert db_path_obj.exists()

        # Test with string path
        db_path_str = str(tmp_path / "path_str.db")
        create_event_store_schema(db_path_str)
        assert Path(db_path_str).exists()

    def test_handles_invalid_path_gracefully(self):
        """Test that schema creation handles invalid paths with clear error messages."""
        # Test with invalid path
        invalid_path = "/root/impossible/path/database.db"

        with pytest.raises((OSError, sqlite3.Error)) as excinfo:
            create_event_store_schema(invalid_path)

        # Should get a meaningful error about the path or file system
        error_msg = str(excinfo.value).lower()
        assert any(keyword in error_msg for keyword in ["database", "path", "permission", "file", "system", "read-only"])


@pytest.mark.skipif(create_event_store_schema is None, reason="schema creation not implemented yet")
class TestEventStoreConstraints:
    """Test database constraints and integrity rules."""

    def test_events_table_has_primary_key_autoincrement(self, tmp_path):
        """Test that events table sequence_number is auto-incrementing primary key."""
        db_path = tmp_path / "test.db"
        create_event_store_schema(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert events without specifying sequence_number
        cursor.execute("""
            INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
        """, ("workflow1", "event1", "type1", "2023-01-01T12:00:00", "{}"))

        cursor.execute("""
            INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
        """, ("workflow1", "event2", "type2", "2023-01-01T12:01:00", "{}"))

        conn.commit()

        # Verify auto-increment worked
        cursor.execute("SELECT sequence_number FROM events ORDER BY sequence_number")
        sequence_numbers = [row[0] for row in cursor.fetchall()]
        assert sequence_numbers == [1, 2]

        conn.close()

    def test_event_id_unique_constraint(self, tmp_path):
        """Test that event_id has unique constraint."""
        db_path = tmp_path / "test.db"
        create_event_store_schema(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert first event
        cursor.execute("""
            INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
        """, ("workflow1", "duplicate-id", "type1", "2023-01-01T12:00:00", "{}"))

        conn.commit()

        # Try to insert event with same event_id - should fail
        with pytest.raises(sqlite3.IntegrityError) as excinfo:
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("workflow2", "duplicate-id", "type2", "2023-01-01T12:01:00", "{}"))
            conn.commit()

        assert "UNIQUE constraint failed" in str(excinfo.value) or "unique" in str(excinfo.value).lower()

        conn.close()

    def test_snapshots_table_primary_key_constraint(self, tmp_path):
        """Test that snapshots table has workflow_id as primary key."""
        db_path = tmp_path / "test.db"
        create_event_store_schema(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert first snapshot
        cursor.execute("""
            INSERT INTO snapshots (workflow_id, sequence_number, state, created_at)
            VALUES (?, ?, ?, ?)
        """, ("workflow1", 1, "{}", "2023-01-01T12:00:00"))

        conn.commit()

        # Try to insert another snapshot with same workflow_id - should fail or update
        with pytest.raises(sqlite3.IntegrityError) as excinfo:
            cursor.execute("""
                INSERT INTO snapshots (workflow_id, sequence_number, state, created_at)
                VALUES (?, ?, ?, ?)
            """, ("workflow1", 2, "{}", "2023-01-01T12:01:00"))
            conn.commit()

        # SQLite may report this as "UNIQUE constraint" or "PRIMARY KEY constraint"
        error_msg = str(excinfo.value).lower()
        assert "constraint" in error_msg and ("unique" in error_msg or "primary key" in error_msg)

        conn.close()