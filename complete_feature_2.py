#!/usr/bin/env python
"""Complete Feature 2 by verifying tests and updating state."""

import json
import sys
from datetime import datetime
from pathlib import Path
import pytest

def run_tests():
    """Run Feature 2 tests."""
    print("=" * 80)
    print("RUNNING FEATURE 2 TESTS")
    print("=" * 80)
    print()

    exit_code = pytest.main([
        "tests/core/test_beads_cli_wrapper.py",
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])

    return exit_code == 0

def update_state():
    """Update the state.json file to mark Feature 2 as complete."""
    state_path = Path("agents/beads-jean_claude-2sz.3/state.json")

    # Read current state
    with open(state_path, 'r') as f:
        state = json.load(f)

    # Find Feature 2 (index 1, since it's the second feature)
    feature_index = 1
    feature = state['features'][feature_index]

    # Verify we're updating the correct feature
    assert feature['name'] == 'beads-cli-wrapper', \
        f"Expected beads-cli-wrapper, got {feature['name']}"

    # Update feature status
    now = datetime.now().isoformat()
    feature['status'] = 'completed'
    feature['tests_passing'] = True
    if feature['started_at'] is None:
        feature['started_at'] = now
    feature['completed_at'] = now

    # Update workflow state
    state['updated_at'] = now
    state['last_verification_at'] = now
    state['last_verification_passed'] = True
    state['verification_count'] = state.get('verification_count', 0) + 1

    # Write updated state
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)

    print()
    print("=" * 80)
    print("STATE UPDATED")
    print("=" * 80)
    print(f"Feature: {feature['name']}")
    print(f"Status: {feature['status']}")
    print(f"Tests Passing: {feature['tests_passing']}")
    print(f"Completed At: {feature['completed_at']}")
    print()

def main():
    print("=" * 80)
    print("FEATURE 2 COMPLETION PROCESS")
    print("=" * 80)
    print()

    # Step 1: Run tests
    print("Step 1: Running tests...")
    if not run_tests():
        print("\n❌ Tests failed! Not updating state.")
        return 1

    print("\n✅ All tests passed!")

    # Step 2: Update state
    print("\nStep 2: Updating state.json...")
    try:
        update_state()
    except Exception as e:
        print(f"\n❌ Failed to update state: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Summary
    print("=" * 80)
    print("✅ FEATURE 2 COMPLETE!")
    print("=" * 80)
    print()
    print("Summary:")
    print("  ✅ Implementation verified")
    print("  ✅ All tests passing")
    print("  ✅ State updated")
    print()
    print("Next feature: beads-status-updater (Feature 3)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
