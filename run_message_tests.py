#!/usr/bin/env python
"""Quick test runner for Message model tests."""

import subprocess
import sys

# Run the Message model tests
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/core/test_message_model.py", "-v"],
    capture_output=True,
    text=True
)

print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)
