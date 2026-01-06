# ABOUTME: Tests for observation note handler in NotesProjectionBuilder
# ABOUTME: Tests apply_agent_note_observation() method to handle observation note events and add to notes list

"""Tests for observation note handler in NotesProjectionBuilder.

This test module validates the implementation of apply_agent_note_observation()
method that handles agent.note.observation events and properly adds them to
the notes list and associated indexes.

Test Coverage:
- Basic note addition to notes list
- Note structure validation
- Index updates (by_category, by_agent, by_tag)
- Edge cases (empty tags, missing optional fields)
- State immutability and proper copying
- Integration with existing notes
"""

import pytest
from typing import Dict, Any

from jean_claude.core.notes_projection_builder import NotesProjectionBuilder
from jean_claude.core.events import AgentNoteEventData


class TestObservationNoteHandler:
    """Test the apply_agent_note_observation method."""

    def test_adds_observation_note_to_empty_state(self):
        """Test that observation note is properly added to empty notes state."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        # Create observation event data matching AgentNoteEventData schema
        event_data = {
            "agent_id": "agent-123",
            "title": "Test Observation",
            "content": "This is an observation about the system behavior.",
            "tags": ["system", "behavior"],
            "related_file": "src/main.py",
            "related_feature": "feature-456"
        }

        result_state = builder.apply_agent_note_observation(event_data, initial_state)

        # Verify note was added to notes list
        assert len(result_state['notes']) == 1

        note = result_state['notes'][0]
        assert note['agent_id'] == "agent-123"
        assert note['title'] == "Test Observation"
        assert note['content'] == "This is an observation about the system behavior."
        assert note['category'] == "observation"
        assert note['tags'] == ["system", "behavior"]
        assert note['related_file'] == "src/main.py"
        assert note['related_feature'] == "feature-456"
        assert 'created_at' in note

    def test_adds_observation_note_with_minimal_data(self):
        """Test observation note with only required fields."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-789",
            "title": "Minimal Note",
            "content": "Simple observation.",
            "tags": []
        }

        result_state = builder.apply_agent_note_observation(event_data, initial_state)

        assert len(result_state['notes']) == 1
        note = result_state['notes'][0]
        assert note['agent_id'] == "agent-789"
        assert note['title'] == "Minimal Note"
        assert note['content'] == "Simple observation."
        assert note['category'] == "observation"
        assert note['tags'] == []
        assert note['related_file'] is None
        assert note['related_feature'] is None

    def test_adds_observation_note_to_existing_notes(self):
        """Test adding observation note when notes already exist."""
        builder = NotesProjectionBuilder()

        # Create state with existing note
        existing_state = {
            'notes': [
                {
                    'agent_id': 'agent-001',
                    'title': 'Existing Note',
                    'content': 'Previous content',
                    'category': 'decision',
                    'tags': ['old'],
                    'related_file': None,
                    'related_feature': None,
                    'created_at': '2024-01-01T00:00:00'
                }
            ],
            'by_category': {'decision': [0]},
            'by_agent': {'agent-001': [0]},
            'by_tag': {'old': [0]}
        }

        event_data = {
            "agent_id": "agent-456",
            "title": "New Observation",
            "content": "Fresh observation content.",
            "tags": ["new", "important"]
        }

        result_state = builder.apply_agent_note_observation(event_data, existing_state)

        # Verify both notes exist
        assert len(result_state['notes']) == 2

        # Original note unchanged
        assert result_state['notes'][0] == existing_state['notes'][0]

        # New note added
        new_note = result_state['notes'][1]
        assert new_note['agent_id'] == "agent-456"
        assert new_note['title'] == "New Observation"
        assert new_note['category'] == "observation"

    def test_updates_by_category_index(self):
        """Test that by_category index is updated when adding observation note."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-123",
            "title": "Test Observation",
            "content": "Test content.",
            "tags": ["test"]
        }

        result_state = builder.apply_agent_note_observation(event_data, initial_state)

        # Check by_category index
        assert 'observation' in result_state['by_category']
        assert result_state['by_category']['observation'] == [0]

    def test_updates_by_agent_index(self):
        """Test that by_agent index is updated when adding observation note."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-456",
            "title": "Agent Note",
            "content": "Test content.",
            "tags": ["test"]
        }

        result_state = builder.apply_agent_note_observation(event_data, initial_state)

        # Check by_agent index
        assert 'agent-456' in result_state['by_agent']
        assert result_state['by_agent']['agent-456'] == [0]

    def test_updates_by_tag_index(self):
        """Test that by_tag index is updated when adding observation note."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-789",
            "title": "Tagged Note",
            "content": "Test content.",
            "tags": ["important", "urgent", "testing"]
        }

        result_state = builder.apply_agent_note_observation(event_data, initial_state)

        # Check by_tag index for each tag
        assert 'important' in result_state['by_tag']
        assert result_state['by_tag']['important'] == [0]
        assert 'urgent' in result_state['by_tag']
        assert result_state['by_tag']['urgent'] == [0]
        assert 'testing' in result_state['by_tag']
        assert result_state['by_tag']['testing'] == [0]

    def test_handles_empty_tags_list(self):
        """Test observation note with empty tags list doesn't break indexing."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-999",
            "title": "No Tags Note",
            "content": "Note without tags.",
            "tags": []
        }

        result_state = builder.apply_agent_note_observation(event_data, initial_state)

        # Should still work with empty tags
        assert len(result_state['notes']) == 1
        assert result_state['notes'][0]['tags'] == []

        # by_tag should be empty (no tags to index)
        assert result_state['by_tag'] == {}

        # Other indexes should still work
        assert 'observation' in result_state['by_category']
        assert 'agent-999' in result_state['by_agent']

    def test_preserves_original_state_immutability(self):
        """Test that the original state is not modified (immutability)."""
        builder = NotesProjectionBuilder()
        original_state = builder.get_initial_state()
        original_notes_copy = original_state['notes'].copy()

        event_data = {
            "agent_id": "agent-123",
            "title": "Test Note",
            "content": "Test content.",
            "tags": ["test"]
        }

        result_state = builder.apply_agent_note_observation(event_data, original_state)

        # Original state should be unchanged
        assert original_state['notes'] == original_notes_copy
        assert len(original_state['notes']) == 0
        assert original_state['by_category'] == {}
        assert original_state['by_agent'] == {}
        assert original_state['by_tag'] == {}

        # Result state should be different object
        assert result_state is not original_state
        assert len(result_state['notes']) == 1

    def test_updates_existing_indexes_correctly(self):
        """Test that existing indexes are properly updated when adding new notes."""
        builder = NotesProjectionBuilder()

        # Start with state containing existing indexes
        initial_state = {
            'notes': [
                {
                    'agent_id': 'agent-001',
                    'title': 'First Note',
                    'content': 'Content 1',
                    'category': 'decision',
                    'tags': ['shared', 'first'],
                    'related_file': None,
                    'related_feature': None,
                    'created_at': '2024-01-01T00:00:00'
                }
            ],
            'by_category': {'decision': [0]},
            'by_agent': {'agent-001': [0]},
            'by_tag': {'shared': [0], 'first': [0]}
        }

        event_data = {
            "agent_id": "agent-001",  # Same agent
            "title": "Second Note",
            "content": "Content 2.",
            "tags": ["shared", "second"]  # One shared tag, one new tag
        }

        result_state = builder.apply_agent_note_observation(event_data, initial_state)

        # Verify indexes are properly updated
        assert len(result_state['notes']) == 2

        # by_category should have both decision and observation
        assert set(result_state['by_category'].keys()) == {'decision', 'observation'}
        assert result_state['by_category']['decision'] == [0]
        assert result_state['by_category']['observation'] == [1]

        # by_agent should have agent-001 pointing to both notes
        assert result_state['by_agent']['agent-001'] == [0, 1]

        # by_tag should handle shared and distinct tags
        assert result_state['by_tag']['shared'] == [0, 1]  # Both notes have 'shared'
        assert result_state['by_tag']['first'] == [0]      # Only first note
        assert result_state['by_tag']['second'] == [1]     # Only second note

    def test_note_contains_timestamp(self):
        """Test that observation notes include a created_at timestamp."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-123",
            "title": "Timestamped Note",
            "content": "Should have timestamp.",
            "tags": ["timestamp"]
        }

        result_state = builder.apply_agent_note_observation(event_data, initial_state)

        note = result_state['notes'][0]
        assert 'created_at' in note
        assert isinstance(note['created_at'], str)
        # Verify it looks like an ISO timestamp
        assert 'T' in note['created_at']
        assert note['created_at'].endswith('Z') or '+' in note['created_at'] or note['created_at'].count(':') >= 2


class TestObservationNoteHandlerEdgeCases:
    """Test edge cases and error conditions for observation note handler."""

    def test_handles_malformed_state_gracefully(self):
        """Test that method handles missing state keys gracefully."""
        builder = NotesProjectionBuilder()

        # State missing some keys
        incomplete_state = {
            'notes': [],
            'by_category': {},
            # Missing by_agent and by_tag
        }

        event_data = {
            "agent_id": "agent-123",
            "title": "Test Note",
            "content": "Test content.",
            "tags": ["test"]
        }

        # Should handle gracefully and complete missing indexes
        result_state = builder.apply_agent_note_observation(event_data, incomplete_state)

        assert len(result_state['notes']) == 1
        assert 'by_agent' in result_state
        assert 'by_tag' in result_state
        assert result_state['by_agent']['agent-123'] == [0]
        assert result_state['by_tag']['test'] == [0]

    def test_preserves_existing_state_structure(self):
        """Test that method preserves all existing state keys."""
        builder = NotesProjectionBuilder()

        # State with extra keys
        state_with_extras = {
            'notes': [],
            'by_category': {},
            'by_agent': {},
            'by_tag': {},
            'custom_field': 'should_be_preserved',
            'metadata': {'version': 1}
        }

        event_data = {
            "agent_id": "agent-123",
            "title": "Test Note",
            "content": "Test content.",
            "tags": ["test"]
        }

        result_state = builder.apply_agent_note_observation(event_data, state_with_extras)

        # Should preserve extra fields
        assert result_state['custom_field'] == 'should_be_preserved'
        assert result_state['metadata'] == {'version': 1}

        # And still add the note properly
        assert len(result_state['notes']) == 1