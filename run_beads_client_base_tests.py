#!/usr/bin/env python3
"""Run tests for beads-client-base feature."""

import subprocess
import sys

def main():
    """Run the BeadsClient tests."""
    print("Running BeadsClient tests...")
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/core/test_beads_client.py", "-v"],
        capture_output=False
    )

    if result.returncode == 0:
        print("\n✅ All BeadsClient tests passed!")
    else:
        print("\n❌ Some BeadsClient tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
