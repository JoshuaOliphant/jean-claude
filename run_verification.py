#!/usr/bin/env python3
"""Quick script to verify existing tests pass."""

import subprocess
import sys

def main():
    """Run existing beads data model tests."""
    cmd = [sys.executable, "-m", "pytest", "tests/core/test_beads_data_model.py", "-v"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print(result.stdout)
    print(result.stderr)

    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
