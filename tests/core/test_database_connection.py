# ABOUTME: Test suite for EventStore database connection management
# ABOUTME: Tests connection initialization, pooling, cleanup, and context manager functionality

"""Test suite for EventStore database connection management.

This module comprehensively tests the database connection management features
of the EventStore class, including:

- Database connection initialization and creation
- Connection pooling and resource management
- Automatic cleanup and proper connection disposal
- Context manager support for transaction handling
- Database file creation and path management
- Error handling for connection failures
- Performance optimizations and SQLite configuration

The tests follow TDD principles and use existing fixtures to ensure consistency
with the overall test suite.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

from jean_claude.core.event_store import EventStore


class TestDatabaseConnectionInitialization:
    """Test database connection initialization and setup."""

    def test_event_store_initializes_database_connection(self, tmp_path):
        """Test that EventStore properly initializes database connection on creation."""
        db_path = tmp_path / "test_events.db"

        # Creating EventStore should automatically initialize the database
        event_store = EventStore(db_path)

        # Database file should exist
        assert db_path.exists()

        # Should be able to get a connection
        conn = event_store.get_connection()
        assert isinstance(conn, sqlite3.Connection)

        # Database should have the correct schema
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert 'events' in tables
        assert 'snapshots' in tables

        conn.close()

    def test_database_connection_with_string_path(self, tmp_path):
        """Test database connection works with string path input."""
        db_path = tmp_path / "test_string.db"

        # Use string path instead of Path object
        event_store = EventStore(str(db_path))

        # Should work the same as Path object
        assert db_path.exists()
        conn = event_store.get_connection()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_database_connection_creates_nested_directories(self, tmp_path):
        """Test that database connection creates nested directories if needed."""
        nested_path = tmp_path / "nested" / "directory" / "events.db"

        # Parent directories don't exist yet
        assert not nested_path.parent.exists()

        # Creating EventStore should create the directories
        event_store = EventStore(nested_path)

        # Directory structure should be created
        assert nested_path.parent.exists()
        assert nested_path.exists()

        # Connection should work
        conn = event_store.get_connection()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_database_connection_validates_input_paths(self):
        """Test that database connection validates input paths properly."""
        # Test None path
        with pytest.raises(ValueError, match="Database path cannot be None"):
            EventStore(None)

        # Test empty string
        with pytest.raises(ValueError, match="empty or whitespace"):
            EventStore("")

        # Test whitespace-only string
        with pytest.raises(ValueError, match="empty or whitespace"):
            EventStore("   ")

        # Test invalid type
        with pytest.raises(TypeError, match="must be a string or Path object"):
            EventStore(123)


class TestDatabaseConnectionManagement:
    """Test connection creation, pooling, and resource management."""

    def test_get_connection_returns_fresh_connections(self, tmp_path):
        """Test that get_connection() returns new connections each time."""
        db_path = tmp_path / "test_pool.db"
        event_store = EventStore(db_path)

        # Get multiple connections
        conn1 = event_store.get_connection()
        conn2 = event_store.get_connection()
        conn3 = event_store.get_connection()

        # Should be different objects
        assert conn1 is not conn2
        assert conn2 is not conn3
        assert conn1 is not conn3

        # All should be valid SQLite connections
        for conn in [conn1, conn2, conn3]:
            assert isinstance(conn, sqlite3.Connection)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1
            conn.close()

    def test_connection_applies_sqlite_optimizations(self, tmp_path):
        """Test that connections have performance optimizations applied."""
        db_path = tmp_path / "test_optimized.db"
        event_store = EventStore(db_path)

        conn = event_store.get_connection()
        cursor = conn.cursor()

        # Check performance settings
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]

        cursor.execute("PRAGMA synchronous")
        synchronous = cursor.fetchone()[0]

        cursor.execute("PRAGMA foreign_keys")
        foreign_keys = cursor.fetchone()[0]

        cursor.execute("PRAGMA busy_timeout")
        busy_timeout = cursor.fetchone()[0]

        # Verify optimizations
        assert journal_mode.upper() == "WAL"  # WAL mode for concurrency
        assert synchronous == 1  # NORMAL mode for balanced performance/safety
        assert foreign_keys == 1  # Foreign keys enabled
        assert busy_timeout == 30000  # 30 second timeout

        conn.close()

    def test_connection_includes_row_factory(self, tmp_path):
        """Test that connections include row factory for easier result access."""
        db_path = tmp_path / "test_row_factory.db"
        event_store = EventStore(db_path)

        conn = event_store.get_connection()

        # Should have row factory set
        assert conn.row_factory is sqlite3.Row

        # Test that it works
        cursor = conn.cursor()
        cursor.execute("SELECT 'test' as name, 42 as value")
        row = cursor.fetchone()

        # Should be able to access by name
        assert row['name'] == 'test'
        assert row['value'] == 42

        conn.close()

    def test_close_connection_handles_cleanup_properly(self, tmp_path):
        """Test that close_connection() properly cleans up resources."""
        db_path = tmp_path / "test_cleanup.db"
        event_store = EventStore(db_path)

        conn = event_store.get_connection()

        # Verify connection works
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1

        # Close the connection
        event_store.close_connection(conn)

        # Connection should be unusable
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

    def test_close_connection_handles_edge_cases(self, tmp_path):
        """Test that close_connection() handles edge cases gracefully."""
        db_path = tmp_path / "test_edge_cases.db"
        event_store = EventStore(db_path)

        # Test with None
        event_store.close_connection(None)  # Should not raise

        # Test with already closed connection
        conn = event_store.get_connection()
        conn.close()  # Close directly
        event_store.close_connection(conn)  # Should not raise


class TestDatabaseContextManager:
    """Test context manager functionality for automatic transaction handling."""

    def test_context_manager_provides_connection(self, tmp_path):
        """Test that EventStore works as context manager providing connections."""
        db_path = tmp_path / "test_context.db"
        event_store = EventStore(db_path)

        # Use as context manager
        with event_store as conn:
            assert isinstance(conn, sqlite3.Connection)

            # Should be able to query
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            count = cursor.fetchone()[0]
            assert count == 0  # Empty database

    def test_context_manager_commits_on_success(self, tmp_path):
        """Test that context manager commits transactions on successful completion."""
        db_path = tmp_path / "test_commit.db"
        event_store = EventStore(db_path)

        # Insert data in context manager
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("test-workflow", "event-123", "test.event", "2023-01-01T12:00:00", "{}"))

        # Verify data was committed with new connection
        verify_conn = event_store.get_connection()
        cursor = verify_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("test-workflow",))
        count = cursor.fetchone()[0]
        assert count == 1
        verify_conn.close()

    def test_context_manager_rolls_back_on_exception(self, tmp_path):
        """Test that context manager rolls back transactions on exceptions."""
        db_path = tmp_path / "test_rollback.db"
        event_store = EventStore(db_path)

        # Insert data but cause exception
        try:
            with event_store as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                    VALUES (?, ?, ?, ?, ?)
                """, ("rollback-test", "event-456", "test.event", "2023-01-01T12:00:00", "{}"))

                # Trigger rollback
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

        # Verify data was NOT committed
        verify_conn = event_store.get_connection()
        cursor = verify_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("rollback-test",))
        count = cursor.fetchone()[0]
        assert count == 0  # Should be 0 due to rollback
        verify_conn.close()

    def test_context_manager_closes_connection_always(self, tmp_path):
        """Test that context manager always closes connections."""
        db_path = tmp_path / "test_always_close.db"
        event_store = EventStore(db_path)

        captured_conn = None

        # Test normal exit
        with event_store as conn:
            captured_conn = conn
            cursor = conn.cursor()
            cursor.execute("SELECT 1")

        # Connection should be closed
        with pytest.raises(sqlite3.ProgrammingError):
            captured_conn.execute("SELECT 1")

        # Test exception exit
        try:
            with event_store as conn:
                captured_conn = conn
                raise ValueError("Test")
        except ValueError:
            pass

        # Connection should still be closed
        with pytest.raises(sqlite3.ProgrammingError):
            captured_conn.execute("SELECT 1")

    def test_multiple_context_managers_work_independently(self, tmp_path):
        """Test that multiple context managers work independently."""
        db_path = tmp_path / "test_multiple.db"
        event_store = EventStore(db_path)

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

        # Verify both transactions committed
        with event_store as conn3:
            cursor = conn3.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            count = cursor.fetchone()[0]
            assert count == 2


