#!/usr/bin/env python3
"""Quick test runner for message_reader tests."""

import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/core/test_message_reader.py", "-v"],
    capture_output=True,
    text=True
)

print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)
