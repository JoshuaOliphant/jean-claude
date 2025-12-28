#!/usr/bin/env python3
"""Run description validation tests."""

import subprocess
import sys

def main():
    """Run the description validation tests."""
    print("Running description validation tests...")
    print()

    # Run pytest on the description validation test file
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/test_description_validation.py", "-v"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode == 0:
        print("\n✓ All description validation tests passed!")
    else:
        print("\n✗ Some tests failed")

    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
