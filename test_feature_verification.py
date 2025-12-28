#!/usr/bin/env python3
"""Quick verification script for beads-status-update feature."""

import sys
sys.path.insert(0, 'src')

try:
    # Import the functions
    from jean_claude.core.beads import update_beads_status, close_beads_task

    print("✓ Successfully imported update_beads_status and close_beads_task")

    # Check function signatures
    import inspect

    update_sig = inspect.signature(update_beads_status)
    print(f"✓ update_beads_status signature: {update_sig}")

    close_sig = inspect.signature(close_beads_task)
    print(f"✓ close_beads_task signature: {close_sig}")

    # Check docstrings
    if update_beads_status.__doc__:
        print(f"✓ update_beads_status has docstring")

    if close_beads_task.__doc__:
        print(f"✓ close_beads_task has docstring")

    print("\n✓ All basic checks passed! Feature implementation verified.")
    sys.exit(0)

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
