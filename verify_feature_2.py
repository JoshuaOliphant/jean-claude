#!/usr/bin/env python
"""Verify feature 2 (beads-cli-integration) implementation and tests."""

import sys
import subprocess

def main():
    print("=" * 80)
    print("VERIFYING FEATURE 2: beads-cli-integration")
    print("=" * 80)
    print()

    # Run the tests for feature 2
    print("Running tests from tests/core/test_beads_fetch.py...")
    print("-" * 80)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/core/test_beads_fetch.py", "-v", "--tb=short"],
        capture_output=False
    )

    print()
    print("=" * 80)

    if result.returncode == 0:
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print()
        print("Feature 2 is complete and ready to be marked as done in state.json")
        return 0
    else:
        print("❌ TESTS FAILED")
        print("=" * 80)
        print()
        print("Please fix the failing tests before marking feature 2 as complete")
        return 1

if __name__ == "__main__":
    sys.exit(main())
