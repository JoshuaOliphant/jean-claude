"""Simple import test for BeadsTask."""
import sys

# Try to import
try:
    from jean_claude.core.beads import BeadsTask, BeadsTaskStatus
    print("SUCCESS: Imports work")
    print(f"BeadsTask: {BeadsTask}")
    print(f"BeadsTaskStatus: {BeadsTaskStatus}")
    sys.exit(0)
except ImportError as e:
    print(f"FAILED: Import error - {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAILED: Other error - {e}")
    sys.exit(1)
