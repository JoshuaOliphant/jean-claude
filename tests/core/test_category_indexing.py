# ABOUTME: Tests for the category indexing functionality in NotesProjectionBuilder
# ABOUTME: Tests by_category index building and maintenance during note event processing

"""Tests for category indexing functionality in NotesProjectionBuilder.

This module tests the by_category index functionality that groups notes
by their category field during event processing. It validates that the
index is properly built and maintained across different note types.

The by_category index is a core feature that enables efficient filtering
and grouping of notes by their category (observation, learning, decision, etc.).
"""

import pytest
from jean_claude.core.notes_projection_builder import NotesProjectionBuilder


class TestCategoryIndexingBasics:
    """Test basic category indexing functionality."""

    def test_empty_state_has_empty_by_category_index(self):
        """Test that initial state has empty by_category index."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        assert 'by_category' in initial_state
        assert initial_state['by_category'] == {}

    def test_single_note_creates_category_index_entry(self):
        """Test that adding a single note creates appropriate category index entry."""
        builder = NotesProjectionBuilder()
        initial_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-123",
            "title": "Test Learning",
            "content": "Test content for learning note.",
            "tags": ["test", "learning"]
        }

        result_state = builder.apply_agent_note_learning(event_data, initial_state)

        # Check by_category index
        assert 'learning' in result_state['by_category']
        assert result_state['by_category']['learning'] == [0]

    def test_multiple_notes_same_category_index_correctly(self):
        """Test that multiple notes of same category are indexed correctly."""
        builder = NotesProjectionBuilder()
        state = builder.get_initial_state()

        # Add first learning note
        event_data_1 = {
            "agent_id": "agent-123",
            "title": "First Learning",
            "content": "First learning content.",
            "tags": ["test1"]
        }
        state = builder.apply_agent_note_learning(event_data_1, state)

        # Add second learning note
        event_data_2 = {
            "agent_id": "agent-456",
            "title": "Second Learning",
            "content": "Second learning content.",
            "tags": ["test2"]
        }
        state = builder.apply_agent_note_learning(event_data_2, state)

        # Check by_category index contains both note indices
        assert 'learning' in state['by_category']
        assert state['by_category']['learning'] == [0, 1]

    def test_multiple_categories_create_separate_index_entries(self):
        """Test that different note categories create separate index entries."""
        builder = NotesProjectionBuilder()
        state = builder.get_initial_state()

        # Add learning note
        learning_data = {
            "agent_id": "agent-123",
            "title": "Test Learning",
            "content": "Learning content.",
            "tags": ["learning"]
        }
        state = builder.apply_agent_note_learning(learning_data, state)

        # Add observation note
        observation_data = {
            "agent_id": "agent-456",
            "title": "Test Observation",
            "content": "Observation content.",
            "tags": ["observation"]
        }
        state = builder.apply_agent_note_observation(observation_data, state)

        # Add decision note
        decision_data = {
            "agent_id": "agent-789",
            "title": "Test Decision",
            "content": "Decision content.",
            "tags": ["decision"]
        }
        state = builder.apply_agent_note_decision(decision_data, state)

        # Check all categories exist separately
        assert 'learning' in state['by_category']
        assert 'observation' in state['by_category']
        assert 'decision' in state['by_category']

        # Check indices are correct
        assert state['by_category']['learning'] == [0]
        assert state['by_category']['observation'] == [1]
        assert state['by_category']['decision'] == [2]


class TestCategoryIndexingAllNoteTypes:
    """Test category indexing across all note types."""

    def test_category_indexing_for_all_note_types(self):
        """Test that category indexing works for all implemented note types."""
        builder = NotesProjectionBuilder()
        state = builder.get_initial_state()

        # Test data for each note type
        note_types_data = [
            ("observation", builder.apply_agent_note_observation, {
                "agent_id": "agent-obs",
                "title": "Test Observation",
                "content": "Observation content.",
                "tags": ["obs-tag"]
            }),
            ("learning", builder.apply_agent_note_learning, {
                "agent_id": "agent-learn",
                "title": "Test Learning",
                "content": "Learning content.",
                "tags": ["learn-tag"]
            }),
            ("decision", builder.apply_agent_note_decision, {
                "agent_id": "agent-decision",
                "title": "Test Decision",
                "content": "Decision content.",
                "tags": ["decision-tag"]
            }),
            ("idea", builder.apply_agent_note_idea, {
                "agent_id": "agent-idea",
                "title": "Test Idea",
                "content": "Idea content.",
                "tags": ["idea-tag"]
            }),
            ("question", builder.apply_agent_note_question, {
                "agent_id": "agent-question",
                "title": "Test Question",
                "content": "Question content.",
                "tags": ["question-tag"]
            }),
            ("reflection", builder.apply_agent_note_reflection, {
                "agent_id": "agent-reflection",
                "title": "Test Reflection",
                "content": "Reflection content.",
                "tags": ["reflection-tag"]
            }),
            ("todo", builder.apply_agent_note_todo, {
                "agent_id": "agent-todo",
                "title": "Test Todo",
                "content": "Todo content.",
                "tags": ["todo-tag"]
            })
        ]

        # Apply each note type and verify category indexing
        for i, (category, apply_method, event_data) in enumerate(note_types_data):
            state = apply_method(event_data, state)

            # Check that category exists in index
            assert category in state['by_category']

            # Check that note index is correctly stored
            assert i in state['by_category'][category]

        # Verify all categories are present and have correct indices
        expected_categories = ["observation", "learning", "decision", "idea",
                               "question", "reflection", "todo"]
        for category in expected_categories:
            assert category in state['by_category']

        # Verify total number of notes
        assert len(state['notes']) == 7


class TestCategoryIndexingEdgeCases:
    """Test edge cases for category indexing."""

    def test_category_indexing_preserves_existing_indexes(self):
        """Test that adding notes preserves existing category indexes."""
        builder = NotesProjectionBuilder()
        state = builder.get_initial_state()

        # Add learning note
        learning_data = {
            "agent_id": "agent-123",
            "title": "First Learning",
            "content": "First learning.",
            "tags": ["test1"]
        }
        state = builder.apply_agent_note_learning(learning_data, state)

        # Verify initial state
        assert state['by_category']['learning'] == [0]

        # Add observation note
        observation_data = {
            "agent_id": "agent-456",
            "title": "Test Observation",
            "content": "Test observation.",
            "tags": ["test2"]
        }
        state = builder.apply_agent_note_observation(observation_data, state)

        # Verify learning index is preserved
        assert state['by_category']['learning'] == [0]
        assert state['by_category']['observation'] == [1]

        # Add another learning note
        learning_data_2 = {
            "agent_id": "agent-789",
            "title": "Second Learning",
            "content": "Second learning.",
            "tags": ["test3"]
        }
        state = builder.apply_agent_note_learning(learning_data_2, state)

        # Verify both learning notes are indexed
        assert state['by_category']['learning'] == [0, 2]
        assert state['by_category']['observation'] == [1]

    def test_category_indexing_handles_missing_state_keys(self):
        """Test that category indexing works when state keys are missing."""
        builder = NotesProjectionBuilder()

        # Create malformed state without by_category
        malformed_state = {
            'notes': []
            # Missing 'by_category', 'by_agent', 'by_tag'
        }

        event_data = {
            "agent_id": "agent-123",
            "title": "Test Learning",
            "content": "Test content.",
            "tags": ["test"]
        }

        result_state = builder.apply_agent_note_learning(event_data, malformed_state)

        # Should create missing keys and index properly
        assert 'by_category' in result_state
        assert 'learning' in result_state['by_category']
        assert result_state['by_category']['learning'] == [0]

    def test_category_indexing_state_immutability(self):
        """Test that category indexing preserves state immutability."""
        builder = NotesProjectionBuilder()
        original_state = builder.get_initial_state()

        event_data = {
            "agent_id": "agent-123",
            "title": "Test Learning",
            "content": "Test content.",
            "tags": ["test"]
        }

        result_state = builder.apply_agent_note_learning(event_data, original_state)

        # Original state should be unchanged
        assert original_state['by_category'] == {}
        assert len(original_state['notes']) == 0

        # Result state should have updates
        assert 'learning' in result_state['by_category']
        assert len(result_state['notes']) == 1


class TestCategoryIndexingIntegration:
    """Integration tests for category indexing functionality."""

    def test_complex_category_indexing_scenario(self):
        """Test complex scenario with multiple agents, categories, and notes."""
        builder = NotesProjectionBuilder()
        state = builder.get_initial_state()

        # Simulate complex workflow with multiple notes
        notes_to_add = [
            ("learning", builder.apply_agent_note_learning, {
                "agent_id": "researcher", "title": "Research Finding",
                "content": "Found important pattern.", "tags": ["research", "pattern"]
            }),
            ("observation", builder.apply_agent_note_observation, {
                "agent_id": "observer", "title": "System Behavior",
                "content": "System responds well.", "tags": ["behavior", "system"]
            }),
            ("decision", builder.apply_agent_note_decision, {
                "agent_id": "architect", "title": "Architecture Choice",
                "content": "Using microservices.", "tags": ["architecture", "choice"]
            }),
            ("learning", builder.apply_agent_note_learning, {
                "agent_id": "researcher", "title": "Additional Research",
                "content": "Found related pattern.", "tags": ["research", "related"]
            }),
            ("observation", builder.apply_agent_note_observation, {
                "agent_id": "tester", "title": "Test Results",
                "content": "All tests passing.", "tags": ["testing", "results"]
            }),
            ("idea", builder.apply_agent_note_idea, {
                "agent_id": "creative", "title": "New Feature Idea",
                "content": "Could add caching.", "tags": ["feature", "performance"]
            })
        ]

        # Apply all notes
        for i, (category, apply_method, event_data) in enumerate(notes_to_add):
            state = apply_method(event_data, state)

        # Verify category groupings
        assert len(state['by_category']['learning']) == 2
        assert len(state['by_category']['observation']) == 2
        assert len(state['by_category']['decision']) == 1
        assert len(state['by_category']['idea']) == 1

        # Verify specific indices
        assert state['by_category']['learning'] == [0, 3]
        assert state['by_category']['observation'] == [1, 4]
        assert state['by_category']['decision'] == [2]
        assert state['by_category']['idea'] == [5]

        # Verify total notes
        assert len(state['notes']) == 6

    def test_category_filtering_use_case(self):
        """Test that category index enables efficient filtering."""
        builder = NotesProjectionBuilder()
        state = builder.get_initial_state()

        # Add mixed notes
        mixed_notes = [
            ("learning", "First learning"),
            ("decision", "First decision"),
            ("learning", "Second learning"),
            ("observation", "First observation"),
            ("learning", "Third learning")
        ]

        for i, (note_type, title) in enumerate(mixed_notes):
            event_data = {
                "agent_id": f"agent-{i}",
                "title": title,
                "content": f"Content for {title}",
                "tags": [f"tag-{i}"]
            }

            if note_type == "learning":
                state = builder.apply_agent_note_learning(event_data, state)
            elif note_type == "decision":
                state = builder.apply_agent_note_decision(event_data, state)
            elif note_type == "observation":
                state = builder.apply_agent_note_observation(event_data, state)

        # Use category index to get learning notes
        learning_indices = state['by_category']['learning']
        learning_notes = [state['notes'][i] for i in learning_indices]

        # Verify learning notes are correctly retrieved
        assert len(learning_notes) == 3
        learning_titles = [note['title'] for note in learning_notes]
        assert "First learning" in learning_titles
        assert "Second learning" in learning_titles
        assert "Third learning" in learning_titles

        # Verify all learning notes have correct category
        for note in learning_notes:
            assert note['category'] == 'learning'