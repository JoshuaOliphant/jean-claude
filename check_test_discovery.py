#!/usr/bin/env python
"""Check if pytest can discover the new test file."""

import sys
import subprocess

# Just collect tests without running them
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "tests/test_interactive_prompt.py",
    "--collect-only", "-q"
], capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")

if result.returncode == 0:
    print("\n✓ Test discovery successful!")
else:
    print("\n✗ Test discovery failed!")
    sys.exit(1)
