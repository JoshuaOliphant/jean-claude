# ABOUTME: Integration tests for complete notes write→event→projection flow
# ABOUTME: Tests end-to-end functionality including event emission and backward compatibility

"""Integration tests for notes write→event flow.

This test module validates the integration of the agent note-taking system,
ensuring that notes written via the API trigger events that are properly
stored in the event store (when event_logger is provided).

Test Coverage:
- Note writing with event emission
- All 10 note categories with events
- Event storage to SQLite
- Backward compatibility without event_logger
- Multiple notes and convenience methods
"""

import pytest
import sqlite3
import json
from pathlib import Path
from jean_claude.core.notes_api import Notes
from jean_claude.core.notes import NoteCategory
from jean_claude.core.events import EventLogger, EventType


class TestNotesFullIntegration:
    """Test complete write→event flow."""

    def test_notes_full_flow_integration(self, tmp_path):
        """Test: Note written via API → Event emitted → Stored in database."""
        workflow_id = "test-workflow"
        agent_id = "test-agent"
        project_root = tmp_path

        # Create agents directory for notes storage
        agents_dir = project_root / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Initialize event logger and notes API
        event_logger = EventLogger(project_root)
        notes = Notes(workflow_id=workflow_id, base_dir=agents_dir)

        # Write note (triggers JSONL + event)
        note = notes.add(
            agent_id=agent_id,
            title="Test Observation",
            content="Test content for integration",
            category=NoteCategory.OBSERVATION,
            tags=["integration-test", "full-flow"],
            related_file="test.py",
            related_feature="test-feature",
            event_logger=event_logger,
        )

        # Verify event was emitted to SQLite
        events_db = project_root / ".jc" / "events.db"
        assert events_db.exists(), "Events database should be created"

        # Verify event data in database
        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT event_type, workflow_id, data FROM events WHERE workflow_id = ?",
            (workflow_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1, "Should have one event in database"
        event_type, db_workflow_id, data_json = rows[0]

        assert event_type == "agent.note.observation"
        assert db_workflow_id == workflow_id

        # Verify event data contains all note information
        data = json.loads(data_json)
        assert data["agent_id"] == agent_id
        assert data["title"] == "Test Observation"
        assert data["content"] == "Test content for integration"
        assert data["tags"] == ["integration-test", "full-flow"]
        assert data["related_file"] == "test.py"
        assert data["related_feature"] == "test-feature"

    @pytest.mark.parametrize(
        "category",
        [
            NoteCategory.OBSERVATION,
            NoteCategory.QUESTION,
            NoteCategory.IDEA,
            NoteCategory.DECISION,
            NoteCategory.LEARNING,
            NoteCategory.REFLECTION,
            NoteCategory.WARNING,
            NoteCategory.ACCOMPLISHMENT,
            NoteCategory.CONTEXT,
            NoteCategory.TODO,
        ],
    )
    def test_all_note_categories_integration(self, tmp_path, category):
        """Test: All 10 note categories emit events correctly."""
        workflow_id = "test-workflow"
        project_root = tmp_path

        # Create agents directory
        agents_dir = project_root / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Initialize
        event_logger = EventLogger(project_root)
        notes = Notes(workflow_id=workflow_id, base_dir=agents_dir)

        # Write note
        notes.add(
            agent_id="test-agent",
            title=f"Test {category.value}",
            content=f"Test content for {category.value}",
            category=category,
            event_logger=event_logger,
        )

        # Verify event in database
        events_db = project_root / ".jc" / "events.db"
        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT event_type, data FROM events WHERE workflow_id = ?",
            (workflow_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1
        event_type, data_json = rows[0]
        assert event_type == f"agent.note.{category.value}"

        data = json.loads(data_json)
        assert data["title"] == f"Test {category.value}"

    def test_multiple_notes_emit_multiple_events(self, tmp_path):
        """Test: Multiple notes emit multiple events to database."""
        workflow_id = "test-workflow"
        project_root = tmp_path

        # Create agents directory
        agents_dir = project_root / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Initialize
        event_logger = EventLogger(project_root)
        notes = Notes(workflow_id=workflow_id, base_dir=agents_dir)

        # Write multiple notes
        notes.add(
            agent_id="agent-1",
            title="First Note",
            content="Content 1",
            category=NoteCategory.OBSERVATION,
            tags=["tag1"],
            event_logger=event_logger,
        )

        notes.add(
            agent_id="agent-2",
            title="Second Note",
            content="Content 2",
            category=NoteCategory.LEARNING,
            tags=["tag2"],
            event_logger=event_logger,
        )

        notes.add(
            agent_id="agent-1",
            title="Third Note",
            content="Content 3",
            category=NoteCategory.DECISION,
            tags=["tag1", "tag3"],
            event_logger=event_logger,
        )

        # Verify all events in database
        events_db = project_root / ".jc" / "events.db"
        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT event_type, data FROM events WHERE workflow_id = ? ORDER BY timestamp",
            (workflow_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 3, "Should have 3 events in database"

        # Verify each event
        event1_type, event1_data_json = rows[0]
        assert event1_type == "agent.note.observation"
        event1_data = json.loads(event1_data_json)
        assert event1_data["title"] == "First Note"
        assert event1_data["agent_id"] == "agent-1"

        event2_type, event2_data_json = rows[1]
        assert event2_type == "agent.note.learning"
        event2_data = json.loads(event2_data_json)
        assert event2_data["title"] == "Second Note"
        assert event2_data["agent_id"] == "agent-2"

        event3_type, event3_data_json = rows[2]
        assert event3_type == "agent.note.decision"
        event3_data = json.loads(event3_data_json)
        assert event3_data["title"] == "Third Note"
        assert event3_data["agent_id"] == "agent-1"

    def test_notes_without_event_logger_backward_compat(self, tmp_path):
        """Test: Notes still work without event_logger (backward compatibility)."""
        workflow_id = "test-workflow"
        project_root = tmp_path

        # Create agents directory
        agents_dir = project_root / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Initialize notes WITHOUT event logger
        notes = Notes(workflow_id=workflow_id, base_dir=agents_dir)

        # Write note without event_logger
        note = notes.add(
            agent_id="test-agent",
            title="Test Note",
            content="Test content",
            category=NoteCategory.OBSERVATION,
        )

        # Verify note was created successfully
        assert note.agent_id == "test-agent"
        assert note.title == "Test Note"

        # Note: Without event_logger, the note is written to JSONL but no event
        # is emitted, so events.db won't exist
        events_db = project_root / ".jc" / "events.db"
        # Database may or may not exist (depending on test order), but if it does,
        # it should not have our workflow's events
        if events_db.exists():
            conn = sqlite3.connect(events_db)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM events WHERE workflow_id = ?",
                (workflow_id,)
            )
            count = cursor.fetchone()[0]
            conn.close()
            assert count == 0, "Should have no events for this workflow"

    def test_event_data_completeness(self, tmp_path):
        """Test: Events contain all required note data."""
        workflow_id = "test-workflow"
        project_root = tmp_path

        # Create agents directory
        agents_dir = project_root / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Initialize
        event_logger = EventLogger(project_root)
        notes = Notes(workflow_id=workflow_id, base_dir=agents_dir)

        # Write note with all fields
        notes.add(
            agent_id="test-agent",
            title="Complete Note",
            content="Full content here",
            category=NoteCategory.DECISION,
            tags=["tag1", "tag2"],
            related_file="path/to/file.py",
            related_feature="feature-name",
            event_logger=event_logger,
        )

        # Verify event data in database
        events_db = project_root / ".jc" / "events.db"
        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT data FROM events WHERE workflow_id = ?",
            (workflow_id,)
        )
        data_json = cursor.fetchone()[0]
        conn.close()

        # Verify all fields present in event data
        data = json.loads(data_json)
        assert data["agent_id"] == "test-agent"
        assert data["title"] == "Complete Note"
        assert data["content"] == "Full content here"
        assert data["tags"] == ["tag1", "tag2"]
        assert data["related_file"] == "path/to/file.py"
        assert data["related_feature"] == "feature-name"


class TestConvenienceMethodsIntegration:
    """Test that convenience methods work in integration scenarios."""

    def test_convenience_methods_emit_events(self, tmp_path):
        """Test: All convenience methods emit events correctly."""
        workflow_id = "test-workflow"
        project_root = tmp_path

        # Create agents directory
        agents_dir = project_root / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Initialize
        event_logger = EventLogger(project_root)
        notes = Notes(workflow_id=workflow_id, base_dir=agents_dir)

        # Use each convenience method
        notes.add_observation(
            agent_id="agent",
            title="Obs",
            content="Content",
            event_logger=event_logger,
        )
        notes.add_learning(
            agent_id="agent",
            title="Learn",
            content="Content",
            event_logger=event_logger,
        )
        notes.add_decision(
            agent_id="agent",
            title="Dec",
            content="Content",
            event_logger=event_logger,
        )
        notes.add_warning(
            agent_id="agent",
            title="Warn",
            content="Content",
            event_logger=event_logger,
        )
        notes.add_accomplishment(
            agent_id="agent",
            title="Acc",
            content="Content",
            event_logger=event_logger,
        )
        notes.add_todo(
            agent_id="agent",
            title="Todo",
            content="Content",
            event_logger=event_logger,
        )

        # Verify all 6 events in database
        events_db = project_root / ".jc" / "events.db"
        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT event_type FROM events WHERE workflow_id = ?",
            (workflow_id,)
        )
        event_types = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert len(event_types) == 6, "Should have 6 events in database"

        # Verify correct event types
        assert "agent.note.observation" in event_types
        assert "agent.note.learning" in event_types
        assert "agent.note.decision" in event_types
        assert "agent.note.warning" in event_types
        assert "agent.note.accomplishment" in event_types
        assert "agent.note.todo" in event_types
