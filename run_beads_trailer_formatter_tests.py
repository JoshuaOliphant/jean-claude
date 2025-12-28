#!/usr/bin/env python
"""Quick test runner for BeadsTrailerFormatter tests."""

import subprocess
import sys

if __name__ == "__main__":
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/test_beads_trailer_formatter.py", "-v"],
        cwd=".",
    )
    sys.exit(result.returncode)
