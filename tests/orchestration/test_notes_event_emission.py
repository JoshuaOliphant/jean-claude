# ABOUTME: Simplified integration tests for note event emission and retrieval
# ABOUTME: Tests EventLogger → SQLite → Query flow without full workflow mocking

"""Integration tests for notes event emission and retrieval.

This test module validates the core contract: note events emitted via EventLogger
are properly stored in .jc/events.db and can be queried back with correct data.

Test Coverage:
- Verification note emission (observation/warning)
- Feature success note emission (accomplishment)
- Feature failure note emission (warning)
- Test result note emission (observation)
- Commit success note emission (accomplishment)
- SQL query retrieval of all note types
"""

import sqlite3
import json
from pathlib import Path

import pytest

from jean_claude.core.events import EventLogger


class TestNoteEventEmission:
    """Test direct note event emission via EventLogger."""

    def test_verification_observation_emitted_and_queryable(self, tmp_path):
        """Verification observation note is stored and retrievable from events.db."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)

        # Emit verification observation note
        event_logger.emit(
            workflow_id=workflow_id,
            event_type="agent.note.observation",
            data={
                "agent_id": "verification-agent",
                "title": "Verification passed",
                "content": "10 test files, 1500ms",
                "tags": ["verification", "tests"],
                "category": "observation",
            }
        )

        # Query events from SQLite
        events_db = tmp_path / ".jc" / "events.db"
        assert events_db.exists(), "Events database should exist"

        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_type, data
            FROM events
            WHERE workflow_id = ? AND event_type = 'agent.note.observation'
        """, (workflow_id,))
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1, "Should have one observation note"
        event_type, data_json = rows[0]
        data = json.loads(data_json)

        assert event_type == "agent.note.observation"
        assert data["agent_id"] == "verification-agent"
        assert data["title"] == "Verification passed"
        assert "10 test files" in data["content"]
        assert "verification" in data["tags"]
        assert data["category"] == "observation"

    def test_verification_warning_emitted_and_queryable(self, tmp_path):
        """Verification warning note is stored and retrievable."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)

        # Emit verification warning note
        event_logger.emit(
            workflow_id=workflow_id,
            event_type="agent.note.warning",
            data={
                "agent_id": "verification-agent",
                "title": "Verification failed",
                "content": "10 test files, 1500ms",
                "tags": ["verification", "tests"],
                "category": "warning",
            }
        )

        # Query events
        events_db = tmp_path / ".jc" / "events.db"
        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_type, data
            FROM events
            WHERE workflow_id = ? AND event_type = 'agent.note.warning'
        """, (workflow_id,))
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1, "Should have one warning note"
        data = json.loads(rows[0][1])
        assert data["agent_id"] == "verification-agent"
        assert "failed" in data["title"].lower()

    def test_feature_success_accomplishment_emitted(self, tmp_path):
        """Feature success accomplishment note is stored correctly."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)

        # Emit feature success note
        event_logger.emit(
            workflow_id=workflow_id,
            event_type="agent.note.accomplishment",
            data={
                "agent_id": "coder-agent",
                "title": "Completed: Login Feature",
                "content": "Implement user login functionality",
                "tags": ["feature-complete", "login-feature"],
                "category": "accomplishment",
                "related_feature": "Login Feature",
            }
        )

        # Query events
        events_db = tmp_path / ".jc" / "events.db"
        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_type, data
            FROM events
            WHERE workflow_id = ? AND event_type = 'agent.note.accomplishment'
        """, (workflow_id,))
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1, "Should have one accomplishment note"
        data = json.loads(rows[0][1])
        assert data["agent_id"] == "coder-agent"
        assert "Completed" in data["title"]
        assert "Login Feature" in data["title"]
        assert data["related_feature"] == "Login Feature"

    def test_feature_failure_warning_emitted(self, tmp_path):
        """Feature failure warning note is stored correctly."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)

        # Emit feature failure note
        event_logger.emit(
            workflow_id=workflow_id,
            event_type="agent.note.warning",
            data={
                "agent_id": "coder-agent",
                "title": "Failed: Broken Feature",
                "content": "Implementation failed due to missing dependencies",
                "tags": ["feature-failed", "error"],
                "category": "warning",
                "related_feature": "Broken Feature",
            }
        )

        # Query events
        events_db = tmp_path / ".jc" / "events.db"
        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT data
            FROM events
            WHERE workflow_id = ? AND event_type = 'agent.note.warning'
        """, (workflow_id,))
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1
        data = json.loads(rows[0][0])
        assert "Failed" in data["title"]
        assert "missing dependencies" in data["content"]
        assert "feature-failed" in data["tags"]

    def test_test_result_observation_emitted(self, tmp_path):
        """Test result observation note is stored correctly."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)

        # Emit test result note
        event_logger.emit(
            workflow_id=workflow_id,
            event_type="agent.note.observation",
            data={
                "agent_id": "commit-orchestrator",
                "title": "Tests passed before commit",
                "content": "15 tests passed",
                "tags": ["tests", "commit"],
                "category": "observation",
            }
        )

        # Query events
        events_db = tmp_path / ".jc" / "events.db"
        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT data
            FROM events
            WHERE workflow_id = ? AND event_type = 'agent.note.observation'
        """, (workflow_id,))
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1
        data = json.loads(rows[0][0])
        assert data["agent_id"] == "commit-orchestrator"
        assert "Tests passed" in data["title"]
        assert "15 tests" in data["content"]

    def test_commit_success_accomplishment_emitted(self, tmp_path):
        """Commit success accomplishment note is stored correctly."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)

        # Emit commit success note
        event_logger.emit(
            workflow_id=workflow_id,
            event_type="agent.note.accomplishment",
            data={
                "agent_id": "commit-orchestrator",
                "title": "Commit created",
                "content": "SHA: abc123def456",
                "tags": ["commit", "git"],
                "category": "accomplishment",
                "related_feature": "API Endpoint",
            }
        )

        # Query events
        events_db = tmp_path / ".jc" / "events.db"
        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT data
            FROM events
            WHERE workflow_id = ? AND event_type = 'agent.note.accomplishment'
            AND json_extract(data, '$.agent_id') = 'commit-orchestrator'
        """, (workflow_id,))
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1
        data = json.loads(rows[0][0])
        assert data["title"] == "Commit created"
        assert "SHA: abc123def456" in data["content"]
        assert "commit" in data["tags"]

    def test_multiple_notes_queryable_by_category(self, tmp_path):
        """Multiple notes can be filtered by category via SQL."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)

        # Emit multiple notes
        event_logger.emit(
            workflow_id=workflow_id,
            event_type="agent.note.observation",
            data={
                "agent_id": "agent-1",
                "title": "Observation 1",
                "content": "Content 1",
                "tags": [],
                "category": "observation",
            }
        )

        event_logger.emit(
            workflow_id=workflow_id,
            event_type="agent.note.warning",
            data={
                "agent_id": "agent-2",
                "title": "Warning 1",
                "content": "Content 2",
                "tags": [],
                "category": "warning",
            }
        )

        event_logger.emit(
            workflow_id=workflow_id,
            event_type="agent.note.accomplishment",
            data={
                "agent_id": "agent-3",
                "title": "Accomplishment 1",
                "content": "Content 3",
                "tags": [],
                "category": "accomplishment",
            }
        )

        # Query by category
        events_db = tmp_path / ".jc" / "events.db"
        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()

        # Query warnings only
        cursor.execute("""
            SELECT event_type, data
            FROM events
            WHERE workflow_id = ? AND event_type = 'agent.note.warning'
        """, (workflow_id,))
        warnings = cursor.fetchall()

        # Query all notes
        cursor.execute("""
            SELECT event_type, data
            FROM events
            WHERE workflow_id = ? AND event_type LIKE 'agent.note.%'
        """, (workflow_id,))
        all_notes = cursor.fetchall()

        conn.close()

        assert len(warnings) == 1, "Should have 1 warning"
        assert len(all_notes) == 3, "Should have 3 total notes"

        # Verify data integrity
        warning_data = json.loads(warnings[0][1])
        assert warning_data["title"] == "Warning 1"
        assert warning_data["category"] == "warning"
