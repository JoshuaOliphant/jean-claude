#!/usr/bin/env python3
"""Comprehensive verification script for beads-status-updater feature.

This script:
1. Runs existing feature tests to ensure nothing is broken
2. Runs new status updater tests
3. Reports overall status
"""

import subprocess
import sys

def run_test_file(test_file, description):
    """Run a single test file and return True if all tests pass."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"File: {test_file}")
    print('='*60)

    result = subprocess.run(
        ["python", "-m", "pytest", test_file, "-v"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        print(f"\n❌ FAILED: {test_file}")
        return False
    else:
        print(f"\n✅ PASSED: {test_file}")
        return True

def main():
    """Run comprehensive verification."""
    print("\n" + "="*60)
    print("BEADS STATUS UPDATER FEATURE VERIFICATION")
    print("="*60)

    # Track test results
    all_passed = True

    # Step 1: Run existing feature tests
    print("\n\nSTEP 1: Verify existing features still work")
    print("-"*60)

    existing_tests = [
        ("tests/core/test_beads_data_model.py", "Feature 1: Beads Data Model"),
        ("tests/core/test_beads_cli_wrapper.py", "Feature 2: Beads CLI Wrapper"),
    ]

    for test_file, description in existing_tests:
        if not run_test_file(test_file, description):
            all_passed = False
            print(f"\n⚠️  ERROR: Existing test failed: {test_file}")
            print("You must fix this before proceeding to new feature!")
            return False

    # Step 2: Run new status updater tests
    print("\n\nSTEP 2: Verify new status updater feature")
    print("-"*60)

    if not run_test_file(
        "tests/core/test_beads_status_updater.py",
        "Feature 3: Beads Status Updater"
    ):
        all_passed = False

    # Final report
    print("\n\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)

    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nFeature Status:")
        print("  ✅ Feature 1 (beads-data-model): PASSING")
        print("  ✅ Feature 2 (beads-cli-wrapper): PASSING")
        print("  ✅ Feature 3 (beads-status-updater): PASSING")
        print("\n🎉 Feature beads-status-updater is complete and ready!")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease review the failures above and fix them.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
