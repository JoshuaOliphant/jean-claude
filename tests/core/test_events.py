# ABOUTME: Tests for event system components and event type mappings
# ABOUTME: Validates EventType enum and ensures correspondence with note categories

"""Tests for event system.

This test module validates the event system infrastructure, particularly
ensuring that event types match corresponding model enums like NoteCategory.
"""

import pytest

from jean_claude.core.events import EventType
from jean_claude.core.notes import NoteCategory


def test_event_types_match_note_categories():
    """Ensure 1:1 correspondence between NoteCategory and EventType.

    This test prevents future bugs where a developer adds a NoteCategory
    without a corresponding EventType or vice versa.
    """
    # Extract note category values
    note_categories = {cat.value for cat in NoteCategory}

    # Extract event type values for agent notes
    event_types = {
        et.value.replace("agent.note.", "")
        for et in EventType
        if et.value.startswith("agent.note.")
    }

    # Verify 1:1 mapping
    assert note_categories == event_types, (
        f"Mismatch between NoteCategory and EventType:\n"
        f"  Only in NoteCategory: {note_categories - event_types}\n"
        f"  Only in EventType: {event_types - note_categories}"
    )

    # Verify all 10 expected categories exist
    expected_categories = {
        "observation", "question", "idea", "decision", "learning",
        "reflection", "warning", "accomplishment", "context", "todo"
    }
    assert note_categories == expected_categories, (
        f"Expected 10 note categories, got {len(note_categories)}: {note_categories}"
    )
