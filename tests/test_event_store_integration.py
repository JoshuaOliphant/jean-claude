# ABOUTME: Integration tests for EventStore end-to-end functionality
# ABOUTME: Tests automatic initialization, database creation, and component integration

"""Integration tests for EventStore end-to-end functionality.

Tests the complete EventStore integration including:
- Automatic schema initialization on instantiation
- Database and table creation at specified path
- End-to-end connection management and queries
- Integration of all EventStore components
"""

import sqlite3
from pathlib import Path

import pytest

from jean_claude.core.event_store import EventStore


class TestEventStoreIntegration:
    """Test EventStore end-to-end integration."""

    def test_eventstore_automatically_initializes_schema_on_creation(self, tmp_path):
        """Test that EventStore automatically creates database and schema on __init__."""
        db_path = tmp_path / "auto_init_events.db"

        # Database shouldn't exist yet
        assert not db_path.exists()

        # Create EventStore - should auto-initialize schema
        store = EventStore(db_path)

        # Database file should now exist
        assert db_path.exists()
        assert db_path.is_file()

        # Tables should be created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verify events table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='events'
        """)
        assert cursor.fetchone() is not None

        # Verify snapshots table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='snapshots'
        """)
        assert cursor.fetchone() is not None

        conn.close()

    def test_eventstore_integration_with_string_path(self, tmp_path):
        """Test that EventStore works end-to-end when initialized with string path."""
        db_path_str = str(tmp_path / "string_path_events.db")

        # Create EventStore with string path
        store = EventStore(db_path_str)

        # Should automatically convert to Path and initialize
        assert isinstance(store.db_path, Path)
        assert store.db_path.exists()

    def test_eventstore_connection_works_after_auto_initialization(self, tmp_path):
        """Test that connection management works after automatic initialization."""
        db_path = tmp_path / "connection_test.db"

        # Create EventStore - auto-initializes
        store = EventStore(db_path)

        # Should be able to get a working connection
        conn = store.get_connection()
        assert conn is not None

        # Should be able to query tables
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        count = cursor.fetchone()[0]
        assert count == 0  # Empty table

        # Should be able to close connection
        store.close_connection(conn)

    def test_eventstore_context_manager_works_after_auto_initialization(self, tmp_path):
        """Test that context manager works after automatic initialization."""
        db_path = tmp_path / "context_test.db"

        # Create EventStore - auto-initializes
        store = EventStore(db_path)

        # Context manager should work
        with store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM snapshots")
            count = cursor.fetchone()[0]
            assert count == 0

    def test_eventstore_indexes_created_automatically(self, tmp_path):
        """Test that indexes are created automatically on initialization."""
        db_path = tmp_path / "indexes_test.db"

        # Create EventStore - should auto-initialize with indexes
        store = EventStore(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check for expected indexes
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

    def test_eventstore_can_be_created_multiple_times_with_same_path(self, tmp_path):
        """Test that EventStore can be instantiated multiple times with same path (idempotent)."""
        db_path = tmp_path / "idempotent_test.db"

        # Create first instance
        store1 = EventStore(db_path)
        assert db_path.exists()

        # Add some data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
        """, ("workflow-1", "event-123", "test.event", "2023-01-01T12:00:00", "{}"))
        conn.commit()
        conn.close()

        # Create second instance with same path - should not destroy data
        store2 = EventStore(db_path)

        # Verify data still exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        count = cursor.fetchone()[0]
        assert count == 1
        conn.close()

    def test_eventstore_creates_parent_directories_automatically(self, tmp_path):
        """Test that EventStore creates parent directories if they don't exist."""
        nested_path = tmp_path / "data" / "events" / "store.db"

        # Parent directories shouldn't exist
        assert not nested_path.parent.exists()

        # Create EventStore - should create parent directories
        store = EventStore(nested_path)

        # Database and parent directories should exist
        assert nested_path.exists()
        assert nested_path.parent.exists()
