#!/usr/bin/env python3
"""Verify BeadsTask data model implementation."""

import sys
import subprocess

def main():
    """Run tests for BeadsTask data model."""
    print("=" * 60)
    print("VERIFYING BEADS DATA MODEL FEATURE")
    print("=" * 60)
    print()

    # Run the model tests
    print("Running BeadsTask model tests...")
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/core/test_beads_model.py", "-v"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Feature is complete!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED - Feature needs work")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
