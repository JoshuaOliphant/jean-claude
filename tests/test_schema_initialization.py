# ABOUTME: Test suite for EventStore._init_schema() private method
# ABOUTME: Tests schema initialization, idempotency, and database connection handling

"""Test suite for EventStore schema initialization.

Tests the EventStore._init_schema() private method including:
- Schema creation when database doesn't exist
- Idempotent operation (safe to call multiple times)
- Proper database connection handling and cleanup
- Integration with existing schema creation functions
- Error handling for database connection issues
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

# Import will fail until we implement the _init_schema method - that's expected in TDD
try:
    from jean_claude.core.event_store import EventStore
except ImportError:
    # Allow tests to be written before implementation
    EventStore = None


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreSchemaInitialization:
    """Test EventStore._init_schema() private method."""

    def test_init_schema_creates_database_and_tables(self, tmp_path):
        """Test that _init_schema() creates database file and tables when they don't exist."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Database file shouldn't exist yet
        assert not db_path.exists()

        # Call _init_schema()
        event_store._init_schema()

        # Database file should now exist
        assert db_path.exists()
        assert db_path.is_file()

        # Verify tables were created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check that events table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='events'
        """)
        assert cursor.fetchone() is not None

        # Check that snapshots table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='snapshots'
        """)
        assert cursor.fetchone() is not None

        conn.close()

    def test_init_schema_is_idempotent(self, tmp_path):
        """Test that _init_schema() can be called multiple times safely."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create schema the first time
        event_store._init_schema()

        # Add some test data to verify it's preserved
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
        """, ("test-workflow", "event-123", "test.event", "2023-01-01T12:00:00", "{}"))
        conn.commit()
        conn.close()

        # Call _init_schema() again - should not fail or affect existing data
        event_store._init_schema()

        # Verify data is still there
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        events_count = cursor.fetchone()[0]
        assert events_count == 1
        conn.close()

    def test_init_schema_creates_parent_directories(self, tmp_path):
        """Test that _init_schema() creates parent directories if they don't exist."""
        nested_path = tmp_path / "data" / "events" / "workflow.db"
        event_store = EventStore(nested_path)

        # Parent directories shouldn't exist yet
        assert not nested_path.parent.exists()

        # Call _init_schema()
        event_store._init_schema()

        # Database file and parent directories should now exist
        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_init_schema_uses_existing_schema_creation_functions(self, tmp_path):
        """Test that _init_schema() integrates with existing schema creation functions."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Mock the schema creation functions to verify they're called
        # Patch where the functions are USED (event_store), not where they're DEFINED (schema_creation)
        with patch('jean_claude.core.event_store.create_event_store_schema') as mock_create_schema, \
             patch('jean_claude.core.event_store.create_event_store_indexes') as mock_create_indexes:

            event_store._init_schema()

            # Verify the schema creation functions were called with correct path
            mock_create_schema.assert_called_once_with(db_path)
            mock_create_indexes.assert_called_once_with(db_path)

    def test_init_schema_handles_connection_errors_gracefully(self, tmp_path):
        """Test that _init_schema() handles database connection errors gracefully."""
        # Create a path in a location that might cause permissions issues
        readonly_path = Path("/dev/null/impossible.db")  # This should fail
        event_store = EventStore(readonly_path)

        # Should raise an appropriate exception with helpful message
        with pytest.raises((OSError, sqlite3.Error)) as excinfo:
            event_store._init_schema()

        # Error message should be helpful
        error_msg = str(excinfo.value).lower()
        assert any(keyword in error_msg for keyword in ["schema", "database", "path", "permission", "file"])

    def test_init_schema_with_string_path_stored_as_path_object(self, tmp_path):
        """Test that _init_schema() works when EventStore was initialized with string path."""
        db_path_str = str(tmp_path / "events.db")
        event_store = EventStore(db_path_str)

        # Verify the path was converted to Path object
        assert isinstance(event_store.db_path, Path)

        # Call _init_schema()
        event_store._init_schema()

        # Database should be created
        assert event_store.db_path.exists()

    def test_init_schema_preserves_existing_database_structure(self, tmp_path):
        """Test that _init_schema() preserves existing database structure and data."""
        db_path = tmp_path / "existing.db"

        # Create database manually first with existing schema creation
        from jean_claude.core.schema_creation import create_event_store_schema, create_event_store_indexes
        create_event_store_schema(db_path)
        create_event_store_indexes(db_path)

        # Add some data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
        """, ("existing-workflow", "event-456", "existing.event", "2023-02-01T10:00:00", '{"key": "value"}'))
        cursor.execute("""
            INSERT INTO snapshots (workflow_id, sequence_number, state, created_at)
            VALUES (?, ?, ?, ?)
        """, ("existing-workflow", 1, '{"state": "active"}', "2023-02-01T10:00:00"))
        conn.commit()
        conn.close()

        # Now create EventStore and call _init_schema()
        event_store = EventStore(db_path)
        event_store._init_schema()

        # Verify data is preserved
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM events")
        assert cursor.fetchone()[0] == 1

        cursor.execute("SELECT COUNT(*) FROM snapshots")
        assert cursor.fetchone()[0] == 1

        cursor.execute("SELECT data FROM events WHERE event_id = ?", ("event-456",))
        data = cursor.fetchone()[0]
        assert '"key": "value"' in data

        conn.close()


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreSchemaInitializationIntegration:
    """Test EventStore._init_schema() integration scenarios."""

    def test_init_schema_creates_both_tables_and_indexes(self, tmp_path):
        """Test that _init_schema() creates complete schema including indexes."""
        db_path = tmp_path / "test.db"
        event_store = EventStore(db_path)

        event_store._init_schema()

        # Verify indexes were created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check for indexes by querying sqlite_master
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name IN (
                'idx_events_workflow_id',
                'idx_events_event_type',
                'idx_events_timestamp'
            )
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        # Should have all three expected indexes
        expected_indexes = ['idx_events_workflow_id', 'idx_events_event_type', 'idx_events_timestamp']
        for expected_index in expected_indexes:
            assert expected_index in indexes

        conn.close()

    def test_init_schema_works_with_relative_paths(self):
        """Test that _init_schema() works with relative database paths."""
        # Use a relative path (will be created in current working directory)
        relative_path = Path("./test_relative_events.db")
        event_store = EventStore(relative_path)

        try:
            event_store._init_schema()

            # Database should exist at the relative path
            assert relative_path.exists()

            # Should be able to connect and query
            conn = sqlite3.connect(relative_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert 'events' in tables
            assert 'snapshots' in tables
            conn.close()

        finally:
            # Clean up relative database file
            if relative_path.exists():
                relative_path.unlink()

    def test_init_schema_error_handling_preserves_object_state(self, tmp_path):
        """Test that _init_schema() errors don't corrupt the EventStore object state."""
        db_path = tmp_path / "test.db"
        event_store = EventStore(db_path)

        # Mock schema creation to raise an error
        # Patch where the function is USED (event_store), not where it's DEFINED (schema_creation)
        with patch('jean_claude.core.event_store.create_event_store_schema') as mock_create:
            mock_create.side_effect = sqlite3.Error("Mock database error")

            # Should raise the error
            with pytest.raises(sqlite3.Error):
                event_store._init_schema()

        # EventStore object should still be in valid state
        assert event_store.db_path == db_path
        assert isinstance(event_store.db_path, Path)

        # Should be able to call _init_schema() again after fixing the issue
        event_store._init_schema()  # This should work now
        assert db_path.exists()

    def test_init_schema_method_is_private(self):
        """Test that _init_schema() is a private method (starts with underscore)."""
        # Verify the method exists and is private by naming convention
        assert hasattr(EventStore, '_init_schema')
        assert EventStore._init_schema.__name__ == '_init_schema'

        # Verify it's a method, not just an attribute
        import types
        assert isinstance(getattr(EventStore, '_init_schema'), types.FunctionType)