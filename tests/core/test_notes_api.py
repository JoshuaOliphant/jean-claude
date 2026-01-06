# ABOUTME: Tests for Notes API class with SQLite event sourcing
# ABOUTME: Tests event emission and querying from SQLite event store

"""Tests for Notes API SQLite event sourcing.

This test module validates the Notes API's pure event sourcing functionality,
ensuring that all notes are written to and read from the SQLite event store.
"""

import pytest
from pathlib import Path

from jean_claude.core.notes_api import Notes
from jean_claude.core.notes import Note, NoteCategory
from jean_claude.core.events import EventLogger, EventType


class TestNotesSQLiteEventSourcing:
    """Test SQLite event sourcing for notes."""

    def test_add_note_writes_to_sqlite(self, tmp_path):
        """Verify note is written as event to SQLite."""
        # Setup
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=event_logger
        )

        # Execute
        note = notes.add(
            agent_id="test-agent",
            title="Test Observation",
            content="Test content",
            category=NoteCategory.OBSERVATION,
            tags=["test-tag"],
            related_file="test.py",
            related_feature="test-feature",
        )

        # Verify note was created
        assert note.agent_id == "test-agent"
        assert note.title == "Test Observation"
        assert note.category == NoteCategory.OBSERVATION

        # Verify event was written to SQLite
        import sqlite3
        import json

        events_db = tmp_path / ".jc" / "events.db"
        assert events_db.exists()

        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_type, data
            FROM events
            WHERE workflow_id = ? AND event_type = ?
        """, (workflow_id, "agent.note.observation"))

        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1
        event_type, data_json = rows[0]
        data = json.loads(data_json)

        assert data["agent_id"] == "test-agent"
        assert data["title"] == "Test Observation"
        assert data["content"] == "Test content"
        assert data["tags"] == ["test-tag"]
        assert data["related_file"] == "test.py"
        assert data["related_feature"] == "test-feature"

    def test_list_reads_from_sqlite(self, tmp_path):
        """Verify list() queries SQLite and returns Note objects."""
        # Setup
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=event_logger
        )

        # Add multiple notes
        notes.add(
            agent_id="agent-1",
            title="Learning 1",
            content="Content 1",
            category=NoteCategory.LEARNING,
        )
        notes.add(
            agent_id="agent-2",
            title="Decision 1",
            content="Content 2",
            category=NoteCategory.DECISION,
        )
        notes.add(
            agent_id="agent-1",
            title="Learning 2",
            content="Content 3",
            category=NoteCategory.LEARNING,
        )

        # Execute - list all
        all_notes = notes.list()

        # Verify
        assert len(all_notes) == 3
        assert all(isinstance(n, Note) for n in all_notes)

    def test_list_filters_by_category(self, tmp_path):
        """Verify list() filters by category."""
        # Setup
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=event_logger
        )

        # Add notes with different categories
        notes.add(
            agent_id="agent-1",
            title="Learning 1",
            content="Content 1",
            category=NoteCategory.LEARNING,
        )
        notes.add(
            agent_id="agent-2",
            title="Decision 1",
            content="Content 2",
            category=NoteCategory.DECISION,
        )
        notes.add(
            agent_id="agent-1",
            title="Learning 2",
            content="Content 3",
            category=NoteCategory.LEARNING,
        )

        # Execute - filter by category
        learning_notes = notes.list(category=NoteCategory.LEARNING)

        # Verify
        assert len(learning_notes) == 2
        assert all(n.category == NoteCategory.LEARNING for n in learning_notes)

    def test_list_filters_by_agent_id(self, tmp_path):
        """Verify list() filters by agent_id."""
        # Setup
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=event_logger
        )

        # Add notes from different agents
        notes.add(
            agent_id="agent-1",
            title="Note 1",
            content="Content 1",
            category=NoteCategory.OBSERVATION,
        )
        notes.add(
            agent_id="agent-2",
            title="Note 2",
            content="Content 2",
            category=NoteCategory.OBSERVATION,
        )
        notes.add(
            agent_id="agent-1",
            title="Note 3",
            content="Content 3",
            category=NoteCategory.OBSERVATION,
        )

        # Execute - filter by agent
        agent1_notes = notes.list(agent_id="agent-1")

        # Verify
        assert len(agent1_notes) == 2
        assert all(n.agent_id == "agent-1" for n in agent1_notes)

    def test_list_respects_limit(self, tmp_path):
        """Verify list() respects limit parameter."""
        # Setup
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=event_logger
        )

        # Add 5 notes
        for i in range(5):
            notes.add(
                agent_id="agent-1",
                title=f"Note {i}",
                content=f"Content {i}",
                category=NoteCategory.OBSERVATION,
            )

        # Execute - limit to 3
        limited_notes = notes.list(limit=3)

        # Verify
        assert len(limited_notes) == 3

    def test_search_finds_matching_notes(self, tmp_path):
        """Verify search() finds notes by text query."""
        # Setup
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=event_logger
        )

        # Add notes with searchable content
        notes.add(
            agent_id="agent-1",
            title="Authentication bug",
            content="Found issue with auth module",
            category=NoteCategory.WARNING,
        )
        notes.add(
            agent_id="agent-2",
            title="Database optimization",
            content="Optimized queries",
            category=NoteCategory.ACCOMPLISHMENT,
        )
        notes.add(
            agent_id="agent-3",
            title="Auth pattern",
            content="Use repository pattern for authentication",
            category=NoteCategory.LEARNING,
        )

        # Execute - search for "auth"
        results = notes.search("auth")

        # Verify - should match 2 notes (title and content)
        assert len(results) == 2
        assert any("auth" in n.title.lower() or "auth" in n.content.lower() for n in results)

    @pytest.mark.parametrize(
        "category,expected_event_type",
        [
            (NoteCategory.OBSERVATION, EventType.AGENT_NOTE_OBSERVATION),
            (NoteCategory.QUESTION, EventType.AGENT_NOTE_QUESTION),
            (NoteCategory.IDEA, EventType.AGENT_NOTE_IDEA),
            (NoteCategory.DECISION, EventType.AGENT_NOTE_DECISION),
            (NoteCategory.LEARNING, EventType.AGENT_NOTE_LEARNING),
            (NoteCategory.REFLECTION, EventType.AGENT_NOTE_REFLECTION),
            (NoteCategory.WARNING, EventType.AGENT_NOTE_WARNING),
            (NoteCategory.ACCOMPLISHMENT, EventType.AGENT_NOTE_ACCOMPLISHMENT),
            (NoteCategory.CONTEXT, EventType.AGENT_NOTE_CONTEXT),
            (NoteCategory.TODO, EventType.AGENT_NOTE_TODO),
        ],
    )
    def test_all_note_categories_emit_correct_event_types(
        self, tmp_path, category, expected_event_type
    ):
        """Verify each note category maps to the correct event type."""
        # Setup
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=event_logger
        )

        # Execute
        notes.add(
            agent_id="test-agent",
            title=f"Test {category.value}",
            content="Test content",
            category=category,
        )

        # Verify correct event type was written
        import sqlite3
        events_db = tmp_path / ".jc" / "events.db"
        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_type
            FROM events
            WHERE workflow_id = ?
        """, (workflow_id,))

        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1
        assert rows[0][0] == expected_event_type.value


