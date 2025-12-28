#!/usr/bin/env python3
"""Run tests for beads-data-model feature."""

import subprocess
import sys

def main():
    """Run the beads data model tests."""
    # Run tests from both test files
    result = subprocess.run(
        ['python', '-m', 'pytest',
         'tests/core/test_beads_model.py',
         'tests/core/test_beads_data_model.py',
         '-xvs'],
        capture_output=False,
        text=True
    )
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()
