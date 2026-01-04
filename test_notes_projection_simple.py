#!/usr/bin/env python3
"""Simple test script to validate NotesProjectionBuilder functionality."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_tests():
    """Run basic tests for NotesProjectionBuilder."""
    try:
        # Test 1: Import
        from jean_claude.core.notes_projection_builder import NotesProjectionBuilder
        from jean_claude.core.projection_builder import ProjectionBuilder
        print("✓ Successfully imported NotesProjectionBuilder and ProjectionBuilder")

        # Test 2: Instantiation
        builder = NotesProjectionBuilder()
        print("✓ Successfully instantiated NotesProjectionBuilder")

        # Test 3: Inheritance
        assert isinstance(builder, ProjectionBuilder), "NotesProjectionBuilder should inherit from ProjectionBuilder"
        print("✓ NotesProjectionBuilder correctly inherits from ProjectionBuilder")

        # Test 4: Initial state creation
        initial_state = builder.create_initial_state()
        print(f"✓ Successfully created initial state: {initial_state}")

        # Test 5: State structure validation
        expected_keys = {'notes', 'by_category', 'by_agent', 'by_tag'}
        actual_keys = set(initial_state.keys())
        assert actual_keys == expected_keys, f"Expected keys {expected_keys}, got {actual_keys}"
        print("✓ Initial state has correct structure")

        # Test 6: Empty structures validation
        assert initial_state['notes'] == [], "notes should be empty list"
        assert initial_state['by_category'] == {}, "by_category should be empty dict"
        assert initial_state['by_agent'] == {}, "by_agent should be empty dict"
        assert initial_state['by_tag'] == {}, "by_tag should be empty dict"
        print("✓ Initial state contains correct empty structures")

        # Test 7: Independent state creation
        state1 = builder.create_initial_state()
        state2 = builder.create_initial_state()
        assert state1 == state2, "States should be equal"
        assert state1 is not state2, "States should be independent objects"
        print("✓ Multiple calls return independent but equal states")

        # Test 8: State independence verification
        state1['notes'].append('test_note')
        assert state1['notes'] != state2['notes'], "Modifying one state should not affect another"
        print("✓ States are truly independent")

        # Test 9: Method existence validation
        required_methods = [
            'apply_agent_message_sent',
            'apply_agent_message_acknowledged',
            'apply_agent_message_completed',
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

        for method_name in required_methods:
            assert hasattr(builder, method_name), f"Method {method_name} should exist"
            assert callable(getattr(builder, method_name)), f"Method {method_name} should be callable"
        print("✓ All required abstract methods are present and callable")

        # Test 10: Method behavior validation
        test_state = {'notes': [], 'by_category': {}}
        test_event_data = {'agent_id': 'test-agent', 'title': 'Test Note'}

        # Test that methods return the current state unchanged (basic implementation)
        result = builder.apply_agent_message_sent(test_event_data, test_state)
        assert result == test_state, "apply_agent_message_sent should return state unchanged"

        result = builder.apply_agent_note_observation(test_event_data, test_state)
        assert result == test_state, "apply_agent_note_observation should return state unchanged"
        print("✓ Abstract method implementations return state unchanged as expected")

        print("\n🎉 All tests passed! NotesProjectionBuilder implementation is working correctly.")
        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)