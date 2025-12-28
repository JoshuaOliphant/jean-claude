#!/usr/bin/env python3
"""Run tests for BeadsTask model verification."""

import subprocess
import sys

def run_tests():
    """Run the BeadsTask model tests."""
    print("Running BeadsTask model tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/core/test_beads_task_model.py", "-v"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