class TestNotesConvenienceMethodsSQLite:
    """Test convenience methods with SQLite event sourcing."""

    def test_add_observation_writes_to_sqlite(self, tmp_path):
        """Verify add_observation() writes observation event."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=event_logger
        )

        note = notes.add_observation(
            agent_id="test-agent",
            title="Test Observation",
            content="Test content",
        )

        assert note.category == NoteCategory.OBSERVATION

        # Verify in SQLite
        import sqlite3
        events_db = tmp_path / ".jc" / "events.db"
        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_type FROM events WHERE workflow_id = ?
        """, (workflow_id,))
        rows = cursor.fetchall()
        conn.close()

        assert rows[0][0] == "agent.note.observation"

    def test_add_learning_writes_to_sqlite(self, tmp_path):
        """Verify add_learning() writes learning event."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=event_logger
        )

        note = notes.add_learning(
            agent_id="test-agent",
            title="Test Learning",
            content="Test content",
        )

        assert note.category == NoteCategory.LEARNING

    def test_add_decision_writes_to_sqlite(self, tmp_path):
        """Verify add_decision() writes decision event."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=event_logger
        )

        note = notes.add_decision(
            agent_id="test-agent",
            title="Test Decision",
            content="Test content",
        )

        assert note.category == NoteCategory.DECISION

    def test_add_warning_writes_to_sqlite(self, tmp_path):
        """Verify add_warning() writes warning event."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=event_logger
        )

        note = notes.add_warning(
            agent_id="test-agent",
            title="Test Warning",
            content="Test content",
        )

        assert note.category == NoteCategory.WARNING

    def test_add_accomplishment_writes_to_sqlite(self, tmp_path):
        """Verify add_accomplishment() writes accomplishment event."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=event_logger
        )

        note = notes.add_accomplishment(
            agent_id="test-agent",
            title="Test Accomplishment",
            content="Test content",
        )

        assert note.category == NoteCategory.ACCOMPLISHMENT

    def test_add_todo_writes_to_sqlite(self, tmp_path):
        """Verify add_todo() writes todo event."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=event_logger
        )

        note = notes.add_todo(
            agent_id="test-agent",
            title="Test TODO",
            content="Test content",
        )

        assert note.category == NoteCategory.TODO
