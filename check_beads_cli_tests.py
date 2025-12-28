#!/usr/bin/env python3
"""Quick check that beads CLI test module can be imported."""

import sys

try:
    # Try to import the test module
    import tests.test_beads_cli
    print("✓ Test module imports successfully")

    # Check that test classes exist
    from tests.test_beads_cli import (
        TestFetchBeadsTask,
        TestUpdateBeadsStatus,
        TestCloseBeadsTask,
        TestBeadsCliIntegration
    )
    print("✓ All test classes found:")
    print("  - TestFetchBeadsTask")
    print("  - TestUpdateBeadsStatus")
    print("  - TestCloseBeadsTask")
    print("  - TestBeadsCliIntegration")

    # Try importing the functions being tested
    from jean_claude.core.beads import (
        fetch_beads_task,
        update_beads_status,
        close_beads_task
    )
    print("✓ All CLI wrapper functions found:")
    print("  - fetch_beads_task")
    print("  - update_beads_status")
    print("  - close_beads_task")

    print("\n✓ All imports successful - tests should be runnable")
    sys.exit(0)

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
