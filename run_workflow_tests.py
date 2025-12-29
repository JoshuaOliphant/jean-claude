#!/usr/bin/env python3
"""Simple test runner for workflow error handling tests."""

import subprocess
import sys

if __name__ == "__main__":
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/cli/commands/test_workflow_error_handling.py",
         "-v", "--tb=short"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    print(result.stderr)
    sys.exit(result.returncode)
