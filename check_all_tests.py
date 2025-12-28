#!/usr/bin/env python3
"""Check all tests and report results."""

import subprocess
import sys

def run_all_tests():
    """Run all tests and report results."""
    print("="*60)
    print("Running ALL tests...")
    print("="*60)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    print("\n" + "="*60)
    if result.returncode == 0:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
        print("="*60)
        print("\nFailed tests need to be fixed before proceeding.")
    print("="*60)

    return result.returncode == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