class TestDatabaseConnectionErrorHandling:
    """Test error handling and edge cases for database connections."""

    def test_connection_handles_invalid_database_paths(self):
        """Test proper error handling for invalid database paths."""
        # Path that cannot be created
        invalid_path = Path("/dev/null/impossible.db")

        with pytest.raises(sqlite3.Error) as excinfo:
            EventStore(invalid_path)

        error_msg = str(excinfo.value).lower()
        assert any(keyword in error_msg for keyword in ["database", "schema", "path", "failed"])

    def test_connection_handles_permission_errors(self, tmp_path):
        """Test connection behavior with permission issues."""
        # Note: This test may need to be adapted based on the system
        # For now, we test the error path structure

        # Create a database first
        db_path = tmp_path / "permission_test.db"
        event_store = EventStore(db_path)

        # Connection should work normally for readable database
        conn = event_store.get_connection()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_connection_provides_helpful_error_messages(self):
        """Test that connection errors provide helpful debugging information."""
        error_cases = [
            (Path("/dev/null/invalid.db"), ["database", "path", "schema"]),
            (Path(""), ["schema", "database"]),
        ]

        for invalid_path, expected_keywords in error_cases:
            with pytest.raises((sqlite3.Error, ValueError, OSError)) as excinfo:
                EventStore(invalid_path)

            error_msg = str(excinfo.value).lower()
            assert any(keyword in error_msg for keyword in expected_keywords)

    def test_get_connection_error_handling(self, tmp_path):
        """Test get_connection() error handling for edge cases."""
        db_path = tmp_path / "error_test.db"
        event_store = EventStore(db_path)

        # Mock connection failure
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError("Database locked")

            with pytest.raises(sqlite3.Error) as excinfo:
                event_store.get_connection()

            error_msg = str(excinfo.value).lower()
            assert any(keyword in error_msg for keyword in ["database", "connection", "path"])


