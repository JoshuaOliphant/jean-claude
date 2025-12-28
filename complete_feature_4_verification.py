#!/usr/bin/env python3
"""Complete verification for Feature 4: test-runner-validator."""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime


def run_script(script_name, description):
    """Run a verification script and return success status."""
    print(f"\n{'=' * 70}")
    print(f"Step: {description}")
    print(f"Script: {script_name}")
    print(f"{'=' * 70}\n")

    result = subprocess.run(
        [sys.executable, script_name],
        capture_output=False
    )

    if result.returncode == 0:
        print(f"\n✅ {description} - PASSED")
        return True
    else:
        print(f"\n❌ {description} - FAILED")
        return False


def update_state_file(state_path):
    """Update the state.json file to mark feature 4 as complete."""
    print(f"\n{'=' * 70}")
    print("Updating state.json")
    print(f"{'=' * 70}\n")

    try:
        # Read current state
        with open(state_path, 'r') as f:
            state = json.load(f)

        # Update feature 4
        feature = state["features"][3]  # Index 3 is feature 4
        feature["status"] = "completed"
        feature["tests_passing"] = True
        feature["completed_at"] = datetime.now().isoformat()

        if feature["started_at"] is None:
            feature["started_at"] = datetime.now().isoformat()

        # Update workflow state
        state["current_feature_index"] = 4  # Move to next feature
        state["updated_at"] = datetime.now().isoformat()

        # Write updated state
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)

        print(f"✅ Updated state.json:")
        print(f"   - Feature: {feature['name']}")
        print(f"   - Status: {feature['status']}")
        print(f"   - Tests passing: {feature['tests_passing']}")
        print(f"   - Completed at: {feature['completed_at']}")
        print(f"   - Current feature index: {state['current_feature_index']}")

        return True

    except Exception as e:
        print(f"❌ Failed to update state.json: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run complete verification for feature 4."""
    print("\n" + "=" * 70)
    print("FEATURE 4 COMPLETE VERIFICATION")
    print("Feature: test-runner-validator")
    print("=" * 70)

    all_passed = True

    # Step 1: Verify imports and basic structure
    if not run_script("verify_test_runner_validator.py", "Verify implementation structure"):
        all_passed = False

    # Step 2: Run manual tests
    if not run_script("manual_test_validator.py", "Run manual functionality tests"):
        all_passed = False

    # Step 3: Run full pytest suite
    if not run_script("run_test_runner_validator_tests.py", "Run full pytest test suite"):
        all_passed = False

    # Final summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    if all_passed:
        print("\n✅ ALL VERIFICATION STEPS PASSED!")
        print("\nFeature 4 (test-runner-validator) is complete and ready.")

        # Update state file
        state_path = Path("/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/agents/beads-jean_claude-2sz.8/state.json")

        if state_path.exists():
            if update_state_file(state_path):
                print("\n✅ State file updated successfully!")
            else:
                print("\n⚠️  Warning: Could not update state file automatically")
                print("Please update manually:")
                print("  - Set feature 4 status to 'completed'")
                print("  - Set tests_passing to true")
                print("  - Increment current_feature_index to 4")
        else:
            print(f"\n⚠️  State file not found at: {state_path}")
            print("Please update state manually if needed.")

        print("\n" + "=" * 70)
        print("🎉 FEATURE 4 COMPLETE! 🎉")
        print("=" * 70)
        return 0
    else:
        print("\n❌ SOME VERIFICATION STEPS FAILED")
        print("Please review the errors above and fix them before marking complete.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
