#!/usr/bin/env python
"""Inline verification of BeadsClient."""
import sys
sys.path.insert(0, "/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/src")

from jean_claude.core.beads import BeadsClient
client = BeadsClient()
print("✅ BeadsClient imported and instantiated successfully")
print(f"   - fetch_task: {callable(client.fetch_task)}")
print(f"   - update_status: {callable(client.update_status)}")
print(f"   - close_task: {callable(client.close_task)}")
