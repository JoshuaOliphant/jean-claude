# ABOUTME: Unit tests for agent note-taking context integration
# ABOUTME: Tests _build_notes_context() helper function with event store queries

"""Unit tests for notes context in auto_continue prompts.

This test module validates the _build_notes_context() helper function
that queries notes from the event store and formats them for agent prompts.

Test Coverage:
- Empty context when events.db doesn't exist
- Empty context when no note events exist
- Formatted context with sample notes
- Limit to 15 most relevant notes
- Priority-based filtering (warnings > decisions > learnings > observations)
"""

import sqlite3
import json
from pathlib import Path

import pytest

from jean_claude.core.state import Feature
from jean_claude.orchestration.auto_continue import _build_notes_context


class TestBuildNotesContext:
    """Test notes context building for agent prompts."""

    def test_no_events_db(self, tmp_path):
        """Return empty context when events.db doesn't exist."""
        workflow_id = "test-workflow"
        feature = Feature(name="Test Feature", description="Test description")

        context = _build_notes_context(workflow_id, tmp_path, feature)

        assert context == ""

    def test_no_notes_in_events(self, tmp_path):
        """Return empty context when no note events exist."""
        workflow_id = "test-workflow"
        feature = Feature(name="Test Feature", description="Test description")

        # Create empty events.db
        events_db = tmp_path / ".jc" / "events.db"
        events_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(events_db)
        conn.execute("""
            CREATE TABLE events (
                workflow_id TEXT,
                event_type TEXT,
                data TEXT,
                timestamp TEXT
            )
        """)
        conn.close()

        context = _build_notes_context(workflow_id, tmp_path, feature)

        assert context == ""

    def test_formats_notes_from_events(self, tmp_path):
        """Format notes from event store with emojis and structure."""
        workflow_id = "test-workflow"
        feature = Feature(name="Test Feature", description="Test description")

        # Create events.db with sample note events
        events_db = tmp_path / ".jc" / "events.db"
        events_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(events_db)
        conn.execute("""
            CREATE TABLE events (
                workflow_id TEXT,
                event_type TEXT,
                data TEXT,
                timestamp TEXT
            )
        """)

        # Insert test note events
        test_notes = [
            {"agent_id": "agent-1", "title": "Warning found", "content": "Test warning content", "category": "warning"},
            {"agent_id": "agent-2", "title": "Decision made", "content": "Test decision content", "category": "decision"},
            {"agent_id": "agent-3", "title": "Learning captured", "content": "Test learning content", "category": "learning"},
        ]

        for note in test_notes:
            conn.execute(
                "INSERT INTO events (workflow_id, event_type, data, timestamp) VALUES (?, ?, ?, ?)",
                ("test-workflow", f"agent.note.{note['category']}", json.dumps(note), "2024-01-01T00:00:00Z")
            )
        conn.commit()
        conn.close()

        context = _build_notes_context(workflow_id, tmp_path, feature)

        # Verify structure
        assert "PREVIOUS NOTES FROM OTHER AGENTS" in context
        assert "Review these notes from agents who worked on earlier features:" in context
        assert "Use these insights to inform your implementation." in context

        # Verify emojis and categories
        assert "⚠️ WARNING" in context
        assert "🎯 DECISION" in context
        assert "💡 LEARNING" in context

        # Verify note titles
        assert "Warning found" in context
        assert "Decision made" in context
        assert "Learning captured" in context

        # Verify size constraint (should be reasonable length)
        assert len(context.split("\n")) < 50  # Limit size

    def test_limits_to_15_notes(self, tmp_path):
        """Limit context to 15 most relevant notes."""
        workflow_id = "test-workflow"
        feature = Feature(name="Test Feature", description="Test description")

        # Create events.db with 50 note events
        events_db = tmp_path / ".jc" / "events.db"
        events_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(events_db)
        conn.execute("""
            CREATE TABLE events (
                workflow_id TEXT,
                event_type TEXT,
                data TEXT,
                timestamp TEXT
            )
        """)

        # Insert 50 test notes across categories
        for i in range(50):
            category = ["warning", "decision", "learning", "observation"][i % 4]
            note = {
                "agent_id": f"agent-{i}",
                "title": f"Note {i}",
                "content": f"Content {i}",
                "category": category
            }
            conn.execute(
                "INSERT INTO events (workflow_id, event_type, data, timestamp) VALUES (?, ?, ?, ?)",
                ("test-workflow", f"agent.note.{category}", json.dumps(note), f"2024-01-01T00:{i:02d}:00Z")
            )
        conn.commit()
        conn.close()

        context = _build_notes_context(workflow_id, tmp_path, feature)

        # Count note entries by counting emoji lines (each note has one emoji line)
        note_count = sum(1 for line in context.split("\n") if any(emoji in line for emoji in ["⚠️", "🎯", "💡", "👁️", "✅", "📝"]))
        assert note_count <= 15, f"Expected <= 15 notes, got {note_count}"

    def test_truncates_long_content(self, tmp_path):
        """Truncate note content to 200 characters."""
        workflow_id = "test-workflow"
        feature = Feature(name="Test Feature", description="Test description")

        # Create events.db with long content note
        events_db = tmp_path / ".jc" / "events.db"
        events_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(events_db)
        conn.execute("""
            CREATE TABLE events (
                workflow_id TEXT,
                event_type TEXT,
                data TEXT,
                timestamp TEXT
            )
        """)

        # Insert note with very long content (500 chars)
        long_content = "a" * 500
        note = {
            "agent_id": "agent-1",
            "title": "Long note",
            "content": long_content,
            "category": "observation"
        }
        conn.execute(
            "INSERT INTO events (workflow_id, event_type, data, timestamp) VALUES (?, ?, ?, ?)",
            ("test-workflow", "agent.note.observation", json.dumps(note), "2024-01-01T00:00:00Z")
        )
        conn.commit()
        conn.close()

        context = _build_notes_context(workflow_id, tmp_path, feature)

        # Verify content is truncated
        assert "..." in context
        # Extract the content line (should be ~200 chars + "...")
        content_lines = [line for line in context.split("\n") if "aaa" in line]
        assert len(content_lines) > 0
        # Content should be truncated to ~203 chars (200 + "...")
        assert len(content_lines[0]) < 250

    def test_includes_related_file_if_present(self, tmp_path):
        """Include related file path with emoji if present."""
        workflow_id = "test-workflow"
        feature = Feature(name="Test Feature", description="Test description")

        # Create events.db with related_file note
        events_db = tmp_path / ".jc" / "events.db"
        events_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(events_db)
        conn.execute("""
            CREATE TABLE events (
                workflow_id TEXT,
                event_type TEXT,
                data TEXT,
                timestamp TEXT
            )
        """)

        note = {
            "agent_id": "agent-1",
            "title": "File-related note",
            "content": "About this file",
            "category": "observation",
            "related_file": "src/jean_claude/core/state.py"
        }
        conn.execute(
            "INSERT INTO events (workflow_id, event_type, data, timestamp) VALUES (?, ?, ?, ?)",
            ("test-workflow", "agent.note.observation", json.dumps(note), "2024-01-01T00:00:00Z")
        )
        conn.commit()
        conn.close()

        context = _build_notes_context(workflow_id, tmp_path, feature)

        # Verify related file is shown
        assert "📄 src/jean_claude/core/state.py" in context
