#!/usr/bin/env python
"""Run interactive prompt handler tests."""

import sys
import subprocess

# Run the interactive prompt tests
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "tests/test_interactive_prompt.py",
    "-v", "--tb=short"
], capture_output=False)

sys.exit(result.returncode)
