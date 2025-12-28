#!/usr/bin/env python
"""Run the BeadsTask model tests."""

import sys
import subprocess

if __name__ == "__main__":
    # Run the BeadsTask model tests
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/core/test_beads_model.py", "-v"],
        capture_output=False
    )

    sys.exit(result.returncode)
