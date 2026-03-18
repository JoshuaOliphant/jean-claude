# ABOUTME: Test suite for EventStore database connection management
# ABOUTME: Tests connection initialization, pooling, cleanup, and context manager functionality

"""Test suite for EventStore database connection management.

Tests connection creation, SQLite optimizations, context manager transactions,
cleanup, and error handling for the EventStore class.
"""

import sqlite3
from unittest.mock import patch
import pytest

from jean_claude.core.event_store import EventStore


class TestDatabaseConnectionManagement:
    """Test connection creation, pooling, and resource management."""

    def test_get_connection_returns_fresh_optimized_connections(self, tmp_path):
        """Test connections are fresh, have row factory, and SQLite optimizations."""
        event_store = EventStore(tmp_path / "test.db")

        conn1 = event_store.get_connection()
        conn2 = event_store.get_connection()
        assert conn1 is not conn2

        # Check optimizations on conn1
        cursor = conn1.cursor()
        cursor.execute("PRAGMA journal_mode")
        assert cursor.fetchone()[0].upper() == "WAL"
        cursor.execute("PRAGMA synchronous")
        assert cursor.fetchone()[0] == 1
        cursor.execute("PRAGMA foreign_keys")
        assert cursor.fetchone()[0] == 1
        cursor.execute("PRAGMA busy_timeout")
        assert cursor.fetchone()[0] == 30000

        # Check row factory
        assert conn1.row_factory is sqlite3.Row
        cursor.execute("SELECT 'test' as name, 42 as value")
        row = cursor.fetchone()
        assert row['name'] == 'test'
        assert row['value'] == 42

        conn1.close()
        conn2.close()

    def test_close_connection_cleanup_and_edge_cases(self, tmp_path):
        """Test close_connection properly cleans up and handles edge cases."""
        event_store = EventStore(tmp_path / "test.db")

        # Normal close
        conn = event_store.get_connection()
        event_store.close_connection(conn)
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

        # Edge cases: None and already-closed
        event_store.close_connection(None)
        conn2 = event_store.get_connection()
        conn2.close()
        event_store.close_connection(conn2)  # Should not raise


class TestDatabaseContextManager:
    """Test context manager functionality for automatic transaction handling."""

    def test_context_manager_commits_and_closes(self, tmp_path):
        """Test context manager provides connection, commits on success, and closes."""
        event_store = EventStore(tmp_path / "test.db")

        captured_conn = None
        with event_store as conn:
            captured_conn = conn
            assert isinstance(conn, sqlite3.Connection)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("test-workflow", "event-123", "test.event", "2023-01-01T12:00:00", "{}"))

        # Connection should be closed
        with pytest.raises(sqlite3.ProgrammingError):
            captured_conn.execute("SELECT 1")

        # Data should be committed
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("test-workflow",))
            assert cursor.fetchone()[0] == 1

    def test_context_manager_rolls_back_on_exception(self, tmp_path):
        """Test context manager rolls back on exception and closes connection."""
        event_store = EventStore(tmp_path / "test.db")

        captured_conn = None
        try:
            with event_store as conn:
                captured_conn = conn
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                    VALUES (?, ?, ?, ?, ?)
                """, ("rollback-test", "event-456", "test.event", "2023-01-01T12:00:00", "{}"))
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Connection closed
        with pytest.raises(sqlite3.ProgrammingError):
            captured_conn.execute("SELECT 1")

        # Data NOT committed
        verify_conn = event_store.get_connection()
        cursor = verify_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("rollback-test",))
        assert cursor.fetchone()[0] == 0
        verify_conn.close()

    def test_multiple_context_managers_independent(self, tmp_path):
        """Test multiple sequential context managers commit independently."""
        event_store = EventStore(tmp_path / "test.db")

        with event_store as conn:
            conn.cursor().execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("w1", "e1", "test.event", "2023-01-01T12:00:00", "{}"))

        with event_store as conn:
            conn.cursor().execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("w2", "e2", "test.event", "2023-01-01T12:00:00", "{}"))

        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            assert cursor.fetchone()[0] == 2


class TestDatabaseConnectionErrorHandling:
    """Test error handling for database connections."""

    def test_get_connection_error_handling(self, tmp_path):
        """Test get_connection() error handling when sqlite3.connect fails."""
        event_store = EventStore(tmp_path / "test.db")

        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError("Database locked")
            with pytest.raises(sqlite3.Error) as excinfo:
                event_store.get_connection()
            error_msg = str(excinfo.value).lower()
            assert any(kw in error_msg for kw in ["database", "connection", "path"])
