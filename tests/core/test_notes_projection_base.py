# ABOUTME: Tests for NotesProjectionBuilder base class
# ABOUTME: Tests basic structure, initialization, and empty state creation

"""Tests for NotesProjectionBuilder base class.

This test module validates the basic structure and initialization of the
NotesProjectionBuilder class, which extends ProjectionBuilder to provide
notes functionality for tracking agent notes across different categories.

Test Coverage:
- Class initialization and inheritance
- Basic state structure creation
- Empty state validation
- Notes list and index structures
"""

import pytest
from typing import Dict, Any

from jean_claude.core.notes_projection_builder import NotesProjectionBuilder


class TestNotesProjectionBuilderInit:
    """Test initialization and basic structure of NotesProjectionBuilder."""

    def test_can_instantiate(self):
        """Test that NotesProjectionBuilder can be instantiated."""
        builder = NotesProjectionBuilder()
        assert builder is not None

    def test_inherits_from_projection_builder(self):
        """Test that NotesProjectionBuilder extends ProjectionBuilder."""
        from jean_claude.core.projection_builder import ProjectionBuilder

        builder = NotesProjectionBuilder()
        assert isinstance(builder, ProjectionBuilder)

    def test_has_required_abstract_methods(self):
        """Test that all required abstract methods from ProjectionBuilder exist."""
        builder = NotesProjectionBuilder()

        # Agent message event handlers
        assert hasattr(builder, 'apply_agent_message_sent')
        assert hasattr(builder, 'apply_agent_message_acknowledged')
        assert hasattr(builder, 'apply_agent_message_completed')

        # Agent note event handlers
        assert hasattr(builder, 'apply_agent_note_observation')
        assert hasattr(builder, 'apply_agent_note_learning')
        assert hasattr(builder, 'apply_agent_note_decision')
        assert hasattr(builder, 'apply_agent_note_warning')
        assert hasattr(builder, 'apply_agent_note_accomplishment')
        assert hasattr(builder, 'apply_agent_note_context')
        assert hasattr(builder, 'apply_agent_note_todo')
        assert hasattr(builder, 'apply_agent_note_question')
        assert hasattr(builder, 'apply_agent_note_idea')
        assert hasattr(builder, 'apply_agent_note_reflection')


class TestNotesProjectionBuilderState:
    """Test state creation and structure for NotesProjectionBuilder."""

    def test_creates_initial_state(self):
        """Test that NotesProjectionBuilder creates proper initial state."""
        builder = NotesProjectionBuilder()
        initial_state = builder.create_initial_state()

        assert isinstance(initial_state, dict)
        assert 'notes' in initial_state
        assert 'by_category' in initial_state
        assert 'by_agent' in initial_state
        assert 'by_tag' in initial_state

    def test_initial_state_has_empty_structures(self):
        """Test that initial state contains empty structures for all collections."""
        builder = NotesProjectionBuilder()
        initial_state = builder.create_initial_state()

        assert initial_state['notes'] == []
        assert initial_state['by_category'] == {}
        assert initial_state['by_agent'] == {}
        assert initial_state['by_tag'] == {}

    def test_initial_state_structure_is_correct(self):
        """Test that initial state has exactly the expected structure."""
        builder = NotesProjectionBuilder()
        initial_state = builder.create_initial_state()

        expected_keys = {'notes', 'by_category', 'by_agent', 'by_tag'}
        actual_keys = set(initial_state.keys())

        assert actual_keys == expected_keys

    def test_multiple_calls_return_independent_states(self):
        """Test that multiple calls to create_initial_state return independent copies."""
        builder = NotesProjectionBuilder()
        state1 = builder.create_initial_state()
        state2 = builder.create_initial_state()

        # States should be equal but not the same object
        assert state1 == state2
        assert state1 is not state2

        # Modifying one shouldn't affect the other
        state1['notes'].append('test')
        assert state1['notes'] != state2['notes']

    def test_indexes_are_independent_dicts(self):
        """Test that index dictionaries are independent objects."""
        builder = NotesProjectionBuilder()
        state1 = builder.create_initial_state()
        state2 = builder.create_initial_state()

        # Modifying indexes in one state shouldn't affect the other
        state1['by_category']['observation'] = []
        assert 'observation' not in state2['by_category']


class TestNotesProjectionBuilderMethods:
    """Test that NotesProjectionBuilder has all required method signatures."""

    def test_has_create_initial_state_method(self):
        """Test that create_initial_state method exists and is callable."""
        builder = NotesProjectionBuilder()
        assert hasattr(builder, 'create_initial_state')
        assert callable(builder.create_initial_state)

    def test_abstract_methods_return_unchanged_state(self):
        """Test that abstract method implementations return the current state unchanged."""
        builder = NotesProjectionBuilder()
        test_state = {'notes': [], 'by_category': {}}
        test_event_data = {'agent_id': 'test-agent', 'title': 'Test Note'}

        # Test message event handlers return state unchanged
        result = builder.apply_agent_message_sent(test_event_data, test_state)
        assert result == test_state

        result = builder.apply_agent_message_acknowledged(test_event_data, test_state)
        assert result == test_state

        result = builder.apply_agent_message_completed(test_event_data, test_state)
        assert result == test_state

        # Test note event handlers return state unchanged
        result = builder.apply_agent_note_observation(test_event_data, test_state)
        assert result == test_state

        result = builder.apply_agent_note_learning(test_event_data, test_state)
        assert result == test_state

        result = builder.apply_agent_note_decision(test_event_data, test_state)
        assert result == test_state

        result = builder.apply_agent_note_warning(test_event_data, test_state)
        assert result == test_state

        result = builder.apply_agent_note_accomplishment(test_event_data, test_state)
        assert result == test_state

        result = builder.apply_agent_note_context(test_event_data, test_state)
        assert result == test_state

        result = builder.apply_agent_note_todo(test_event_data, test_state)
        assert result == test_state

        result = builder.apply_agent_note_question(test_event_data, test_state)
        assert result == test_state

        result = builder.apply_agent_note_idea(test_event_data, test_state)
        assert result == test_state

        result = builder.apply_agent_note_reflection(test_event_data, test_state)
        assert result == test_state