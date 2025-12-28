#!/usr/bin/env python3
"""Run post_tool_use_hook tests."""

import subprocess
import sys

# Run the tests
result = subprocess.run(
    ["python", "-m", "pytest", "tests/orchestration/test_post_tool_use_hook.py", "-v"],
    capture_output=True,
    text=True
)

print(result.stdout)
print(result.stderr)

sys.exit(result.returncode)
