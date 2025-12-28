#!/usr/bin/env python3
"""Run tests for beads-data-model feature."""

import subprocess
import sys

def run_tests():
    """Run pytest for beads model tests."""
    try:
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/core/test_beads_model.py', '-v'],
            cwd='/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude',
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print(result.stderr)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
