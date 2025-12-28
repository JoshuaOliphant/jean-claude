#!/usr/bin/env python3
"""Script to verify BeadsClient tests pass."""

import subprocess
import sys


def run_tests():
    """Run the beads client tests."""
    # First run the beads data model tests (feature 1)
    print("=" * 60)
    print("Running BeadsTask/BeadsConfig tests (Feature 1)...")
    print("=" * 60)
    result1 = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/core/test_beads_data_model.py", "-v"],
        capture_output=True,
        text=True
    )
    print(result1.stdout)
    if result1.stderr:
        print("STDERR:", result1.stderr)

    # Then run the beads client tests (feature 2)
    print("\n" + "=" * 60)
    print("Running BeadsClient tests (Feature 2)...")
    print("=" * 60)
    result2 = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/core/test_beads_client.py", "-v"],
        capture_output=True,
        text=True
    )
    print(result2.stdout)
    if result2.stderr:
        print("STDERR:", result2.stderr)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Feature 1 (BeadsTask/BeadsConfig): {'PASSED' if result1.returncode == 0 else 'FAILED'}")
    print(f"Feature 2 (BeadsClient): {'PASSED' if result2.returncode == 0 else 'FAILED'}")

    # Return 0 if both passed, 1 otherwise
    return 0 if (result1.returncode == 0 and result2.returncode == 0) else 1


if __name__ == "__main__":
    sys.exit(run_tests())
