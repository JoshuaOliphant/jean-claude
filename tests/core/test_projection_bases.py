# ABOUTME: Consolidated tests for MailboxProjectionBuilder and NotesProjectionBuilder base classes
# ABOUTME: Tests initialization, inheritance, state creation, and abstract method signatures

"""Consolidated tests for projection builder base classes.

Merges test_mailbox_projection_base.py and test_notes_projection_base.py into a
single parametrized test suite that validates shared structure (inheritance,
instantiation, state independence) and builder-specific state shapes.
"""

import pytest

from jean_claude.core.projection_builder import ProjectionBuilder
from jean_claude.core.mailbox_projection_builder import MailboxProjectionBuilder
from jean_claude.core.notes_projection_builder import NotesProjectionBuilder


ALL_BUILDERS = [MailboxProjectionBuilder, NotesProjectionBuilder]

# Expected initial state keys per builder
EXPECTED_KEYS = {
    MailboxProjectionBuilder: {"inbox", "outbox", "conversation_history"},
    NotesProjectionBuilder: {"notes", "by_category", "by_agent", "by_tag"},
}

# Required abstract method names shared by both builders
REQUIRED_METHODS = [
    "apply_agent_message_sent",
    "apply_agent_message_acknowledged",
    "apply_agent_message_completed",
    "apply_agent_note_observation",
    "apply_agent_note_learning",
    "apply_agent_note_decision",
    "apply_agent_note_warning",
    "apply_agent_note_accomplishment",
    "apply_agent_note_context",
    "apply_agent_note_todo",
    "apply_agent_note_question",
    "apply_agent_note_idea",
    "apply_agent_note_reflection",
]


@pytest.mark.parametrize("builder_cls", ALL_BUILDERS)
class TestProjectionBuilderShared:
    """Tests that apply to both projection builders."""

    def test_can_instantiate(self, builder_cls):
        builder = builder_cls()
        assert builder is not None

    def test_inherits_from_projection_builder(self, builder_cls):
        builder = builder_cls()
        assert isinstance(builder, ProjectionBuilder)

    def test_has_required_abstract_methods(self, builder_cls):
        builder = builder_cls()
        for method_name in REQUIRED_METHODS:
            assert hasattr(builder, method_name), f"Missing method: {method_name}"

    def test_creates_initial_state_with_correct_keys(self, builder_cls):
        builder = builder_cls()
        initial_state = builder.get_initial_state()
        assert isinstance(initial_state, dict)
        assert set(initial_state.keys()) == EXPECTED_KEYS[builder_cls]

    def test_initial_state_has_empty_collections(self, builder_cls):
        builder = builder_cls()
        initial_state = builder.get_initial_state()
        for value in initial_state.values():
            assert value == [] or value == {}

    def test_multiple_calls_return_independent_states(self, builder_cls):
        builder = builder_cls()
        state1 = builder.get_initial_state()
        state2 = builder.get_initial_state()
        assert state1 == state2
        assert state1 is not state2
        # Mutate first list/dict found in state1
        first_key = next(iter(state1))
        if isinstance(state1[first_key], list):
            state1[first_key].append("test")
        else:
            state1[first_key]["test_key"] = "test_val"
        assert state1[first_key] != state2[first_key]


class TestMailboxProjectionBuilderAbstractMethods:
    """Test mailbox-specific abstract method behavior."""

    @pytest.fixture
    def builder(self):
        return MailboxProjectionBuilder()

    @pytest.fixture
    def sample_current_state(self):
        return {"inbox": [], "outbox": [], "conversation_history": []}

    def test_apply_agent_message_sent_returns_state(self, builder, sample_current_state):
        event_data = {
            "from_agent": "agent-1",
            "to_agent": "agent-2",
            "content": "Test message",
            "priority": "normal",
            "correlation_id": "test-123",
        }
        result = builder.apply_agent_message_sent(event_data, sample_current_state)
        assert isinstance(result, dict)

    def test_apply_agent_message_acknowledged_returns_state(self, builder, sample_current_state):
        ack_data = {
            "correlation_id": "test-123",
            "from_agent": "agent-2",
            "acknowledged_at": "2024-01-01T00:00:00Z",
        }
        result = builder.apply_agent_message_acknowledged(ack_data, sample_current_state)
        assert isinstance(result, dict)

    def test_apply_agent_message_completed_returns_state(self, builder, sample_current_state):
        completed_data = {
            "correlation_id": "test-123",
            "from_agent": "agent-2",
            "result": "Completed successfully",
            "success": True,
        }
        result = builder.apply_agent_message_completed(completed_data, sample_current_state)
        assert isinstance(result, dict)

    def test_agent_note_methods_return_state(self, builder, sample_current_state):
        note_data = {"agent_id": "agent-1", "title": "Test Note", "content": "Content", "tags": []}
        note_methods = [m for m in REQUIRED_METHODS if m.startswith("apply_agent_note_")]
        for method_name in note_methods:
            method = getattr(builder, method_name)
            result = method(note_data, sample_current_state)
            assert isinstance(result, dict), f"{method_name} should return a dict"


class TestNotesProjectionBuilderSpecific:
    """Tests specific to NotesProjectionBuilder."""

    def test_indexes_are_independent_dicts(self):
        builder = NotesProjectionBuilder()
        state1 = builder.get_initial_state()
        state2 = builder.get_initial_state()
        state1["by_category"]["observation"] = []
        assert "observation" not in state2["by_category"]

    def test_has_get_initial_state_callable(self):
        builder = NotesProjectionBuilder()
        assert hasattr(builder, "get_initial_state")
        assert callable(builder.get_initial_state)

    def test_message_handlers_return_state_unchanged(self):
        builder = NotesProjectionBuilder()
        test_state = {"notes": [], "by_category": {}}
        test_event_data = {"agent_id": "test-agent", "title": "Test Note"}

        result = builder.apply_agent_message_sent(test_event_data, test_state)
        assert result == test_state
        result = builder.apply_agent_message_acknowledged(test_event_data, test_state)
        assert result == test_state
        result = builder.apply_agent_message_completed(test_event_data, test_state)
        assert result == test_state
