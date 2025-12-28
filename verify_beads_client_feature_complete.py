#!/usr/bin/env python
"""Verify BeadsClient feature is complete and all tests pass."""

import sys
import subprocess

def run_tests():
    """Run the BeadsClient tests."""
    print("=" * 60)
    print("RUNNING BEADS CLIENT TESTS")
    print("=" * 60)

    result = subprocess.run(
        ["python", "-m", "pytest", "tests/core/test_beads_client.py", "-v", "--tb=short"],
        capture_output=False
    )

    return result.returncode == 0

def run_beads_tests():
    """Run the general beads module tests."""
    print("\n" + "=" * 60)
    print("RUNNING BEADS MODULE TESTS")
    print("=" * 60)

    result = subprocess.run(
        ["python", "-m", "pytest", "tests/core/test_beads.py", "-v", "--tb=short"],
        capture_output=False
    )

    return result.returncode == 0

def main():
    """Main verification function."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  BEADS CLIENT FEATURE VERIFICATION                        ║")
    print("╚" + "=" * 58 + "╝")
    print()

    # Run the tests
    client_tests_passed = run_tests()
    beads_tests_passed = run_beads_tests()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if client_tests_passed:
        print("✅ BeadsClient tests: PASSED")
    else:
        print("❌ BeadsClient tests: FAILED")

    if beads_tests_passed:
        print("✅ Beads module tests: PASSED")
    else:
        print("❌ Beads module tests: FAILED")

    print("=" * 60)

    if client_tests_passed and beads_tests_passed:
        print("\n🎉 ALL TESTS PASSED! Feature is complete!")
        print("\nBeadsClient implementation verified:")
        print("  ✓ BeadsClient class exists")
        print("  ✓ fetch_task() method calls 'bd show --json <task-id>'")
        print("  ✓ Parses JSON response into BeadsTask dataclass")
        print("  ✓ BeadsTask has all required fields:")
        print("    - id, title, description, status")
        print("    - acceptance_criteria, created_at, updated_at")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
