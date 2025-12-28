#!/usr/bin/env python3
"""Quick verification script for fetch_beads_task function."""

import sys
import subprocess
import json

# Test import
try:
    from jean_claude.core.beads import fetch_beads_task, BeadsTask, BeadsTaskStatus
    print("✓ Successfully imported fetch_beads_task and BeadsTask")
except ImportError as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Test that the function exists and has the right signature
print(f"✓ fetch_beads_task function exists: {callable(fetch_beads_task)}")
print(f"✓ BeadsTask class exists: {BeadsTask}")
print(f"✓ BeadsTaskStatus enum exists: {BeadsTaskStatus}")

# Quick function signature check
import inspect
sig = inspect.signature(fetch_beads_task)
print(f"✓ Function signature: {sig}")

# Verify the implementation handles basic cases
print("\nVerifying implementation details...")
source = inspect.getsource(fetch_beads_task)
checks = [
    ("subprocess.run" in source, "Uses subprocess.run"),
    ("'bd'" in source and "'show'" in source, "Calls 'bd show' command"),
    ("'--json'" in source, "Uses --json flag"),
    ("json.loads" in source, "Parses JSON output"),
    ("ValueError" in source, "Validates task_id"),
    ("RuntimeError" in source, "Handles errors"),
]

for check, description in checks:
    status = "✓" if check else "✗"
    print(f"{status} {description}")

print("\n" + "="*60)
print("Implementation verification complete!")
print("="*60)
