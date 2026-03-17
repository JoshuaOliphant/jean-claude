# ABOUTME: Consolidated tests for all note category handlers in NotesProjectionBuilder
# ABOUTME: Tests apply_agent_note_{category}() methods using parametrize over 7 categories

"""Consolidated tests for all note category handlers in NotesProjectionBuilder.

Replaces 7 near-identical test files (one per category) with a single parametrized
test suite. Each category handler (decision, idea, learning, observation, question,
reflection, todo) follows the same pattern, so we test the pattern once thoroughly
and verify each category's method exists and produces the correct category label.
"""

import pytest
from jean_claude.core.notes_projection_builder import NotesProjectionBuilder


# All 7 note categories and their corresponding method names
ALL_CATEGORIES = [
    "decision",
    "idea",
    "learning",
    "observation",
    "question",
    "reflection",
    "todo",
]


def _get_handler(builder, category):
    """Get the apply_agent_note_{category} method from the builder."""
    method_name = f"apply_agent_note_{category}"
    return getattr(builder, method_name)


@pytest.mark.parametrize("category", ALL_CATEGORIES)
class TestNoteHandlerAllCategories:
    """Verify each category handler exists and produces correct category output."""

    def test_adds_note_to_empty_state_with_correct_category(self, category):
        """Each category handler adds a note with the correct category label."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()
        handler = _get_handler(builder, category)

        event_data = {
            "agent_id": "agent-123",
            "title": f"Test {category.title()}",
            "content": f"This is a {category} note.",
            "tags": ["test", "category"],
            "related_file": "src/core/base.py",
            "related_feature": "feature-789",
        }

        result_state = handler(event_data, initial_state)

        assert len(result_state["notes"]) == 1
        note = result_state["notes"][0]
        assert note["agent_id"] == "agent-123"
        assert note["title"] == f"Test {category.title()}"
        assert note["content"] == f"This is a {category} note."
        assert note["category"] == category
        assert note["tags"] == ["test", "category"]
        assert note["related_file"] == "src/core/base.py"
        assert note["related_feature"] == "feature-789"
        assert "created_at" in note


# The remaining tests use "observation" as the representative category,
# since all handlers share the same implementation pattern.
REPRESENTATIVE = "observation"


class TestNoteHandlerDetailedBehavior:
    """Detailed behavior tests using a single representative category."""

    def test_adds_note_with_minimal_data(self):
        """Note with only required fields sets optional fields to None."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()
        handler = _get_handler(builder, REPRESENTATIVE)

        event_data = {
            "agent_id": "agent-789",
            "title": "Minimal Note",
            "content": "Simple content.",
            "tags": [],
        }

        result_state = handler(event_data, initial_state)

        assert len(result_state["notes"]) == 1
        note = result_state["notes"][0]
        assert note["agent_id"] == "agent-789"
        assert note["category"] == REPRESENTATIVE
        assert note["tags"] == []
        assert note["related_file"] is None
        assert note["related_feature"] is None

    def test_adds_note_to_existing_notes(self):
        """Adding a note preserves existing notes."""
        builder = NotesProjectionBuilder()
        handler = _get_handler(builder, REPRESENTATIVE)

        existing_state = {
            "notes": [
                {
                    "agent_id": "agent-001",
                    "title": "Existing Note",
                    "content": "Previous content",
                    "category": "decision",
                    "tags": ["old"],
                    "related_file": None,
                    "related_feature": None,
                    "created_at": "2024-01-01T00:00:00",
                }
            ],
            "by_category": {"decision": [0]},
            "by_agent": {"agent-001": [0]},
            "by_tag": {"old": [0]},
        }

        event_data = {
            "agent_id": "agent-456",
            "title": "New Note",
            "content": "Fresh content.",
            "tags": ["new", "important"],
        }

        result_state = handler(event_data, existing_state)

        assert len(result_state["notes"]) == 2
        assert result_state["notes"][0] == existing_state["notes"][0]
        assert result_state["notes"][1]["category"] == REPRESENTATIVE

    def test_updates_by_category_index(self):
        """by_category index is updated when adding a note."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()
        handler = _get_handler(builder, REPRESENTATIVE)

        event_data = {
            "agent_id": "agent-123",
            "title": "Test",
            "content": "Content.",
            "tags": ["test"],
        }

        result_state = handler(event_data, initial_state)

        assert REPRESENTATIVE in result_state["by_category"]
        assert result_state["by_category"][REPRESENTATIVE] == [0]

    def test_updates_by_agent_index(self):
        """by_agent index is updated when adding a note."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()
        handler = _get_handler(builder, REPRESENTATIVE)

        event_data = {
            "agent_id": "agent-456",
            "title": "Agent Note",
            "content": "Content.",
            "tags": ["test"],
        }

        result_state = handler(event_data, initial_state)

        assert "agent-456" in result_state["by_agent"]
        assert result_state["by_agent"]["agent-456"] == [0]

    def test_updates_by_tag_index(self):
        """by_tag index is updated for each tag."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()
        handler = _get_handler(builder, REPRESENTATIVE)

        event_data = {
            "agent_id": "agent-789",
            "title": "Tagged Note",
            "content": "Content.",
            "tags": ["important", "urgent", "testing"],
        }

        result_state = handler(event_data, initial_state)

        for tag in ["important", "urgent", "testing"]:
            assert tag in result_state["by_tag"]
            assert result_state["by_tag"][tag] == [0]

    def test_handles_empty_tags_list(self):
        """Empty tags list doesn't break indexing."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()
        handler = _get_handler(builder, REPRESENTATIVE)

        event_data = {
            "agent_id": "agent-999",
            "title": "No Tags",
            "content": "No tags note.",
            "tags": [],
        }

        result_state = handler(event_data, initial_state)

        assert len(result_state["notes"]) == 1
        assert result_state["notes"][0]["tags"] == []
        assert result_state["by_tag"] == {}
        assert REPRESENTATIVE in result_state["by_category"]
        assert "agent-999" in result_state["by_agent"]

    def test_preserves_original_state_immutability(self):
        """Original state is not modified (immutability)."""
        builder = NotesProjectionBuilder()
        original_state = builder.get_initial_state()
        original_notes_copy = original_state["notes"].copy()
        handler = _get_handler(builder, REPRESENTATIVE)

        event_data = {
            "agent_id": "agent-123",
            "title": "Test",
            "content": "Content.",
            "tags": ["test"],
        }

        result_state = handler(event_data, original_state)

        assert original_state["notes"] == original_notes_copy
        assert len(original_state["notes"]) == 0
        assert original_state["by_category"] == {}
        assert original_state["by_agent"] == {}
        assert original_state["by_tag"] == {}
        assert result_state is not original_state
        assert len(result_state["notes"]) == 1

    def test_updates_existing_indexes_correctly(self):
        """Existing indexes are properly updated with shared tags/agents."""
        builder = NotesProjectionBuilder()
        handler = _get_handler(builder, REPRESENTATIVE)

        initial_state = {
            "notes": [
                {
                    "agent_id": "agent-001",
                    "title": "First Note",
                    "content": "Content 1",
                    "category": "decision",
                    "tags": ["shared", "first"],
                    "related_file": None,
                    "related_feature": None,
                    "created_at": "2024-01-01T00:00:00",
                }
            ],
            "by_category": {"decision": [0]},
            "by_agent": {"agent-001": [0]},
            "by_tag": {"shared": [0], "first": [0]},
        }

        event_data = {
            "agent_id": "agent-001",
            "title": "Second Note",
            "content": "Content 2.",
            "tags": ["shared", "second"],
        }

        result_state = handler(event_data, initial_state)

        assert len(result_state["notes"]) == 2
        assert set(result_state["by_category"].keys()) == {"decision", REPRESENTATIVE}
        assert result_state["by_agent"]["agent-001"] == [0, 1]
        assert result_state["by_tag"]["shared"] == [0, 1]
        assert result_state["by_tag"]["first"] == [0]
        assert result_state["by_tag"]["second"] == [1]

    def test_note_contains_timestamp(self):
        """Notes include a created_at timestamp."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()
        handler = _get_handler(builder, REPRESENTATIVE)

        event_data = {
            "agent_id": "agent-123",
            "title": "Timestamped",
            "content": "Should have timestamp.",
            "tags": ["timestamp"],
        }

        result_state = handler(event_data, initial_state)

        note = result_state["notes"][0]
        assert "created_at" in note
        assert isinstance(note["created_at"], str)
        assert "T" in note["created_at"]


class TestNoteHandlerEdgeCases:
    """Edge cases using representative category."""

    def test_handles_malformed_state_gracefully(self):
        """Method handles missing state keys gracefully."""
        builder = NotesProjectionBuilder()
        handler = _get_handler(builder, REPRESENTATIVE)

        incomplete_state = {
            "notes": [],
            "by_category": {},
        }

        event_data = {
            "agent_id": "agent-123",
            "title": "Test",
            "content": "Content.",
            "tags": ["test"],
        }

        result_state = handler(event_data, incomplete_state)

        assert len(result_state["notes"]) == 1
        assert "by_agent" in result_state
        assert "by_tag" in result_state
        assert result_state["by_agent"]["agent-123"] == [0]
        assert result_state["by_tag"]["test"] == [0]

    def test_preserves_existing_state_structure(self):
        """Method preserves all existing state keys."""
        builder = NotesProjectionBuilder()
        handler = _get_handler(builder, REPRESENTATIVE)

        state_with_extras = {
            "notes": [],
            "by_category": {},
            "by_agent": {},
            "by_tag": {},
            "custom_field": "should_be_preserved",
            "metadata": {"version": 1},
        }

        event_data = {
            "agent_id": "agent-123",
            "title": "Test",
            "content": "Content.",
            "tags": ["test"],
        }

        result_state = handler(event_data, state_with_extras)

        assert result_state["custom_field"] == "should_be_preserved"
        assert result_state["metadata"] == {"version": 1}
        assert len(result_state["notes"]) == 1
