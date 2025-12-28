#!/usr/bin/env python
"""Verify all tests pass before implementing new feature."""

import sys
import pytest

def main():
    print("=" * 70)
    print("STEP 1: Running ALL existing tests to verify baseline")
    print("=" * 70)

    # First run all existing tests
    print("\n1. Running core tests for completed features...")
    exit_code = pytest.main([
        "tests/core/test_beads_task_model.py",
        "tests/core/test_beads_fetch.py",
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])

    if exit_code != 0:
        print("\n❌ BASELINE TESTS FAILED!")
        print("Fix failing tests before proceeding to new feature implementation.")
        return exit_code

    print("\n✅ Baseline tests passed!")

    print("\n" + "=" * 70)
    print("STEP 2: Running NEW feature tests (spec-template)")
    print("=" * 70)

    # Now run the spec template tests
    print("\n2. Running spec template tests...")
    exit_code = pytest.main([
        "tests/test_spec_template.py",
        "-v",
        "--tb=short"
    ])

    if exit_code != 0:
        print("\n❌ SPEC TEMPLATE TESTS FAILED!")
        return exit_code

    print("\n✅ All tests passed!")
    print("\n" + "=" * 70)
    print("SUCCESS: All tests are passing. Feature is complete.")
    print("=" * 70)

    return 0

if __name__ == "__main__":
    sys.exit(main())
