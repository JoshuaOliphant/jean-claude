# ABOUTME: Tests for Notes API class with event emission
# ABOUTME: Tests event publishing when event_logger is provided and backward compatibility

"""Tests for Notes API event emission.

This test module validates the Notes API's event emission functionality,
ensuring that events are properly emitted when an event_logger is provided
and that backward compatibility is maintained when no logger is given.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, call

from jean_claude.core.notes_api import Notes
from jean_claude.core.notes import NoteCategory
from jean_claude.core.events import EventType


class TestNotesEventEmission:
    """Test event emission when adding notes with event_logger."""

    def test_add_note_with_event_logger_emits_event(self, tmp_path):
        """Verify event emitted when logger provided."""
        # Setup
        workflow_id = "test-workflow"
        notes = Notes(workflow_id=workflow_id, base_dir=tmp_path)
        mock_event_logger = Mock()

        # Execute
        note = notes.add(
            agent_id="test-agent",
            title="Test Observation",
            content="Test content",
            category=NoteCategory.OBSERVATION,
            tags=["test-tag"],
            related_file="test.py",
            related_feature="test-feature",
            event_logger=mock_event_logger,
        )

        # Verify event emission
        mock_event_logger.emit.assert_called_once()
        call_args = mock_event_logger.emit.call_args

        # Verify event details
        assert call_args.kwargs["workflow_id"] == workflow_id
        assert call_args.kwargs["event_type"] == EventType.AGENT_NOTE_OBSERVATION
        assert call_args.kwargs["data"]["agent_id"] == "test-agent"
        assert call_args.kwargs["data"]["title"] == "Test Observation"
        assert call_args.kwargs["data"]["content"] == "Test content"
        assert call_args.kwargs["data"]["tags"] == ["test-tag"]
        assert call_args.kwargs["data"]["related_file"] == "test.py"
        assert call_args.kwargs["data"]["related_feature"] == "test-feature"

        # Verify note was created
        assert note.agent_id == "test-agent"
        assert note.title == "Test Observation"

    def test_add_note_without_event_logger_works(self, tmp_path):
        """Verify backward compatibility - no logger works."""
        # Setup
        workflow_id = "test-workflow"
        notes = Notes(workflow_id=workflow_id, base_dir=tmp_path)

        # Execute - no event_logger parameter
        note = notes.add(
            agent_id="test-agent",
            title="Test Note",
            content="Test content",
            category=NoteCategory.LEARNING,
        )

        # Verify note was created successfully
        assert note.agent_id == "test-agent"
        assert note.title == "Test Note"
        assert note.category == NoteCategory.LEARNING

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
        notes = Notes(workflow_id=workflow_id, base_dir=tmp_path)
        mock_event_logger = Mock()

        # Execute
        notes.add(
            agent_id="test-agent",
            title=f"Test {category.value}",
            content="Test content",
            category=category,
            event_logger=mock_event_logger,
        )

        # Verify correct event type emitted
        call_args = mock_event_logger.emit.call_args
        assert call_args.kwargs["event_type"] == expected_event_type


class TestNotesConvenienceMethodsEventEmission:
    """Test that convenience methods pass through event_logger."""

    def test_add_observation_with_event_logger(self, tmp_path):
        """Verify add_observation passes event_logger through."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)
        mock_event_logger = Mock()

        note = notes.add_observation(
            agent_id="test-agent",
            title="Test Observation",
            content="Test content",
            event_logger=mock_event_logger,
        )

        # Verify event emitted
        mock_event_logger.emit.assert_called_once()
        call_args = mock_event_logger.emit.call_args
        assert call_args.kwargs["event_type"] == EventType.AGENT_NOTE_OBSERVATION

    def test_add_learning_with_event_logger(self, tmp_path):
        """Verify add_learning passes event_logger through."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)
        mock_event_logger = Mock()

        note = notes.add_learning(
            agent_id="test-agent",
            title="Test Learning",
            content="Test content",
            event_logger=mock_event_logger,
        )

        # Verify event emitted
        mock_event_logger.emit.assert_called_once()
        call_args = mock_event_logger.emit.call_args
        assert call_args.kwargs["event_type"] == EventType.AGENT_NOTE_LEARNING

    def test_add_decision_with_event_logger(self, tmp_path):
        """Verify add_decision passes event_logger through."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)
        mock_event_logger = Mock()

        note = notes.add_decision(
            agent_id="test-agent",
            title="Test Decision",
            content="Test content",
            event_logger=mock_event_logger,
        )

        # Verify event emitted
        mock_event_logger.emit.assert_called_once()
        call_args = mock_event_logger.emit.call_args
        assert call_args.kwargs["event_type"] == EventType.AGENT_NOTE_DECISION

    def test_add_warning_with_event_logger(self, tmp_path):
        """Verify add_warning passes event_logger through."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)
        mock_event_logger = Mock()

        note = notes.add_warning(
            agent_id="test-agent",
            title="Test Warning",
            content="Test content",
            event_logger=mock_event_logger,
        )

        # Verify event emitted
        mock_event_logger.emit.assert_called_once()
        call_args = mock_event_logger.emit.call_args
        assert call_args.kwargs["event_type"] == EventType.AGENT_NOTE_WARNING

    def test_add_accomplishment_with_event_logger(self, tmp_path):
        """Verify add_accomplishment passes event_logger through."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)
        mock_event_logger = Mock()

        note = notes.add_accomplishment(
            agent_id="test-agent",
            title="Test Accomplishment",
            content="Test content",
            event_logger=mock_event_logger,
        )

        # Verify event emitted
        mock_event_logger.emit.assert_called_once()
        call_args = mock_event_logger.emit.call_args
        assert call_args.kwargs["event_type"] == EventType.AGENT_NOTE_ACCOMPLISHMENT

    def test_add_todo_with_event_logger(self, tmp_path):
        """Verify add_todo passes event_logger through."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)
        mock_event_logger = Mock()

        note = notes.add_todo(
            agent_id="test-agent",
            title="Test TODO",
            content="Test content",
            event_logger=mock_event_logger,
        )

        # Verify event emitted
        mock_event_logger.emit.assert_called_once()
        call_args = mock_event_logger.emit.call_args
        assert call_args.kwargs["event_type"] == EventType.AGENT_NOTE_TODO

    def test_convenience_methods_without_event_logger_work(self, tmp_path):
        """Verify convenience methods work without event_logger."""
        notes = Notes(workflow_id="test-workflow", base_dir=tmp_path)

        # All convenience methods should work without event_logger
        notes.add_observation(
            agent_id="test-agent", title="Test", content="Test"
        )
        notes.add_learning(
            agent_id="test-agent", title="Test", content="Test"
        )
        notes.add_decision(
            agent_id="test-agent", title="Test", content="Test"
        )
        notes.add_warning(
            agent_id="test-agent", title="Test", content="Test"
        )
        notes.add_accomplishment(
            agent_id="test-agent", title="Test", content="Test"
        )
        notes.add_todo(
            agent_id="test-agent", title="Test", content="Test"
        )

        # Verify all 6 notes were created
        all_notes = notes.list()
        assert len(all_notes) == 6
