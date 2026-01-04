# ABOUTME: Test suite for note event type constants in EventType enum
# ABOUTME: Tests the 7 new agent note event types for proper definition and string values

"""Test suite for note event type constants.

Tests that the 7 agent note event type constants are properly defined in the EventType enum:
- AGENT_NOTE_OBSERVATION
- AGENT_NOTE_LEARNING
- AGENT_NOTE_DECISION
- AGENT_NOTE_WARNING
- AGENT_NOTE_ACCOMPLISHMENT
- AGENT_NOTE_CONTEXT
- AGENT_NOTE_TODO
"""

import pytest
from jean_claude.core.events import EventType


class TestNoteEventTypeConstants:
    """Test that all 7 note event type constants are properly defined."""

    def test_agent_note_observation_exists(self):
        """Test that AGENT_NOTE_OBSERVATION constant exists with correct value."""
        assert hasattr(EventType, 'AGENT_NOTE_OBSERVATION')
        assert EventType.AGENT_NOTE_OBSERVATION == "agent.note.observation"
        assert isinstance(EventType.AGENT_NOTE_OBSERVATION, str)

    def test_agent_note_learning_exists(self):
        """Test that AGENT_NOTE_LEARNING constant exists with correct value."""
        assert hasattr(EventType, 'AGENT_NOTE_LEARNING')
        assert EventType.AGENT_NOTE_LEARNING == "agent.note.learning"
        assert isinstance(EventType.AGENT_NOTE_LEARNING, str)

    def test_agent_note_decision_exists(self):
        """Test that AGENT_NOTE_DECISION constant exists with correct value."""
        assert hasattr(EventType, 'AGENT_NOTE_DECISION')
        assert EventType.AGENT_NOTE_DECISION == "agent.note.decision"
        assert isinstance(EventType.AGENT_NOTE_DECISION, str)

    def test_agent_note_warning_exists(self):
        """Test that AGENT_NOTE_WARNING constant exists with correct value."""
        assert hasattr(EventType, 'AGENT_NOTE_WARNING')
        assert EventType.AGENT_NOTE_WARNING == "agent.note.warning"
        assert isinstance(EventType.AGENT_NOTE_WARNING, str)

    def test_agent_note_accomplishment_exists(self):
        """Test that AGENT_NOTE_ACCOMPLISHMENT constant exists with correct value."""
        assert hasattr(EventType, 'AGENT_NOTE_ACCOMPLISHMENT')
        assert EventType.AGENT_NOTE_ACCOMPLISHMENT == "agent.note.accomplishment"
        assert isinstance(EventType.AGENT_NOTE_ACCOMPLISHMENT, str)

    def test_agent_note_context_exists(self):
        """Test that AGENT_NOTE_CONTEXT constant exists with correct value."""
        assert hasattr(EventType, 'AGENT_NOTE_CONTEXT')
        assert EventType.AGENT_NOTE_CONTEXT == "agent.note.context"
        assert isinstance(EventType.AGENT_NOTE_CONTEXT, str)

    def test_agent_note_todo_exists(self):
        """Test that AGENT_NOTE_TODO constant exists with correct value."""
        assert hasattr(EventType, 'AGENT_NOTE_TODO')
        assert EventType.AGENT_NOTE_TODO == "agent.note.todo"
        assert isinstance(EventType.AGENT_NOTE_TODO, str)


class TestNoteEventTypeConstantsIntegration:
    """Test that note event constants integrate properly with the EventType enum."""

    def test_all_note_constants_are_event_type_members(self):
        """Test that all note constants are proper EventType enum members."""
        note_constants = [
            EventType.AGENT_NOTE_OBSERVATION,
            EventType.AGENT_NOTE_LEARNING,
            EventType.AGENT_NOTE_DECISION,
            EventType.AGENT_NOTE_WARNING,
            EventType.AGENT_NOTE_ACCOMPLISHMENT,
            EventType.AGENT_NOTE_CONTEXT,
            EventType.AGENT_NOTE_TODO,
        ]

        # All should be strings (EventType inherits from str, Enum)
        for constant in note_constants:
            assert isinstance(constant, str)
            assert isinstance(constant, EventType)

    def test_note_constants_have_agent_note_prefix(self):
        """Test that all note constants follow the 'agent.note.' naming convention."""
        note_constants = [
            EventType.AGENT_NOTE_OBSERVATION,
            EventType.AGENT_NOTE_LEARNING,
            EventType.AGENT_NOTE_DECISION,
            EventType.AGENT_NOTE_WARNING,
            EventType.AGENT_NOTE_ACCOMPLISHMENT,
            EventType.AGENT_NOTE_CONTEXT,
            EventType.AGENT_NOTE_TODO,
        ]

        for constant in note_constants:
            assert constant.startswith("agent.note.")

    def test_note_constants_are_unique(self):
        """Test that all note constants have unique string values."""
        note_constants = [
            EventType.AGENT_NOTE_OBSERVATION,
            EventType.AGENT_NOTE_LEARNING,
            EventType.AGENT_NOTE_DECISION,
            EventType.AGENT_NOTE_WARNING,
            EventType.AGENT_NOTE_ACCOMPLISHMENT,
            EventType.AGENT_NOTE_CONTEXT,
            EventType.AGENT_NOTE_TODO,
        ]

        # Convert to set to check for uniqueness
        unique_constants = set(note_constants)
        assert len(unique_constants) == len(note_constants), "Note event constants must have unique values"

    def test_note_constants_can_be_used_in_event_creation(self):
        """Test that note constants can be used to create Event objects."""
        from jean_claude.core.events import Event

        # Test creating events with each note constant
        note_constants = [
            EventType.AGENT_NOTE_OBSERVATION,
            EventType.AGENT_NOTE_LEARNING,
            EventType.AGENT_NOTE_DECISION,
            EventType.AGENT_NOTE_WARNING,
            EventType.AGENT_NOTE_ACCOMPLISHMENT,
            EventType.AGENT_NOTE_CONTEXT,
            EventType.AGENT_NOTE_TODO,
        ]

        for event_type in note_constants:
            event = Event(
                workflow_id="test-workflow",
                event_type=event_type,
                data={"test": "data"}
            )
            assert event.event_type == event_type
            assert event.workflow_id == "test-workflow"
            assert event.data == {"test": "data"}


class TestNoteEventTypeConstantsCompleteness:
    """Test that all required note event constants are present."""

    def test_all_seven_note_constants_exist(self):
        """Test that exactly 7 note event constants are defined."""
        # Get all EventType members that start with AGENT_NOTE_
        note_members = [
            member for member in EventType.__members__.values()
            if member.name.startswith("AGENT_NOTE_")
        ]

        expected_constants = {
            "AGENT_NOTE_OBSERVATION",
            "AGENT_NOTE_LEARNING",
            "AGENT_NOTE_DECISION",
            "AGENT_NOTE_WARNING",
            "AGENT_NOTE_ACCOMPLISHMENT",
            "AGENT_NOTE_CONTEXT",
            "AGENT_NOTE_TODO",
        }

        actual_constants = {member.name for member in note_members}

        # Check that we have exactly the expected constants
        assert actual_constants == expected_constants, (
            f"Expected note constants: {expected_constants}, "
            f"but found: {actual_constants}"
        )

        # Verify we have exactly 7 constants
        assert len(note_members) == 7, f"Expected 7 note constants, found {len(note_members)}"