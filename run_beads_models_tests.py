#!/usr/bin/env python
"""Run tests for the beads_models feature."""

import subprocess
import sys

def main():
    """Run the beads models tests."""
    try:
        # Run pytest on the new test file
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/test_beads_models.py', '-v'],
            capture_output=True,
            text=True
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        sys.exit(result.returncode)

    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
