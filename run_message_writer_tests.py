#!/usr/bin/env python3
"""Run message writer tests to verify implementation."""

import subprocess
import sys

def main():
    """Run the message writer tests."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/core/test_message_writer.py",
        "-xvs"
    ]

    print(f"Running: {' '.join(cmd)}")
    print("=" * 80)

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("=" * 80)
        print("✓ All message writer tests passed!")
        print("=" * 80)
    else:
        print("=" * 80)
        print("✗ Some tests failed")
        print("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    main()
