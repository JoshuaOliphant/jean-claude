#!/usr/bin/env python
"""Run tests for beads_client to verify implementation."""

import subprocess
import sys

def main():
    """Run the beads_client tests."""
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/core/test_beads_client.py", "-v"],
        capture_output=False,
        text=True
    )

    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
