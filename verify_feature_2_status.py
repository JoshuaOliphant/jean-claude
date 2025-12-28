#!/usr/bin/env python
"""Verify feature 2 (beads-cli-wrapper) implementation and tests."""

import sys
import subprocess

def main():
    print("=" * 80)
    print("VERIFYING FEATURE 2: beads-cli-wrapper")
    print("=" * 80)
    print()

    # Run the beads_cli_wrapper tests
    print("Running tests for beads-cli-wrapper...")
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/core/test_beads_cli_wrapper.py", "-v"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode == 0:
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED - Feature 2 is complete!")
        print("=" * 80)
        return 0
    else:
        print("\n" + "=" * 80)
        print("✗ TESTS FAILED - Need to fix issues")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())
