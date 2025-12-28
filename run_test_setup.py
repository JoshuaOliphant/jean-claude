#!/usr/bin/env python
"""Quick test runner for test_setup.py to verify test infrastructure."""

import subprocess
import sys

if __name__ == "__main__":
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_setup.py", "-v", "--tb=short"],
        cwd=".",
    )
    sys.exit(result.returncode)
