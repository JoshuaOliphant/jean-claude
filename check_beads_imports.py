#!/usr/bin/env python3
"""Check that beads module imports correctly."""

import sys

try:
    print("Attempting to import beads module...")
    from jean_claude.core.beads import (
        BeadsTask,
        BeadsTaskStatus,
        BeadsConfig,
        BeadsClient,
        fetch_beads_task,
        update_beads_status,
        close_beads_task,
        generate_spec_from_beads
    )

    print("✅ Successfully imported all beads components:")
    print(f"  - BeadsTask: {BeadsTask}")
    print(f"  - BeadsTaskStatus: {BeadsTaskStatus}")
    print(f"  - BeadsConfig: {BeadsConfig}")
    print(f"  - BeadsClient: {BeadsClient}")
    print(f"  - fetch_beads_task: {fetch_beads_task}")
    print(f"  - update_beads_status: {update_beads_status}")
    print(f"  - close_beads_task: {close_beads_task}")
    print(f"  - generate_spec_from_beads: {generate_spec_from_beads}")

    print("\n✅ All imports successful - beads module is working!")
    sys.exit(0)

except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
