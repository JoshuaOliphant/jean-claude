# ABOUTME: Test suite for EventStore connection management
# ABOUTME: Tests SQLite connection creation, pooling, resource cleanup, and context manager support

"""Test suite for EventStore connection management.

Tests the EventStore class connection management including:
- SQLite connection creation and management
- Proper resource cleanup and connection disposal
- Context manager support for automatic connection handling
- Connection pooling using sqlite3
- Error handling for connection failures
- Thread safety considerations for connection handling
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import pytest
from contextlib import contextmanager

# Import will fail until we implement the connection management features - expected in TDD
try:
    from jean_claude.core.event_store import EventStore
except ImportError:
    # Allow tests to be written before implementation
    EventStore = None


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreConnectionManagement:
    """Test EventStore connection creation and management."""

    def test_get_connection_creates_sqlite_connection(self, tmp_path):
        """Test that get_connection() returns a valid SQLite connection."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Initialize schema first
        event_store._init_schema()

        # Get connection
        conn = event_store.get_connection()

        # Should be a SQLite connection
        assert isinstance(conn, sqlite3.Connection)

        # Should be able to execute queries
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        assert len(tables) > 0  # Should have our event store tables

        conn.close()

    def test_get_connection_returns_new_connection_each_call(self, tmp_path):
        """Test that get_connection() returns a new connection each time."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)
        event_store._init_schema()

        # Get two connections
        conn1 = event_store.get_connection()
        conn2 = event_store.get_connection()

        # Should be different connection objects
        assert conn1 is not conn2

        # Both should be valid SQLite connections
        assert isinstance(conn1, sqlite3.Connection)
        assert isinstance(conn2, sqlite3.Connection)

        # Both should connect to the same database
        cursor1 = conn1.cursor()
        cursor2 = conn2.cursor()

        cursor1.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables1 = set(row[0] for row in cursor1.fetchall())

        cursor2.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables2 = set(row[0] for row in cursor2.fetchall())

        assert tables1 == tables2

        conn1.close()
        conn2.close()

    def test_get_connection_applies_sqlite_optimizations(self, tmp_path):
        """Test that get_connection() applies performance optimizations."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)
        event_store._init_schema()

        conn = event_store.get_connection()
        cursor = conn.cursor()

        # Check for common SQLite optimizations
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]

        cursor.execute("PRAGMA synchronous")
        synchronous = cursor.fetchone()[0]

        cursor.execute("PRAGMA foreign_keys")
        foreign_keys = cursor.fetchone()[0]

        # Should have performance-oriented settings
        assert journal_mode.upper() in ('WAL', 'MEMORY')  # WAL mode for better concurrency
        assert synchronous in (0, 1)  # Reduced synchronous for better performance
        assert foreign_keys == 1  # Foreign keys should be enabled for data integrity

        conn.close()

    def test_get_connection_handles_database_creation(self, tmp_path):
        """Test that get_connection() works even if database file doesn't exist yet."""
        db_path = tmp_path / "new_events.db"
        event_store = EventStore(db_path)

        # Database file doesn't exist yet
        assert not db_path.exists()

        # get_connection should still work (SQLite creates file automatically)
        conn = event_store.get_connection()

        assert isinstance(conn, sqlite3.Connection)
        assert db_path.exists()  # File should be created

        conn.close()

    def test_get_connection_raises_clear_error_on_invalid_path(self):
        """Test that get_connection() raises helpful error for invalid database path."""
        # Use a path that should cause permission errors
        invalid_path = Path("/dev/null/impossible.db")
        event_store = EventStore(invalid_path)

        with pytest.raises((OSError, sqlite3.Error)) as excinfo:
            event_store.get_connection()

        error_msg = str(excinfo.value).lower()
        assert any(keyword in error_msg for keyword in ["database", "connection", "path", "permission"])

    def test_get_connection_uses_stored_db_path(self, tmp_path):
        """Test that get_connection() uses the db_path stored during initialization."""
        db_path = tmp_path / "specific_events.db"
        event_store = EventStore(db_path)
        event_store._init_schema()

        conn = event_store.get_connection()

        # The connection should be to our specific database file
        # We can verify this by checking that our schema exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        events_table = cursor.fetchone()
        assert events_table is not None

        conn.close()


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreContextManager:
    """Test EventStore context manager support for automatic connection handling."""

    def test_context_manager_provides_connection(self, tmp_path):
        """Test that EventStore can be used as context manager providing a connection."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)
        event_store._init_schema()

        # Use as context manager
        with event_store as conn:
            # Should provide a SQLite connection
            assert isinstance(conn, sqlite3.Connection)

            # Should be able to use the connection
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_context_manager_automatically_closes_connection(self, tmp_path):
        """Test that context manager automatically closes connection on exit."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)
        event_store._init_schema()

        # Capture the connection to check it later
        captured_conn = None

        with event_store as conn:
            captured_conn = conn
            # Connection should be open during context
            assert not conn.in_transaction  # Basic check that connection is valid

        # Connection should be closed after context exit
        # In SQLite, trying to use a closed connection raises an error
        with pytest.raises(sqlite3.ProgrammingError):
            captured_conn.execute("SELECT 1")

    def test_context_manager_closes_connection_on_exception(self, tmp_path):
        """Test that context manager closes connection even when exception occurs."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)
        event_store._init_schema()

        captured_conn = None

        try:
            with event_store as conn:
                captured_conn = conn
                # Trigger an exception
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected exception

        # Connection should still be closed despite the exception
        with pytest.raises(sqlite3.ProgrammingError):
            captured_conn.execute("SELECT 1")

    def test_context_manager_commits_transaction_on_success(self, tmp_path):
        """Test that context manager commits transaction when no exceptions occur."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)
        event_store._init_schema()

        # Insert data within context manager
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("test-workflow", "event-123", "test.event", "2023-01-01T12:00:00", "{}"))

        # Verify data was committed by opening a new connection
        new_conn = event_store.get_connection()
        cursor = new_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("test-workflow",))
        count = cursor.fetchone()[0]
        assert count == 1
        new_conn.close()

    def test_context_manager_rolls_back_transaction_on_exception(self, tmp_path):
        """Test that context manager rolls back transaction when exception occurs."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)
        event_store._init_schema()

        # Insert data but trigger exception
        try:
            with event_store as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                    VALUES (?, ?, ?, ?, ?)
                """, ("test-workflow", "event-456", "test.event", "2023-01-01T12:00:00", "{}"))

                # Trigger exception before commit
                raise ValueError("Test rollback")
        except ValueError:
            pass  # Expected exception

        # Verify data was NOT committed by checking with new connection
        new_conn = event_store.get_connection()
        cursor = new_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("test-workflow",))
        count = cursor.fetchone()[0]
        assert count == 0  # Should be 0 due to rollback
        new_conn.close()

    def test_context_manager_supports_nested_usage(self, tmp_path):
        """Test that multiple context managers can be used with same EventStore."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)
        event_store._init_schema()

        # Use context manager multiple times
        with event_store as conn1:
            cursor = conn1.cursor()
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("workflow-1", "event-1", "test.event", "2023-01-01T12:00:00", "{}"))

        with event_store as conn2:
            cursor = conn2.cursor()
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("workflow-2", "event-2", "test.event", "2023-01-01T12:00:00", "{}"))

        # Verify both inserts were committed
        with event_store as conn3:
            cursor = conn3.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            total_count = cursor.fetchone()[0]
            assert total_count == 2


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreConnectionResourceManagement:
    """Test EventStore resource cleanup and connection disposal."""

    def test_close_connection_properly_disposes_connection(self, tmp_path):
        """Test that close_connection() properly disposes of a connection."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)
        event_store._init_schema()

        conn = event_store.get_connection()

        # Verify connection is usable
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1

        # Close the connection
        event_store.close_connection(conn)

        # Connection should now be unusable
        with pytest.raises(sqlite3.ProgrammingError):
            cursor.execute("SELECT 1")

    def test_close_connection_handles_already_closed_connection(self, tmp_path):
        """Test that close_connection() handles already closed connections gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)
        event_store._init_schema()

        conn = event_store.get_connection()

        # Close connection directly
        conn.close()

        # close_connection() should handle already closed connection gracefully
        event_store.close_connection(conn)  # Should not raise an exception

    def test_close_connection_handles_none_input(self, tmp_path):
        """Test that close_connection() handles None input gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Should handle None without error
        event_store.close_connection(None)  # Should not raise an exception

    def test_connection_cleanup_on_multiple_connections(self, tmp_path):
        """Test proper cleanup when multiple connections are created and closed."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)
        event_store._init_schema()

        connections = []

        # Create multiple connections
        for i in range(5):
            conn = event_store.get_connection()
            connections.append(conn)

        # Verify all connections work
        for conn in connections:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1

        # Close all connections
        for conn in connections:
            event_store.close_connection(conn)

        # All connections should now be unusable
        for conn in connections:
            with pytest.raises(sqlite3.ProgrammingError):
                conn.execute("SELECT 1")


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreConnectionErrorHandling:
    """Test EventStore connection error handling and edge cases."""

    def test_connection_methods_handle_corrupted_database(self, tmp_path):
        """Test connection handling when database file is corrupted."""
        db_path = tmp_path / "corrupted.db"

        # Create a corrupted database file
        with open(db_path, 'w') as f:
            f.write("This is not a SQLite database")

        event_store = EventStore(db_path)

        # Should raise appropriate error for corrupted database
        with pytest.raises((sqlite3.Error, sqlite3.DatabaseError)):
            event_store.get_connection()

    def test_connection_with_readonly_database_file(self, tmp_path):
        """Test connection behavior with read-only database file."""
        db_path = tmp_path / "readonly.db"
        event_store = EventStore(db_path)
        event_store._init_schema()

        # Make file read-only
        import stat
        db_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        try:
            # Should still be able to connect for reading
            conn = event_store.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            assert len(tables) > 0
            conn.close()

        finally:
            # Restore write permissions for cleanup
            db_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

    def test_context_manager_handles_connection_errors(self, tmp_path):
        """Test context manager behavior when connection creation fails."""
        # Use invalid path that will cause connection error
        invalid_path = Path("/dev/null/impossible.db")
        event_store = EventStore(invalid_path)

        # Context manager should propagate connection errors
        with pytest.raises((OSError, sqlite3.Error)):
            with event_store as conn:
                pass  # Should not reach here

    def test_connection_error_messages_are_helpful(self, tmp_path):
        """Test that connection error messages provide helpful debugging information."""
        # Test various error scenarios and verify helpful error messages
        test_cases = [
            (Path("/dev/null/impossible.db"), ["path", "permission", "directory"]),
            (Path(""), ["path", "empty", "invalid"]),
        ]

        for invalid_path, expected_keywords in test_cases:
            event_store = EventStore(invalid_path)

            with pytest.raises((OSError, sqlite3.Error, ValueError)) as excinfo:
                event_store.get_connection()

            error_msg = str(excinfo.value).lower()
            # Should contain at least one helpful keyword
            assert any(keyword in error_msg for keyword in expected_keywords)


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreConnectionIntegration:
    """Test EventStore connection management integration with existing functionality."""

    def test_connection_integrates_with_init_schema(self, tmp_path):
        """Test that connection management works properly with _init_schema()."""
        db_path = tmp_path / "integration.db"
        event_store = EventStore(db_path)

        # _init_schema should work with connection management
        event_store._init_schema()

        # Should be able to get connection to initialized database
        conn = event_store.get_connection()
        cursor = conn.cursor()

        # Verify schema was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert 'events' in tables
        assert 'snapshots' in tables

        conn.close()

    def test_connection_management_preserves_database_path(self, tmp_path):
        """Test that connection management maintains reference to correct database path."""
        db_path1 = tmp_path / "db1.db"
        db_path2 = tmp_path / "db2.db"

        event_store1 = EventStore(db_path1)
        event_store2 = EventStore(db_path2)

        event_store1._init_schema()
        event_store2._init_schema()

        # Add different data to each database
        with event_store1 as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("workflow-1", "event-1", "test.event", "2023-01-01T12:00:00", "{}"))

        with event_store2 as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("workflow-2", "event-2", "test.event", "2023-01-01T12:00:00", "{}"))

        # Verify each EventStore connects to its own database
        with event_store1 as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT workflow_id FROM events")
            workflow_ids = [row[0] for row in cursor.fetchall()]
            assert workflow_ids == ["workflow-1"]

        with event_store2 as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT workflow_id FROM events")
            workflow_ids = [row[0] for row in cursor.fetchall()]
            assert workflow_ids == ["workflow-2"]

    def test_connection_works_with_string_and_path_initialization(self, tmp_path):
        """Test that connection management works regardless of how EventStore was initialized."""
        db_path = tmp_path / "test.db"

        # Test with Path object initialization
        event_store_path = EventStore(db_path)
        event_store_path._init_schema()

        # Test with string initialization
        event_store_str = EventStore(str(db_path))

        # Both should connect to the same database
        with event_store_path as conn1:
            cursor = conn1.cursor()
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("shared-workflow", "event-1", "test.event", "2023-01-01T12:00:00", "{}"))

        with event_store_str as conn2:
            cursor = conn2.cursor()
            cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("shared-workflow",))
            count = cursor.fetchone()[0]
            assert count == 1  # Should see the data from the first EventStore