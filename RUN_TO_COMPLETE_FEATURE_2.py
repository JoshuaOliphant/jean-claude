#!/usr/bin/env python
"""
Complete Feature 2 (beads-cli-wrapper) - Final Verification and State Update

This script:
1. Verifies the fetch_beads_task() implementation exists
2. Runs all tests for feature 2
3. Updates state.json to mark feature as complete
4. Provides summary and next steps

Run this script to complete Feature 2 and move to Feature 3.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import pytest
import inspect

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")

def print_success(text):
    """Print success message."""
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    """Print error message."""
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    """Print info message."""
    print(f"{BLUE}ℹ️  {text}{RESET}")

def verify_implementation():
    """Verify that fetch_beads_task() is properly implemented."""
    print_header("STEP 1: VERIFYING IMPLEMENTATION")

    try:
        from jean_claude.core.beads import fetch_beads_task, BeadsTask
        print_success("Imported fetch_beads_task successfully")
    except ImportError as e:
        print_error(f"Failed to import: {e}")
        return False

    # Check function signature
    sig = inspect.signature(fetch_beads_task)
    print_success(f"Function signature verified: {sig}")

    # Check implementation details
    source = inspect.getsource(fetch_beads_task)

    checks = {
        "subprocess.run": "Executes subprocess",
        "json.loads": "Parses JSON",
        "CalledProcessError": "Handles command failures",
        "JSONDecodeError": "Handles invalid JSON",
        "ValueError": "Validates input",
        "BeadsTask(": "Creates BeadsTask instance"
    }

    print("\nImplementation checks:")
    all_checks_passed = True
    for check, description in checks.items():
        if check in source:
            print_success(f"  {description}")
        else:
            print_error(f"  {description}")
            all_checks_passed = False

    if all_checks_passed:
        print_success("\nAll implementation checks passed!")
        return True
    else:
        print_error("\nSome implementation checks failed!")
        return False

def run_tests():
    """Run Feature 2 tests."""
    print_header("STEP 2: RUNNING TESTS")

    test_file = "tests/core/test_beads_cli_wrapper.py"
    if not Path(test_file).exists():
        print_error(f"Test file not found: {test_file}")
        return False

    print_info(f"Running tests from {test_file}...")

    exit_code = pytest.main([
        test_file,
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])

    if exit_code == 0:
        print_success("\nAll tests passed!")
        return True
    else:
        print_error("\nSome tests failed!")
        return False

def update_state(state_file_path):
    """Update state.json to mark Feature 2 as complete."""
    print_header("STEP 3: UPDATING STATE")

    state_path = Path(state_file_path)
    if not state_path.exists():
        print_error(f"State file not found: {state_file_path}")
        return False

    # Read current state
    print_info(f"Reading state from {state_file_path}...")
    with open(state_path, 'r') as f:
        state = json.load(f)

    # Find the beads-cli-wrapper feature
    feature_index = None
    for i, feature in enumerate(state['features']):
        if feature['name'] == 'beads-cli-wrapper':
            feature_index = i
            break

    if feature_index is None:
        print_error("Could not find beads-cli-wrapper feature in state.json")
        print_info("Available features:")
        for i, f in enumerate(state['features']):
            print(f"  {i}: {f['name']} (status: {f['status']})")
        return False

    feature = state['features'][feature_index]
    print_info(f"Found feature at index {feature_index}: {feature['name']}")

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

    # Update current_feature_index to next feature
    state['current_feature_index'] = feature_index + 1

    # Write updated state
    print_info("Writing updated state...")
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)

    print_success("State updated successfully!")
    print(f"\n  Feature: {feature['name']}")
    print(f"  Status: {feature['status']}")
    print(f"  Tests Passing: {feature['tests_passing']}")
    print(f"  Completed At: {feature['completed_at']}")
    print(f"  Current Feature Index: {state['current_feature_index']}")

    # Show next feature
    if state['current_feature_index'] < len(state['features']):
        next_feature = state['features'][state['current_feature_index']]
        print(f"\n{YELLOW}Next Feature:{RESET}")
        print(f"  Name: {next_feature['name']}")
        print(f"  Description: {next_feature['description'][:100]}...")
    else:
        print_success("\n🎉 All features complete!")

    return True

def main():
    """Main execution function."""
    print_header("FEATURE 2 (beads-cli-wrapper) - COMPLETION SCRIPT")

    # Step 1: Verify implementation
    if not verify_implementation():
        print_error("\nImplementation verification failed!")
        return 1

    # Step 2: Run tests
    if not run_tests():
        print_error("\nTests failed! Not updating state.")
        return 1

    # Step 3: Update state
    # Try to find the state file in the standard location
    state_file_path = "agents/beads-jean_claude-2sz.3/state.json"

    if not update_state(state_file_path):
        print_error("\nFailed to update state!")
        return 1

    # Final summary
    print_header("✅ FEATURE 2 COMPLETE!")

    print("Summary:")
    print_success("  Implementation verified")
    print_success("  All tests passing")
    print_success("  State updated")
    print()
    print(f"{BOLD}You can now proceed to Feature 3{RESET}")

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Operation cancelled by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
