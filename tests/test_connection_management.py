# ABOUTME: Test suite for EventStore connection management
# ABOUTME: Tests SQLite connection creation, pooling, resource cleanup, and context manager support

"""Test suite for EventStore connection management.

Tests connection creation, context manager transactions, resource cleanup,
and error handling. Complements tests/core/test_database_connection.py
with integration-level scenarios.
"""

import sqlite3
import stat
from pathlib import Path
from unittest.mock import patch
import pytest

try:
    from jean_claude.core.event_store import EventStore
except ImportError:
    EventStore = None


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreConnectionManagement:
    """Test EventStore connection creation and management."""

    def test_get_connection_creates_valid_optimized_connection(self, tmp_path):
        """Test get_connection returns valid SQLite connections with optimizations."""
        event_store = EventStore(tmp_path / "test.db")

        conn1 = event_store.get_connection()
        conn2 = event_store.get_connection()

        assert isinstance(conn1, sqlite3.Connection)
        assert conn1 is not conn2

        cursor = conn1.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert 'events' in tables

        # Check optimizations
        cursor.execute("PRAGMA journal_mode")
        assert cursor.fetchone()[0].upper() in ('WAL', 'MEMORY')
        cursor.execute("PRAGMA foreign_keys")
        assert cursor.fetchone()[0] == 1

        conn1.close()
        conn2.close()

    def test_close_connection_and_edge_cases(self, tmp_path):
        """Test close_connection properly disposes and handles edge cases."""
        event_store = EventStore(tmp_path / "test.db")

        conn = event_store.get_connection()
        event_store.close_connection(conn)
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

        # Edge cases
        event_store.close_connection(None)
        conn2 = event_store.get_connection()
        conn2.close()
        event_store.close_connection(conn2)

    def test_multiple_connections_create_and_cleanup(self, tmp_path):
        """Test creating and closing multiple connections."""
        event_store = EventStore(tmp_path / "test.db")
        connections = [event_store.get_connection() for _ in range(5)]

        for conn in connections:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1

        for conn in connections:
            event_store.close_connection(conn)

        for conn in connections:
            with pytest.raises(sqlite3.ProgrammingError):
                conn.execute("SELECT 1")


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreContextManager:
    """Test EventStore context manager support."""

    def test_context_manager_commit_close_and_rollback(self, tmp_path):
        """Test context manager commits on success, closes connection, and rolls back on error."""
        event_store = EventStore(tmp_path / "test.db")

        # Successful commit and close
        captured_conn = None
        with event_store as conn:
            captured_conn = conn
            assert isinstance(conn, sqlite3.Connection)
            conn.cursor().execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("test-wf", "e-123", "test.event", "2023-01-01T12:00:00", "{}"))

        with pytest.raises(sqlite3.ProgrammingError):
            captured_conn.execute("SELECT 1")

        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("test-wf",))
            assert cursor.fetchone()[0] == 1

        # Rollback on exception
        try:
            with event_store as conn:
                conn.cursor().execute("""
                    INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                    VALUES (?, ?, ?, ?, ?)
                """, ("rollback-wf", "e-456", "test.event", "2023-01-01T12:00:00", "{}"))
                raise ValueError("Test rollback")
        except ValueError:
            pass

        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("rollback-wf",))
            assert cursor.fetchone()[0] == 0

    def test_multiple_sequential_context_managers(self, tmp_path):
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


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreErrorHandling:
    """Test EventStore connection error handling."""

    def test_corrupted_database_file(self, tmp_path):
        """Test handling of corrupted database files."""
        db_path = tmp_path / "corrupted.db"
        with open(db_path, 'w') as f:
            f.write("This is not a SQLite database")

        with pytest.raises((sqlite3.Error, sqlite3.DatabaseError)):
            EventStore(db_path)

    def test_invalid_path_error_messages(self):
        """Test error handling for invalid paths."""
        for invalid_path, keywords in [
            (Path("/dev/null/impossible.db"), ["path", "permission", "directory", "schema"]),
            (Path(""), ["schema", "database", "initialize"]),
        ]:
            with pytest.raises((OSError, sqlite3.Error, ValueError)) as excinfo:
                EventStore(invalid_path)
            error_msg = str(excinfo.value).lower()
            assert any(kw in error_msg for kw in keywords)

    def test_readonly_database_still_readable(self, tmp_path):
        """Test that read-only database can still be queried."""
        db_path = tmp_path / "readonly.db"
        event_store = EventStore(db_path)

        db_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        try:
            conn = event_store.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            assert len(cursor.fetchall()) > 0
            conn.close()
        finally:
            db_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreConnectionIntegration:
    """Test EventStore connection integration scenarios."""

    def test_separate_event_stores_maintain_independent_data(self, tmp_path):
        """Test two EventStores to different paths maintain separate data."""
        store1 = EventStore(tmp_path / "db1.db")
        store2 = EventStore(tmp_path / "db2.db")

        with store1 as conn:
            conn.cursor().execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("w1", "e1", "test.event", "2023-01-01T12:00:00", "{}"))

        with store2 as conn:
            conn.cursor().execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("w2", "e2", "test.event", "2023-01-01T12:00:00", "{}"))

        with store1 as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT workflow_id FROM events")
            assert [row[0] for row in cursor.fetchall()] == ["w1"]

        with store2 as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT workflow_id FROM events")
            assert [row[0] for row in cursor.fetchall()] == ["w2"]

    def test_string_and_path_initialization_share_database(self, tmp_path):
        """Test that string and Path init connect to same database."""
        db_path = tmp_path / "test.db"
        store_path = EventStore(db_path)
        store_str = EventStore(str(db_path))

        with store_path as conn:
            conn.cursor().execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, ("shared", "e1", "test.event", "2023-01-01T12:00:00", "{}"))

        with store_str as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("shared",))
            assert cursor.fetchone()[0] == 1
