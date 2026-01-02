# ABOUTME: Test suite for SQLite database indexes on events table
# ABOUTME: Tests performance indexes on workflow_id, event_type, and timestamp columns

"""Test suite for SQLite database indexes.

Tests the database index creation functionality including:
- Indexes on events table for workflow_id, event_type, and timestamp columns
- Query performance optimization verification
- Proper index naming and structure
- Idempotent index creation (can be called multiple times safely)
"""

import sqlite3
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Import will fail until we implement the index creation - that's expected in TDD
try:
    from jean_claude.core.schema_creation import create_event_store_schema, create_event_store_indexes
except ImportError:
    # Allow tests to be written before implementation
    create_event_store_schema = None
    create_event_store_indexes = None


@pytest.mark.skipif(create_event_store_indexes is None, reason="index creation not implemented yet")
class TestEventStoreIndexCreation:
    """Test database index creation for event store."""

    def test_creates_workflow_id_index(self, tmp_path):
        """Test that create_event_store_indexes creates index on workflow_id column."""
        db_path = tmp_path / "test.db"

        # Create schema first
        create_event_store_schema(db_path)

        # Create indexes
        create_event_store_indexes(db_path)

        # Verify the index was created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check that workflow_id index exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_events_workflow_id'
        """)
        index_result = cursor.fetchone()
        assert index_result is not None, "workflow_id index was not created"

        # Verify index is on the correct table and column
        cursor.execute("PRAGMA index_info(idx_events_workflow_id)")
        index_info = cursor.fetchall()
        assert len(index_info) == 1
        assert index_info[0][2] == "workflow_id"  # column name is at index 2

        conn.close()

    def test_creates_event_type_index(self, tmp_path):
        """Test that create_event_store_indexes creates index on event_type column."""
        db_path = tmp_path / "test.db"

        # Create schema first
        create_event_store_schema(db_path)

        # Create indexes
        create_event_store_indexes(db_path)

        # Verify the index was created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check that event_type index exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_events_event_type'
        """)
        index_result = cursor.fetchone()
        assert index_result is not None, "event_type index was not created"

        # Verify index is on the correct table and column
        cursor.execute("PRAGMA index_info(idx_events_event_type)")
        index_info = cursor.fetchall()
        assert len(index_info) == 1
        assert index_info[0][2] == "event_type"  # column name is at index 2

        conn.close()

    def test_creates_timestamp_index(self, tmp_path):
        """Test that create_event_store_indexes creates index on timestamp column."""
        db_path = tmp_path / "test.db"

        # Create schema first
        create_event_store_schema(db_path)

        # Create indexes
        create_event_store_indexes(db_path)

        # Verify the index was created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check that timestamp index exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_events_timestamp'
        """)
        index_result = cursor.fetchone()
        assert index_result is not None, "timestamp index was not created"

        # Verify index is on the correct table and column
        cursor.execute("PRAGMA index_info(idx_events_timestamp)")
        index_info = cursor.fetchall()
        assert len(index_info) == 1
        assert index_info[0][2] == "timestamp"  # column name is at index 2

        conn.close()

    def test_creates_all_indexes_together(self, tmp_path):
        """Test that all three indexes are created when create_event_store_indexes is called."""
        db_path = tmp_path / "test.db"

        # Create schema first
        create_event_store_schema(db_path)

        # Create indexes
        create_event_store_indexes(db_path)

        # Verify all indexes were created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all indexes for the events table
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='events' AND name LIKE 'idx_events_%'
            ORDER BY name
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = ['idx_events_event_type', 'idx_events_timestamp', 'idx_events_workflow_id']
        assert indexes == expected_indexes, f"Expected {expected_indexes}, got {indexes}"

        conn.close()

    def test_index_creation_is_idempotent(self, tmp_path):
        """Test that index creation can be called multiple times safely."""
        db_path = tmp_path / "test.db"

        # Create schema first
        create_event_store_schema(db_path)

        # Create indexes the first time
        create_event_store_indexes(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert test data to verify it's preserved
        cursor.execute("""
            INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
        """, ("test-workflow", "event-123", "test.event", "2023-01-01T12:00:00", "{}"))

        conn.commit()

        # Count indexes before second call
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='index' AND tbl_name='events' AND name LIKE 'idx_events_%'
        """)
        initial_index_count = cursor.fetchone()[0]

        conn.close()

        # Create indexes again - should not fail or create duplicates
        create_event_store_indexes(db_path)

        # Verify index count is the same and data is preserved
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='index' AND tbl_name='events' AND name LIKE 'idx_events_%'
        """)
        final_index_count = cursor.fetchone()[0]
        assert final_index_count == initial_index_count, "Indexes were duplicated"

        cursor.execute("SELECT COUNT(*) FROM events")
        events_count = cursor.fetchone()[0]
        assert events_count == 1, "Data was lost during index re-creation"

        conn.close()

    def test_accepts_path_object_and_string(self, tmp_path):
        """Test that index creation accepts both Path objects and strings."""
        # Test with Path object
        db_path_obj = tmp_path / "path_obj.db"
        create_event_store_schema(db_path_obj)
        create_event_store_indexes(db_path_obj)

        # Verify index was created
        conn = sqlite3.connect(db_path_obj)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='index' AND name='idx_events_workflow_id'
        """)
        assert cursor.fetchone()[0] == 1
        conn.close()

        # Test with string path
        db_path_str = str(tmp_path / "path_str.db")
        create_event_store_schema(db_path_str)
        create_event_store_indexes(db_path_str)

        # Verify index was created
        conn = sqlite3.connect(db_path_str)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='index' AND name='idx_events_workflow_id'
        """)
        assert cursor.fetchone()[0] == 1
        conn.close()

    def test_handles_invalid_path_gracefully(self, tmp_path):
        """Test that index creation handles invalid paths with clear error messages."""
        # Use mocking since filesystem behavior varies by environment (esp. running as root)
        invalid_path = tmp_path / "invalid" / "path" / "database.db"

        # Mock sqlite3.connect to raise an error
        with patch('sqlite3.connect', side_effect=sqlite3.OperationalError("unable to open database file")):
            with pytest.raises((OSError, sqlite3.Error)) as excinfo:
                create_event_store_indexes(invalid_path)

            # Should get a meaningful error about the path or database
            error_msg = str(excinfo.value).lower()
            assert any(keyword in error_msg for keyword in ["database", "path", "unable", "open"])

    def test_handles_database_without_schema_gracefully(self, tmp_path):
        """Test that index creation handles database without proper schema."""
        db_path = tmp_path / "empty.db"

        # Create empty database file without schema
        conn = sqlite3.connect(db_path)
        conn.close()

        # Should handle missing events table gracefully
        with pytest.raises(sqlite3.Error) as excinfo:
            create_event_store_indexes(db_path)

        error_msg = str(excinfo.value).lower()
        assert "events" in error_msg or "table" in error_msg


@pytest.mark.skipif(create_event_store_indexes is None, reason="index creation not implemented yet")
class TestIndexPerformanceOptimization:
    """Test that indexes actually improve query performance."""

    def setup_test_data(self, db_path, num_records=1000):
        """Helper method to set up test data for performance tests."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert test data
        for i in range(num_records):
            workflow_id = f"workflow-{i % 10}"  # 10 different workflows
            event_type = f"event.type.{i % 5}"  # 5 different event types
            timestamp = f"2023-01-{(i % 30) + 1:02d}T12:00:00"  # 30 different timestamps
            cursor.execute("""
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, (workflow_id, f"event-{i}", event_type, timestamp, "{}"))

        conn.commit()
        conn.close()

    def test_workflow_id_index_improves_query_performance(self, tmp_path):
        """Test that workflow_id index improves query performance."""
        db_path = tmp_path / "perf_test.db"

        # Create schema and populate with test data
        create_event_store_schema(db_path)
        self.setup_test_data(db_path, 1000)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Measure query time without index
        start_time = time.time()
        cursor.execute("SELECT * FROM events WHERE workflow_id = 'workflow-5'")
        results_without_index = cursor.fetchall()
        time_without_index = time.time() - start_time

        # Create indexes
        conn.close()
        create_event_store_indexes(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Measure query time with index
        start_time = time.time()
        cursor.execute("SELECT * FROM events WHERE workflow_id = 'workflow-5'")
        results_with_index = cursor.fetchall()
        time_with_index = time.time() - start_time

        # Verify results are the same
        assert len(results_without_index) == len(results_with_index)
        assert len(results_with_index) > 0  # Should find some records

        # Verify the query plan uses the index
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM events WHERE workflow_id = 'workflow-5'")
        query_plan = cursor.fetchall()
        plan_text = " ".join([str(row) for row in query_plan]).lower()
        assert "idx_events_workflow_id" in plan_text, "Query plan should use the workflow_id index"

        conn.close()

    def test_event_type_index_improves_query_performance(self, tmp_path):
        """Test that event_type index improves query performance."""
        db_path = tmp_path / "perf_test.db"

        # Create schema, add indexes, and populate with test data
        create_event_store_schema(db_path)
        create_event_store_indexes(db_path)
        self.setup_test_data(db_path, 1000)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Test event_type query uses index
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM events WHERE event_type = 'event.type.2'")
        query_plan = cursor.fetchall()
        plan_text = " ".join([str(row) for row in query_plan]).lower()
        assert "idx_events_event_type" in plan_text, "Query plan should use the event_type index"

        # Verify query returns correct results
        cursor.execute("SELECT * FROM events WHERE event_type = 'event.type.2'")
        results = cursor.fetchall()
        assert len(results) > 0  # Should find some records

        conn.close()

    def test_timestamp_index_improves_range_queries(self, tmp_path):
        """Test that timestamp index improves range query performance."""
        db_path = tmp_path / "perf_test.db"

        # Create schema, add indexes, and populate with test data
        create_event_store_schema(db_path)
        create_event_store_indexes(db_path)
        self.setup_test_data(db_path, 1000)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Test timestamp range query uses index
        cursor.execute("""
            EXPLAIN QUERY PLAN
            SELECT * FROM events
            WHERE timestamp BETWEEN '2023-01-10T12:00:00' AND '2023-01-20T12:00:00'
        """)
        query_plan = cursor.fetchall()
        plan_text = " ".join([str(row) for row in query_plan]).lower()
        assert "idx_events_timestamp" in plan_text, "Query plan should use the timestamp index"

        # Verify query returns correct results
        cursor.execute("""
            SELECT * FROM events
            WHERE timestamp BETWEEN '2023-01-10T12:00:00' AND '2023-01-20T12:00:00'
        """)
        results = cursor.fetchall()
        assert len(results) > 0  # Should find some records

        conn.close()

    def test_combined_query_optimization(self, tmp_path):
        """Test that multiple indexes can work together for complex queries."""
        db_path = tmp_path / "perf_test.db"

        # Create schema, add indexes, and populate with test data
        create_event_store_schema(db_path)
        create_event_store_indexes(db_path)
        self.setup_test_data(db_path, 1000)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Test query that could use multiple indexes
        # Use workflow-1 and event.type.1 (both i%10==1 and i%5==1 match at i=1,11,21,31...)
        cursor.execute("""
            SELECT * FROM events
            WHERE workflow_id = 'workflow-1' AND event_type = 'event.type.1'
            ORDER BY timestamp
        """)
        results = cursor.fetchall()
        assert len(results) > 0  # Should find some records

        # Verify results are ordered by timestamp
        timestamps = [result[4] for result in results]  # timestamp is at index 4
        assert timestamps == sorted(timestamps), "Results should be ordered by timestamp"

        conn.close()