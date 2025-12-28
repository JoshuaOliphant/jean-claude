#!/usr/bin/env python
"""Verify all existing feature tests pass before proceeding."""

import sys
import pytest

def main():
    print("=" * 80)
    print("STEP 1: VERIFYING EXISTING TESTS")
    print("=" * 80)
    print()

    # Test Feature 1: BeadsTask model
    print("Testing Feature 1: beads-task-model...")
    exit_code_1 = pytest.main([
        "tests/core/test_beads_task_model.py",
        "-v",
        "--tb=short"
    ])

    if exit_code_1 != 0:
        print("\n❌ Feature 1 tests FAILED!")
        return 1

    print("\n✅ Feature 1 tests PASSED!")
    print()

    # Test Feature 2: fetch_beads_task CLI wrapper
    print("Testing Feature 2: beads-cli-wrapper...")
    exit_code_2 = pytest.main([
        "tests/core/test_beads_cli_wrapper.py",
        "-v",
        "--tb=short"
    ])

    if exit_code_2 != 0:
        print("\n❌ Feature 2 tests FAILED!")
        return 1

    print("\n✅ Feature 2 tests PASSED!")
    print()

    print("=" * 80)
    print("✅ ALL EXISTING TESTS PASSED!")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(main())
