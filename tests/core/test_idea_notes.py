# ABOUTME: Tests for idea note handler in NotesProjectionBuilder
# ABOUTME: Tests apply_agent_note_idea() method to handle idea note events and add to notes list

"""Tests for idea note handler in NotesProjectionBuilder.

This test module validates the implementation of apply_agent_note_idea()
method that handles agent.note.idea events and properly adds them to
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


class TestIdeaNoteHandler:
    """Test the apply_agent_note_idea method."""

    def test_adds_idea_note_to_empty_state(self):
        """Test that idea note is properly added to empty notes state."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        # Create idea event data matching AgentNoteEventData schema
        event_data = {
            "agent_id": "agent-123",
            "title": "Test Idea",
            "content": "This is a brilliant idea about the system architecture.",
            "tags": ["architecture", "innovation"],
            "related_file": "src/core/base.py",
            "related_feature": "feature-789"
        }

        result_state = builder.apply_agent_note_idea(event_data, initial_state)

        # Verify note was added to notes list
        assert len(result_state['notes']) == 1

        note = result_state['notes'][0]
        assert note['agent_id'] == "agent-123"
        assert note['title'] == "Test Idea"
        assert note['content'] == "This is a brilliant idea about the system architecture."
        assert note['category'] == "idea"
        assert note['tags'] == ["architecture", "innovation"]
        assert note['related_file'] == "src/core/base.py"
        assert note['related_feature'] == "feature-789"
        assert 'created_at' in note

    def test_adds_idea_note_with_minimal_data(self):
        """Test idea note with only required fields."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-456",
            "title": "Key Idea",
            "content": "Important innovative concept.",
            "tags": []
        }

        result_state = builder.apply_agent_note_idea(event_data, initial_state)

        assert len(result_state['notes']) == 1
        note = result_state['notes'][0]
        assert note['agent_id'] == "agent-456"
        assert note['title'] == "Key Idea"
        assert note['content'] == "Important innovative concept."
        assert note['category'] == "idea"
        assert note['tags'] == []
        assert note['related_file'] is None
        assert note['related_feature'] is None

    def test_adds_idea_note_to_existing_notes(self):
        """Test adding idea note when notes already exist."""
        builder = NotesProjectionBuilder()

        # Create state with existing note
        existing_state = {
            'notes': [
                {
                    'agent_id': 'agent-001',
                    'title': 'Existing Observation',
                    'content': 'Previous observation',
                    'category': 'observation',
                    'tags': ['system'],
                    'related_file': None,
                    'related_feature': None,
                    'created_at': '2024-01-01T00:00:00'
                }
            ],
            'by_category': {'observation': [0]},
            'by_agent': {'agent-001': [0]},
            'by_tag': {'system': [0]}
        }

        event_data = {
            "agent_id": "agent-456",
            "title": "New Idea",
            "content": "Fresh innovative content.",
            "tags": ["innovation", "important"]
        }

        result_state = builder.apply_agent_note_idea(event_data, existing_state)

        # Verify both notes exist
        assert len(result_state['notes']) == 2

        # Original note unchanged
        assert result_state['notes'][0] == existing_state['notes'][0]

        # New note added
        new_note = result_state['notes'][1]
        assert new_note['agent_id'] == "agent-456"
        assert new_note['title'] == "New Idea"
        assert new_note['category'] == "idea"

    def test_updates_by_category_index(self):
        """Test that by_category index is updated when adding idea note."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-123",
            "title": "Test Idea",
            "content": "Test content.",
            "tags": ["test"]
        }

        result_state = builder.apply_agent_note_idea(event_data, initial_state)

        # Check by_category index
        assert 'idea' in result_state['by_category']
        assert result_state['by_category']['idea'] == [0]

    def test_updates_by_agent_index(self):
        """Test that by_agent index is updated when adding idea note."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-456",
            "title": "Agent Idea",
            "content": "Test content.",
            "tags": ["test"]
        }

        result_state = builder.apply_agent_note_idea(event_data, initial_state)

        # Check by_agent index
        assert 'agent-456' in result_state['by_agent']
        assert result_state['by_agent']['agent-456'] == [0]

    def test_updates_by_tag_index(self):
        """Test that by_tag index is updated when adding idea note."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-789",
            "title": "Tagged Idea",
            "content": "Test content.",
            "tags": ["innovation", "design", "architecture"]
        }

        result_state = builder.apply_agent_note_idea(event_data, initial_state)

        # Check by_tag index for each tag
        assert 'innovation' in result_state['by_tag']
        assert result_state['by_tag']['innovation'] == [0]
        assert 'design' in result_state['by_tag']
        assert result_state['by_tag']['design'] == [0]
        assert 'architecture' in result_state['by_tag']
        assert result_state['by_tag']['architecture'] == [0]

    def test_handles_empty_tags_list(self):
        """Test idea note with empty tags list doesn't break indexing."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-999",
            "title": "No Tags Idea",
            "content": "Idea without tags.",
            "tags": []
        }

        result_state = builder.apply_agent_note_idea(event_data, initial_state)

        # Should still work with empty tags
        assert len(result_state['notes']) == 1
        assert result_state['notes'][0]['tags'] == []

        # by_tag should be empty (no tags to index)
        assert result_state['by_tag'] == {}

        # Other indexes should still work
        assert 'idea' in result_state['by_category']
        assert 'agent-999' in result_state['by_agent']

    def test_preserves_original_state_immutability(self):
        """Test that the original state is not modified (immutability)."""
        builder = NotesProjectionBuilder()
        original_state = builder.get_initial_state()
        original_notes_copy = original_state['notes'].copy()

        event_data = {
            "agent_id": "agent-123",
            "title": "Test Idea",
            "content": "Test content.",
            "tags": ["test"]
        }

        result_state = builder.apply_agent_note_idea(event_data, original_state)

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
        """Test that existing indexes are properly updated when adding new idea notes."""
        builder = NotesProjectionBuilder()

        # Start with state containing existing indexes
        initial_state = {
            'notes': [
                {
                    'agent_id': 'agent-001',
                    'title': 'First Note',
                    'content': 'Content 1',
                    'category': 'observation',
                    'tags': ['shared', 'first'],
                    'related_file': None,
                    'related_feature': None,
                    'created_at': '2024-01-01T00:00:00'
                }
            ],
            'by_category': {'observation': [0]},
            'by_agent': {'agent-001': [0]},
            'by_tag': {'shared': [0], 'first': [0]}
        }

        event_data = {
            "agent_id": "agent-001",  # Same agent
            "title": "Second Idea",
            "content": "Idea content.",
            "tags": ["shared", "second"]  # One shared tag, one new tag
        }

        result_state = builder.apply_agent_note_idea(event_data, initial_state)

        # Verify indexes are properly updated
        assert len(result_state['notes']) == 2

        # by_category should have both observation and idea
        assert set(result_state['by_category'].keys()) == {'observation', 'idea'}
        assert result_state['by_category']['observation'] == [0]
        assert result_state['by_category']['idea'] == [1]

        # by_agent should have agent-001 pointing to both notes
        assert result_state['by_agent']['agent-001'] == [0, 1]

        # by_tag should handle shared and distinct tags
        assert result_state['by_tag']['shared'] == [0, 1]  # Both notes have 'shared'
        assert result_state['by_tag']['first'] == [0]      # Only first note
        assert result_state['by_tag']['second'] == [1]     # Only second note

    def test_note_contains_timestamp(self):
        """Test that idea notes include a created_at timestamp."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-123",
            "title": "Timestamped Idea",
            "content": "Should have timestamp.",
            "tags": ["timestamp"]
        }

        result_state = builder.apply_agent_note_idea(event_data, initial_state)

        note = result_state['notes'][0]
        assert 'created_at' in note
        assert isinstance(note['created_at'], str)
        # Verify it looks like an ISO timestamp
        assert 'T' in note['created_at']
        assert note['created_at'].endswith('Z') or '+' in note['created_at'] or note['created_at'].count(':') >= 2


class TestIdeaNoteHandlerEdgeCases:
    """Test edge cases and error conditions for idea note handler."""

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
            "title": "Test Idea",
            "content": "Test content.",
            "tags": ["test"]
        }

        # Should handle gracefully and complete missing indexes
        result_state = builder.apply_agent_note_idea(event_data, incomplete_state)

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
            "title": "Test Idea",
            "content": "Test content.",
            "tags": ["test"]
        }

        result_state = builder.apply_agent_note_idea(event_data, state_with_extras)

        # Should preserve extra fields
        assert result_state['custom_field'] == 'should_be_preserved'
        assert result_state['metadata'] == {'version': 1}

        # And still add the note properly
        assert len(result_state['notes']) == 1