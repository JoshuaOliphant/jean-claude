# ABOUTME: Test suite for the agent note-taking system
# ABOUTME: Comprehensive tests for Note model, NotesPaths, writer, reader, and API

"""Tests for the agent note-taking system.

This module tests all components of the notes system including the Note model,
NotesPaths helper, note_writer, note_reader, and Notes API.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Callable

import pytest
from pydantic import ValidationError

from jean_claude.core.notes import Note, NoteCategory
from jean_claude.core.notes_paths import NotesPaths
from jean_claude.core.note_writer import write_note
from jean_claude.core.note_reader import read_notes, search_notes
from jean_claude.core.notes_api import Notes


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_note() -> Note:
    """Provide a standard Note for testing."""
    return Note(
        agent_id="test-agent",
        category=NoteCategory.OBSERVATION,
        title="Test Note Title",
        content="This is a test note content.",
        tags=["test", "sample"],
    )


@pytest.fixture
def note_factory() -> Callable[..., Note]:
    """Factory fixture for creating Note with custom values."""
    def _create_note(
        agent_id: str = "test-agent",
        category: NoteCategory = NoteCategory.OBSERVATION,
        title: str = "Test Note",
        content: str = "Test content",
        tags: list[str] | None = None,
        related_file: str | None = None,
        related_feature: str | None = None,
    ) -> Note:
        return Note(
            agent_id=agent_id,
            category=category,
            title=title,
            content=content,
            tags=tags or [],
            related_file=related_file,
            related_feature=related_feature,
        )
    return _create_note


# =============================================================================
# Note Model Tests
# =============================================================================


class TestNoteModel:
    """Tests for the Note Pydantic model."""

    def test_note_creation_with_all_fields(self, note_factory):
        """Test creating a note with all fields populated."""
        note = note_factory(
            agent_id="coder-agent",
            category=NoteCategory.LEARNING,
            title="Found a bug pattern",
            content="The codebase has a consistent pattern...",
            tags=["architecture", "patterns"],
            related_file="src/core/auth.py",
            related_feature="user-authentication",
        )

        assert note.agent_id == "coder-agent"
        assert note.category == NoteCategory.LEARNING
        assert note.title == "Found a bug pattern"
        assert note.content == "The codebase has a consistent pattern..."
        assert note.tags == ["architecture", "patterns"]
        assert note.related_file == "src/core/auth.py"
        assert note.related_feature == "user-authentication"
        assert note.id is not None
        assert isinstance(note.created_at, datetime)

    def test_note_category_values(self):
        """Test all note category enum values."""
        categories = [
            NoteCategory.OBSERVATION,
            NoteCategory.DECISION,
            NoteCategory.LEARNING,
            NoteCategory.WARNING,
            NoteCategory.ACCOMPLISHMENT,
            NoteCategory.CONTEXT,
            NoteCategory.TODO,
        ]
        for category in categories:
            note = Note(
                agent_id="test",
                title="Test",
                content="Content",
                category=category,
            )
            assert note.category == category

    def test_note_validation_rejects_empty_required_fields(self):
        """Test that empty required fields are rejected."""
        with pytest.raises(ValidationError):
            Note(agent_id="", title="Title", content="Content")

        with pytest.raises(ValidationError):
            Note(agent_id="agent", title="", content="Content")

        with pytest.raises(ValidationError):
            Note(agent_id="agent", title="Title", content="")

    def test_note_tags_validation_strips_whitespace(self):
        """Test that tags are cleaned properly."""
        note = Note(
            agent_id="test",
            title="Test",
            content="Content",
            tags=["  tag1  ", "", "tag2", "   "],
        )
        assert note.tags == ["tag1", "tag2"]

    def test_note_format_for_display(self, sample_note):
        """Test the format_for_display method."""
        display = sample_note.format_for_display()

        assert "[OBSERVATION]" in display
        assert sample_note.title in display
        assert sample_note.agent_id in display
        assert sample_note.content in display


# =============================================================================
# NotesPaths Tests
# =============================================================================


class TestNotesPaths:
    """Tests for the NotesPaths helper class."""

    def test_notes_paths_creation(self, tmp_path):
        """Test NotesPaths creation and path generation."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)

        assert paths.workflow_id == "test-workflow"
        assert paths.base_dir == tmp_path
        assert paths.notes_dir == tmp_path / "test-workflow" / "notes"
        assert paths.notes_path == tmp_path / "test-workflow" / "notes" / "notes.jsonl"

    def test_notes_paths_rejects_invalid_workflow_id(self, tmp_path):
        """Test that invalid workflow IDs are rejected."""
        with pytest.raises(ValueError):
            NotesPaths(workflow_id="", base_dir=tmp_path)

        with pytest.raises(ValueError):
            NotesPaths(workflow_id="   ", base_dir=tmp_path)

        with pytest.raises(TypeError):
            NotesPaths(workflow_id=None, base_dir=tmp_path)

    def test_notes_paths_ensure_notes_dir(self, tmp_path):
        """Test that ensure_notes_dir creates the directory."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)

        assert not paths.notes_dir.exists()
        paths.ensure_notes_dir()
        assert paths.notes_dir.exists()

        # Calling again should be idempotent
        paths.ensure_notes_dir()
        assert paths.notes_dir.exists()


# =============================================================================
# Note Writer Tests
# =============================================================================


class TestNoteWriter:
    """Tests for the write_note function."""

    def test_write_note_creates_directory_and_file(self, tmp_path, note_factory):
        """Test that write_note creates the notes directory and file."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)
        note = note_factory(title="First Note", content="First content")

        assert not paths.notes_dir.exists()
        write_note(note, paths)

        assert paths.notes_dir.exists()
        assert paths.notes_path.exists()

    def test_write_note_appends_to_file(self, tmp_path, note_factory):
        """Test that multiple notes are appended to the file."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)

        for i in range(3):
            note = note_factory(title=f"Note {i}", content=f"Content {i}")
            write_note(note, paths)

        lines = paths.notes_path.read_text().strip().split("\n")
        assert len(lines) == 3

        for i, line in enumerate(lines):
            parsed = json.loads(line)
            assert parsed["title"] == f"Note {i}"

    def test_write_note_jsonl_format(self, tmp_path, note_factory):
        """Test that notes are written in JSONL format."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)
        note = note_factory(
            agent_id="test-agent",
            category=NoteCategory.LEARNING,
            title="Test Title",
            content="Test content with\nnewlines",
            tags=["tag1", "tag2"],
            related_file="src/test.py",
        )
        write_note(note, paths)

        content = paths.notes_path.read_text().strip()
        parsed = json.loads(content)

        assert parsed["agent_id"] == "test-agent"
        assert parsed["category"] == "learning"
        assert parsed["title"] == "Test Title"
        assert "\n" in parsed["content"]
        assert parsed["tags"] == ["tag1", "tag2"]
        assert parsed["related_file"] == "src/test.py"

    def test_write_note_rejects_invalid_type(self, tmp_path):
        """Test that write_note rejects non-Note objects."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)

        with pytest.raises(TypeError):
            write_note("not a note", paths)

        with pytest.raises(TypeError):
            write_note({"title": "dict"}, paths)


# =============================================================================
# Note Reader Tests
# =============================================================================


class TestNoteReader:
    """Tests for the read_notes and search_notes functions."""

    def test_read_notes_returns_empty_for_missing_file(self, tmp_path):
        """Test that read_notes returns empty list for missing file."""
        paths = NotesPaths(workflow_id="nonexistent", base_dir=tmp_path)
        notes = read_notes(paths)
        assert notes == []

    def test_read_notes_parses_all_notes(self, tmp_path, note_factory):
        """Test that read_notes parses all notes from file."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Write multiple notes
        for i in range(5):
            note = note_factory(
                agent_id=f"agent-{i}",
                title=f"Note {i}",
                content=f"Content {i}",
            )
            write_note(note, paths)

        # Read all notes
        notes = read_notes(paths)
        assert len(notes) == 5
        for i, note in enumerate(notes):
            assert note.agent_id == f"agent-{i}"

    def test_read_notes_filter_by_agent_id(self, tmp_path, note_factory):
        """Test filtering notes by agent_id."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Write notes from different agents
        for agent in ["agent-a", "agent-b", "agent-a", "agent-c"]:
            write_note(note_factory(agent_id=agent), paths)

        # Filter by agent
        notes = read_notes(paths, agent_id="agent-a")
        assert len(notes) == 2
        for note in notes:
            assert note.agent_id == "agent-a"

    def test_read_notes_filter_by_category(self, tmp_path, note_factory):
        """Test filtering notes by category."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Write notes with different categories
        categories = [
            NoteCategory.LEARNING,
            NoteCategory.OBSERVATION,
            NoteCategory.LEARNING,
            NoteCategory.WARNING,
        ]
        for cat in categories:
            write_note(note_factory(category=cat), paths)

        # Filter by category
        notes = read_notes(paths, category=NoteCategory.LEARNING)
        assert len(notes) == 2
        for note in notes:
            assert note.category == NoteCategory.LEARNING

    def test_read_notes_filter_by_tag(self, tmp_path, note_factory):
        """Test filtering notes by tag."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)

        write_note(note_factory(tags=["bug", "urgent"]), paths)
        write_note(note_factory(tags=["feature"]), paths)
        write_note(note_factory(tags=["bug", "minor"]), paths)

        notes = read_notes(paths, tag="bug")
        assert len(notes) == 2

    def test_read_notes_with_limit(self, tmp_path, note_factory):
        """Test reading notes with a limit."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)

        for i in range(10):
            write_note(note_factory(title=f"Note {i}"), paths)

        notes = read_notes(paths, limit=3)
        assert len(notes) == 3
        # Should return the most recent (last 3)
        assert notes[0].title == "Note 7"
        assert notes[2].title == "Note 9"

    def test_search_notes_by_title(self, tmp_path, note_factory):
        """Test searching notes by title."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)

        write_note(note_factory(title="Authentication bug found"), paths)
        write_note(note_factory(title="Database optimization"), paths)
        write_note(note_factory(title="Auth flow explained"), paths)

        results = search_notes(paths, "auth")
        assert len(results) == 2

    def test_search_notes_by_content(self, tmp_path, note_factory):
        """Test searching notes by content."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)

        write_note(note_factory(
            title="Note 1",
            content="The memory leak is in the cache module"
        ), paths)
        write_note(note_factory(
            title="Note 2",
            content="Database connection pooling works well"
        ), paths)

        results = search_notes(paths, "memory")
        assert len(results) == 1
        assert "memory" in results[0].content.lower()

    def test_search_notes_case_insensitive(self, tmp_path, note_factory):
        """Test that search is case insensitive."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)

        write_note(note_factory(title="UPPERCASE TITLE"), paths)
        write_note(note_factory(title="lowercase title"), paths)

        results = search_notes(paths, "title")
        assert len(results) == 2

    def test_read_notes_handles_corrupted_lines(self, tmp_path, note_factory):
        """Test that read_notes skips corrupted JSON lines."""
        paths = NotesPaths(workflow_id="test-workflow", base_dir=tmp_path)

        # Write valid note
        write_note(note_factory(title="Valid Note"), paths)

        # Append corrupted line
        with open(paths.notes_path, "a") as f:
            f.write("{not valid json}\n")

        # Write another valid note
        write_note(note_factory(title="Another Valid"), paths)

        # Should get 2 valid notes, skipping corrupted line
        notes = read_notes(paths)
        assert len(notes) == 2


# =============================================================================
# Notes API Tests
# =============================================================================


class TestNotesAPI:
    """Tests for the high-level Notes API class."""

    def test_notes_api_initialization(self, tmp_path):
        """Test Notes API initialization."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)

        assert notes.workflow_id == "test-workflow"
        assert notes.paths.workflow_id == "test-workflow"

    def test_notes_api_add_note(self, tmp_path):
        """Test adding a note via the API."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)

        created = notes.add(
            agent_id="coder-agent",
            title="Test Note",
            content="Test content",
            category=NoteCategory.LEARNING,
            tags=["test"],
        )

        assert created.id is not None
        assert created.agent_id == "coder-agent"
        assert created.title == "Test Note"

        # Verify it was saved
        all_notes = notes.list()
        assert len(all_notes) == 1

    def test_notes_api_convenience_methods(self, tmp_path):
        """Test convenience methods for adding notes by category."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)

        notes.add_observation("agent", "Observation", "Observed something")
        notes.add_learning("agent", "Learning", "Learned something")
        notes.add_decision("agent", "Decision", "Decided something")
        notes.add_warning("agent", "Warning", "Warning about something")
        notes.add_accomplishment("agent", "Done", "Completed something")
        notes.add_todo("agent", "TODO", "Need to do something")

        all_notes = notes.list()
        assert len(all_notes) == 6

        categories = [n.category for n in all_notes]
        assert NoteCategory.OBSERVATION in categories
        assert NoteCategory.LEARNING in categories
        assert NoteCategory.DECISION in categories
        assert NoteCategory.WARNING in categories
        assert NoteCategory.ACCOMPLISHMENT in categories
        assert NoteCategory.TODO in categories

    def test_notes_api_list_with_filters(self, tmp_path):
        """Test listing notes with filters."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)

        notes.add_learning("agent-1", "L1", "Learning 1")
        notes.add_learning("agent-2", "L2", "Learning 2")
        notes.add_observation("agent-1", "O1", "Observation 1")

        # Filter by agent
        agent1_notes = notes.list(agent_id="agent-1")
        assert len(agent1_notes) == 2

        # Filter by category
        learnings = notes.list(category=NoteCategory.LEARNING)
        assert len(learnings) == 2

    def test_notes_api_search(self, tmp_path):
        """Test searching notes via the API."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)

        notes.add("agent", "Auth bug", "Found authentication bug", NoteCategory.WARNING)
        notes.add("agent", "DB issue", "Database connection problem", NoteCategory.WARNING)
        notes.add("agent", "Auth fix", "Fixed the auth issue", NoteCategory.ACCOMPLISHMENT)

        results = notes.search("auth")
        assert len(results) == 2

    def test_notes_api_get_summary(self, tmp_path):
        """Test getting notes summary."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)

        notes.add_learning("agent", "L1", "Content 1")
        notes.add_learning("agent", "L2", "Content 2")
        notes.add_warning("agent", "W1", "Warning content")

        summary = notes.get_summary()

        assert "Notes Summary" in summary
        assert "3 total" in summary
        assert "LEARNING" in summary
        assert "WARNING" in summary

    def test_notes_api_format_for_context(self, tmp_path):
        """Test formatting notes for agent context."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)

        notes.add("agent", "Title 1", "Content 1", NoteCategory.LEARNING)
        notes.add("agent", "Title 2", "Content 2", NoteCategory.OBSERVATION)

        context = notes.format_for_context()

        assert "## Shared Notes" in context
        assert "Title 1" in context
        assert "Title 2" in context
        assert "Content 1" in context
        assert "Content 2" in context

    def test_notes_api_empty_notes(self, tmp_path):
        """Test behavior with no notes."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)

        assert notes.list() == []
        assert notes.search("anything") == []
        assert "No notes found" in notes.get_summary()
        assert "No shared notes" in notes.format_for_context()


# =============================================================================
# Integration Tests
# =============================================================================


class TestNotesIntegration:
    """Integration tests for the complete notes system."""

    def test_full_workflow_multiple_agents(self, tmp_path):
        """Test a realistic workflow with multiple agents taking notes."""
        notes = Notes(workflow_id="feature-123", base_dir=tmp_path)

        # Planning agent adds context
        notes.add(
            agent_id="planner",
            title="Feature scope defined",
            content="This feature requires modifications to auth and user modules.",
            category=NoteCategory.CONTEXT,
            tags=["planning", "scope"],
        )

        # Coder agent discovers something while implementing
        notes.add_learning(
            agent_id="coder",
            title="Auth module uses async pattern",
            content="All auth methods are async and return Promises.",
            related_file="src/auth/handler.py",
        )

        # Coder agent makes a decision
        notes.add_decision(
            agent_id="coder",
            title="Using repository pattern for data access",
            content="Following existing codebase patterns for consistency.",
        )

        # Coder agent completes a feature
        notes.add_accomplishment(
            agent_id="coder",
            title="User authentication implemented",
            content="Added login, logout, and token refresh endpoints.",
            related_feature="user-authentication",
        )

        # Reviewer agent adds a warning
        notes.add_warning(
            agent_id="reviewer",
            title="Missing rate limiting on auth endpoints",
            content="Should add rate limiting to prevent brute force attacks.",
            tags=["security", "review"],
        )

        # Verify all notes are accessible
        all_notes = notes.list()
        assert len(all_notes) == 5

        # Verify filtering works
        coder_notes = notes.list(agent_id="coder")
        assert len(coder_notes) == 3

        warnings = notes.list(category=NoteCategory.WARNING)
        assert len(warnings) == 1

        # Verify search works
        auth_notes = notes.search("auth")
        assert len(auth_notes) >= 2

        # Verify summary includes all categories
        summary = notes.get_summary()
        assert "CONTEXT" in summary
        assert "LEARNING" in summary
        assert "DECISION" in summary
        assert "ACCOMPLISHMENT" in summary
        assert "WARNING" in summary
