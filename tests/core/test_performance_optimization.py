# ABOUTME: Test performance optimizations for EventStore including indexes,
# ABOUTME: batch operations, and query pagination

"""Test performance optimizations for EventStore.

This module tests:
- Database indexes on workflow_id and timestamp
- Batch event append operations
- Query pagination for large result sets
"""

import pytest
import sqlite3
from pathlib import Path
from jean_claude.core.event_store import EventStore
from jean_claude.core.event_models import Event


class TestDatabaseIndexes:
    """Test that proper database indexes are created."""

    def test_workflow_id_index_exists(self, tmp_path):
        """Test that workflow_id column has an index."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Query SQLite to check for indexes
        conn = event_store.get_connection()
        cursor = conn.cursor()

        # Get all indexes on the events table
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='events'
        """)
        indexes = [row["name"] for row in cursor.fetchall()]

        # Should have index on workflow_id
        workflow_id_indexes = [idx for idx in indexes if 'workflow_id' in idx.lower()]
        assert len(workflow_id_indexes) > 0, "No index found on workflow_id column"

        event_store.close_connection(conn)

    def test_timestamp_index_exists(self, tmp_path):
        """Test that timestamp column has an index."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        conn = event_store.get_connection()
        cursor = conn.cursor()

        # Get all indexes on the events table
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='events'
        """)
        indexes = [row["name"] for row in cursor.fetchall()]

        # Should have index on timestamp
        timestamp_indexes = [idx for idx in indexes if 'timestamp' in idx.lower()]
        assert len(timestamp_indexes) > 0, "No index found on timestamp column"

        event_store.close_connection(conn)

    def test_indexes_improve_query_performance(self, tmp_path):
        """Test that indexes improve query performance."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Add many events
        for i in range(100):
            event = Event(
                workflow_id=f"workflow-{i % 10}",
                event_type="test.event",
                event_data={"index": i}
            )
            event_store.append(event)

        conn = event_store.get_connection()
        cursor = conn.cursor()

        # Query should use index (EXPLAIN QUERY PLAN shows this)
        cursor.execute("""
            EXPLAIN QUERY PLAN
            SELECT * FROM events WHERE workflow_id = 'workflow-5'
        """)
        plan = cursor.fetchall()

        # Plan should mention using an index (not a full table scan)
        plan_str = " ".join([str(row) for row in plan])
        assert "SCAN" not in plan_str or "INDEX" in plan_str.upper()

        event_store.close_connection(conn)


class TestBatchOperations:
    """Test batch event append operations."""

    def test_append_batch_basic(self, tmp_path):
        """Test basic batch append operation."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create batch of events
        events = [
            Event(
                workflow_id=f"workflow-{i}",
                event_type="batch.event",
                event_data={"batch_index": i}
            )
            for i in range(10)
        ]

        # If append_batch method exists, use it
        if hasattr(event_store, 'append_batch'):
            result = event_store.append_batch(events)
            assert result is True

            # Verify all events were stored
            for i in range(10):
                stored_events = event_store.get_events(f"workflow-{i}")
                assert len(stored_events) == 1
                assert stored_events[0].event_data["batch_index"] == i
        else:
            pytest.skip("append_batch method not yet implemented")

    def test_append_batch_transaction_rollback(self, tmp_path):
        """Test that batch append rolls back on failure."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        if not hasattr(event_store, 'append_batch'):
            pytest.skip("append_batch method not yet implemented")

        events = [
            Event(
                workflow_id="workflow-1",
                event_type="batch.event",
                event_data={"index": 1}
            ),
            None,  # Invalid event should cause rollback
            Event(
                workflow_id="workflow-3",
                event_type="batch.event",
                event_data={"index": 3}
            )
        ]

        result = event_store.append_batch(events)
        assert result is False

        # No events should have been stored
        stored_events = event_store.get_events("workflow-1")
        assert len(stored_events) == 0

    def test_append_batch_performance_gain(self, tmp_path):
        """Test that batch operations are faster than individual appends."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        if not hasattr(event_store, 'append_batch'):
            pytest.skip("append_batch method not yet implemented")

        import time

        # Batch append
        events = [
            Event(
                workflow_id="batch-workflow",
                event_type="perf.test",
                event_data={"index": i}
            )
            for i in range(100)
        ]

        start = time.time()
        event_store.append_batch(events)
        batch_time = time.time() - start

        # Individual appends (in a new database for fair comparison)
        db_path2 = tmp_path / "test_events2.db"
        event_store2 = EventStore(db_path2)

        start = time.time()
        for i in range(100):
            event = Event(
                workflow_id="individual-workflow",
                event_type="perf.test",
                event_data={"index": i}
            )
            event_store2.append(event)
        individual_time = time.time() - start

        # Batch should be faster (allow some margin for variance)
        assert batch_time < individual_time, \
            f"Batch ({batch_time:.4f}s) should be faster than individual ({individual_time:.4f}s)"


class TestQueryPagination:
    """Test query pagination for large result sets."""

    def test_get_events_with_limit(self, tmp_path):
        """Test query with limit parameter."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Add 20 events
        for i in range(20):
            event = Event(
                workflow_id="pagination-workflow",
                event_type="page.event",
                event_data={"index": i}
            )
            event_store.append(event)

        # Check if get_events supports limit parameter
        import inspect
        sig = inspect.signature(event_store.get_events)
        if 'limit' in sig.parameters:
            # Get first 5 events
            events = event_store.get_events("pagination-workflow", limit=5)
            assert len(events) == 5

            # Get first 10 events
            events = event_store.get_events("pagination-workflow", limit=10)
            assert len(events) == 10
        else:
            pytest.skip("Pagination (limit parameter) not yet implemented")

    def test_get_events_with_offset(self, tmp_path):
        """Test query with offset parameter."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Add 20 events
        for i in range(20):
            event = Event(
                workflow_id="offset-workflow",
                event_type="offset.event",
                event_data={"index": i}
            )
            event_store.append(event)

        import inspect
        sig = inspect.signature(event_store.get_events)
        if 'offset' in sig.parameters:
            # Get events starting from index 10
            events = event_store.get_events("offset-workflow", offset=10)
            assert len(events) == 10

            # Get events from index 5 to 15
            if 'limit' in sig.parameters:
                events = event_store.get_events("offset-workflow", offset=5, limit=10)
                assert len(events) == 10
        else:
            pytest.skip("Pagination (offset parameter) not yet implemented")

    def test_pagination_handles_bounds(self, tmp_path):
        """Test that pagination handles edge cases correctly."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Add 10 events
        for i in range(10):
            event = Event(
                workflow_id="bounds-workflow",
                event_type="bounds.event",
                event_data={"index": i}
            )
            event_store.append(event)

        import inspect
        sig = inspect.signature(event_store.get_events)

        if 'limit' in sig.parameters and 'offset' in sig.parameters:
            # Offset beyond available events
            events = event_store.get_events("bounds-workflow", offset=20)
            assert len(events) == 0

            # Limit larger than available events
            events = event_store.get_events("bounds-workflow", limit=100)
            assert len(events) == 10

            # Offset + limit beyond available
            events = event_store.get_events("bounds-workflow", offset=5, limit=100)
            assert len(events) == 5
        else:
            pytest.skip("Pagination not yet fully implemented")
