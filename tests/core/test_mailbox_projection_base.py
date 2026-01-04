# ABOUTME: Tests for MailboxProjectionBuilder base class
# ABOUTME: Tests basic structure, initialization, and empty state creation

"""Tests for MailboxProjectionBuilder base class.

This test module validates the basic structure and initialization of the
MailboxProjectionBuilder class, which extends ProjectionBuilder to provide
mailbox functionality for agent messaging.

Test Coverage:
- Class initialization and inheritance
- Basic state structure creation
- Empty state validation
"""

import pytest
from typing import Dict, Any

from jean_claude.core.mailbox_projection_builder import MailboxProjectionBuilder


class TestMailboxProjectionBuilderInit:
    """Test initialization and basic structure of MailboxProjectionBuilder."""

    def test_can_instantiate(self):
        """Test that MailboxProjectionBuilder can be instantiated."""
        builder = MailboxProjectionBuilder()
        assert builder is not None

    def test_inherits_from_projection_builder(self):
        """Test that MailboxProjectionBuilder extends ProjectionBuilder."""
        from jean_claude.core.projection_builder import ProjectionBuilder

        builder = MailboxProjectionBuilder()
        assert isinstance(builder, ProjectionBuilder)

    def test_has_required_abstract_methods(self):
        """Test that all required abstract methods from ProjectionBuilder exist."""
        builder = MailboxProjectionBuilder()

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


class TestMailboxProjectionBuilderState:
    """Test state creation and structure for MailboxProjectionBuilder."""

    def test_creates_initial_state(self):
        """Test that MailboxProjectionBuilder creates proper initial state."""
        builder = MailboxProjectionBuilder()
        initial_state = builder.create_initial_state()

        assert isinstance(initial_state, dict)
        assert 'inbox' in initial_state
        assert 'outbox' in initial_state
        assert 'conversation_history' in initial_state

    def test_initial_state_has_empty_arrays(self):
        """Test that initial state contains empty arrays for all collections."""
        builder = MailboxProjectionBuilder()
        initial_state = builder.create_initial_state()

        assert initial_state['inbox'] == []
        assert initial_state['outbox'] == []
        assert initial_state['conversation_history'] == []

    def test_initial_state_structure_is_correct(self):
        """Test that initial state has exactly the expected structure."""
        builder = MailboxProjectionBuilder()
        initial_state = builder.create_initial_state()

        expected_keys = {'inbox', 'outbox', 'conversation_history'}
        actual_keys = set(initial_state.keys())

        assert actual_keys == expected_keys

    def test_multiple_calls_return_independent_states(self):
        """Test that multiple calls to create_initial_state return independent copies."""
        builder = MailboxProjectionBuilder()
        state1 = builder.create_initial_state()
        state2 = builder.create_initial_state()

        # States should be equal but not the same object
        assert state1 == state2
        assert state1 is not state2

        # Modifying one shouldn't affect the other
        state1['inbox'].append('test')
        assert state1['inbox'] != state2['inbox']


class TestMailboxProjectionBuilderAbstractMethods:
    """Test that abstract methods are implemented but only return current_state for now."""

    @pytest.fixture
    def builder(self):
        """Provide a MailboxProjectionBuilder instance."""
        return MailboxProjectionBuilder()

    @pytest.fixture
    def sample_event_data(self):
        """Provide sample event data for testing."""
        return {
            'from_agent': 'agent-1',
            'to_agent': 'agent-2',
            'content': 'Test message',
            'priority': 'normal',
            'correlation_id': 'test-correlation-123'
        }

    @pytest.fixture
    def sample_current_state(self):
        """Provide sample current state for testing."""
        return {
            'inbox': [],
            'outbox': [],
            'conversation_history': []
        }

    def test_apply_agent_message_sent_returns_state(self, builder, sample_event_data, sample_current_state):
        """Test apply_agent_message_sent method exists and returns state (basic implementation)."""
        result = builder.apply_agent_message_sent(sample_event_data, sample_current_state)
        assert isinstance(result, dict)
        # For now, just verify it returns a dict - actual logic tested in future features

    def test_apply_agent_message_acknowledged_returns_state(self, builder, sample_event_data, sample_current_state):
        """Test apply_agent_message_acknowledged method exists and returns state."""
        ack_data = {
            'correlation_id': 'test-correlation-123',
            'from_agent': 'agent-2',
            'acknowledged_at': '2024-01-01T00:00:00Z'
        }
        result = builder.apply_agent_message_acknowledged(ack_data, sample_current_state)
        assert isinstance(result, dict)

    def test_apply_agent_message_completed_returns_state(self, builder, sample_event_data, sample_current_state):
        """Test apply_agent_message_completed method exists and returns state."""
        completed_data = {
            'correlation_id': 'test-correlation-123',
            'from_agent': 'agent-2',
            'result': 'Completed successfully',
            'success': True
        }
        result = builder.apply_agent_message_completed(completed_data, sample_current_state)
        assert isinstance(result, dict)

    def test_agent_note_methods_return_state(self, builder, sample_current_state):
        """Test that all agent note methods exist and return state."""
        note_data = {
            'agent_id': 'agent-1',
            'title': 'Test Note',
            'content': 'Note content',
            'tags': []
        }

        note_methods = [
            'apply_agent_note_observation',
            'apply_agent_note_learning',
            'apply_agent_note_decision',
            'apply_agent_note_warning',
            'apply_agent_note_accomplishment',
            'apply_agent_note_context',
            'apply_agent_note_todo',
            'apply_agent_note_question',
            'apply_agent_note_idea',
            'apply_agent_note_reflection'
        ]

        for method_name in note_methods:
            method = getattr(builder, method_name)
            result = method(note_data, sample_current_state)
            assert isinstance(result, dict), f"{method_name} should return a dict"