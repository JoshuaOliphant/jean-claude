#!/usr/bin/env python3
"""Quick test runner for CommitBodyGenerator tests."""

import subprocess
import sys

def main():
    """Run the CommitBodyGenerator tests."""
    result = subprocess.run(
        ['python', '-m', 'pytest', 'tests/test_commit_body_generator.py', '-v'],
        capture_output=False,
        text=True
    )
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()