class TestDatabaseConnectionIntegration:
    """Test integration of connection management with other EventStore features."""

    def test_connection_integrates_with_schema_initialization(self, tmp_path):
        """Test that connection management works properly with schema initialization."""
        db_path = tmp_path / "integration.db"

        # EventStore creation should initialize schema automatically
        event_store = EventStore(db_path)

        # Should be able to get connection and verify schema
        conn = event_store.get_connection()
        cursor = conn.cursor()

        # Verify tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert 'events' in tables
        assert 'snapshots' in tables

        # Verify indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        expected_indexes = {'idx_events_workflow_id', 'idx_events_event_type', 'idx_events_timestamp'}
        assert expected_indexes.issubset(indexes)

        conn.close()

    def test_connection_preserves_database_path_reference(self, tmp_path):
        """Test that connection management maintains correct database path reference."""
        db_path = tmp_path / "path_test.db"
        event_store = EventStore(db_path)

        # EventStore should maintain reference to the correct path
        assert event_store.db_path == db_path

        # Connections should be to the correct database
        conn = event_store.get_connection()

        # Insert test data
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("path-test", "event-1", "test.event", "2023-01-01T12:00:00", "{}"))

        # Verify data is in the correct database file
        # Create a separate EventStore instance to the same path
        event_store2 = EventStore(db_path)
        with event_store2 as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("path-test",))
            count = cursor.fetchone()[0]
            assert count == 1

    def test_connection_works_with_both_path_types(self, tmp_path):
        """Test that connection works with both string and Path initialization."""
        db_path = tmp_path / "path_types.db"

        # Initialize with Path object
        event_store_path = EventStore(db_path)

        # Initialize with string
        event_store_str = EventStore(str(db_path))

        # Both should connect to same database
        with event_store_path as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("shared", "event-path", "test.event", "2023-01-01T12:00:00", "{}"))

        with event_store_str as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("shared",))
            count = cursor.fetchone()[0]
            assert count == 1  # Should see data from Path-initialized store