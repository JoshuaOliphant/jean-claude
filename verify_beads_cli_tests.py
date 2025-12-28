#!/usr/bin/env python3
"""Verify that beads CLI wrapper tests pass."""

import subprocess
import sys

def main():
    """Run beads CLI tests and report results."""
    print("Running beads CLI wrapper tests...")
    print("=" * 60)

    result = subprocess.run(
        ["python", "-m", "pytest", "tests/test_beads_cli.py", "-v"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    print("=" * 60)
    if result.returncode == 0:
        print("✓ All beads CLI wrapper tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
