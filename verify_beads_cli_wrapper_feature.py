#!/usr/bin/env python
"""Verify beads CLI wrapper feature implementation.

This script verifies:
1. The fetch_beads_task() function exists and is importable
2. The test file exists at the correct location
3. All tests pass
"""

import sys
import os
from pathlib import Path

def verify_implementation():
    """Verify the fetch_beads_task implementation exists."""
    print("="*60)
    print("STEP 1: Verifying implementation...")
    print("="*60)

    try:
        from jean_claude.core.beads import fetch_beads_task
        print("✅ fetch_beads_task() function is importable")

        # Check function signature
        import inspect
        sig = inspect.signature(fetch_beads_task)
        print(f"   Function signature: {sig}")

        # Check docstring
        if fetch_beads_task.__doc__:
            print(f"   Docstring present: Yes")
        else:
            print(f"   ⚠️  Docstring present: No")

        return True
    except ImportError as e:
        print(f"❌ Failed to import fetch_beads_task: {e}")
        return False

def verify_test_file():
    """Verify the test file exists."""
    print("\n" + "="*60)
    print("STEP 2: Verifying test file...")
    print("="*60)

    test_file = Path("tests/core/test_beads_cli_wrapper.py")

    if test_file.exists():
        print(f"✅ Test file exists: {test_file}")

        # Count test functions
        with open(test_file, 'r') as f:
            content = f.read()
            test_count = content.count("def test_")
            print(f"   Number of test functions: {test_count}")

        return True
    else:
        print(f"❌ Test file not found: {test_file}")
        return False

def run_tests():
    """Run the tests."""
    print("\n" + "="*60)
    print("STEP 3: Running tests...")
    print("="*60)

    try:
        import pytest

        exit_code = pytest.main([
            "tests/core/test_beads_cli_wrapper.py",
            "-v",
            "--tb=short"
        ])

        if exit_code == 0:
            print("\n✅ All tests passed!")
            return True
        else:
            print(f"\n❌ Tests failed with exit code: {exit_code}")
            return False

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def main():
    """Main verification function."""
    print("\n" + "="*70)
    print(" BEADS CLI WRAPPER FEATURE VERIFICATION")
    print("="*70 + "\n")

    results = []

    # Run all verification steps
    results.append(("Implementation", verify_implementation()))
    results.append(("Test File", verify_test_file()))
    results.append(("Tests", run_tests()))

    # Summary
    print("\n" + "="*70)
    print(" VERIFICATION SUMMARY")
    print("="*70)

    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:20s} {status}")
        if not passed:
            all_passed = False

    print("="*70)

    if all_passed:
        print("\n🎉 ALL VERIFICATION CHECKS PASSED!")
        print("\nThe beads-cli-wrapper feature is complete:")
        print("  - fetch_beads_task() function implemented")
        print("  - Comprehensive tests created")
        print("  - All tests passing")
        return 0
    else:
        print("\n❌ SOME VERIFICATION CHECKS FAILED")
        print("\nPlease review the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
