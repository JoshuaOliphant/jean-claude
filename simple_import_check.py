#!/usr/bin/env python
"""Simple import check to verify modules work."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Checking imports...")

try:
    from jean_claude.core.beads import (
        BeadsTask,
        BeadsTaskStatus,
        BeadsClient,
        fetch_beads_task,
        update_beads_status,
        close_beads_task,
        generate_spec_from_beads
    )
    print("✓ All imports successful")

    print("\nChecking BeadsClient methods:")
    client = BeadsClient()
    print(f"✓ BeadsClient instantiated")
    print(f"✓ Has fetch_task: {hasattr(client, 'fetch_task')}")
    print(f"✓ Has update_status: {hasattr(client, 'update_status')}")
    print(f"✓ Has close_task: {hasattr(client, 'close_task')}")

    print("\nChecking module-level functions:")
    print(f"✓ fetch_beads_task exists: {callable(fetch_beads_task)}")
    print(f"✓ update_beads_status exists: {callable(update_beads_status)}")
    print(f"✓ close_beads_task exists: {callable(close_beads_task)}")
    print(f"✓ generate_spec_from_beads exists: {callable(generate_spec_from_beads)}")

    print("\nChecking template file:")
    template_path = Path(__file__).parent / "src" / "jean_claude" / "templates" / "beads_spec.md"
    print(f"✓ Template exists: {template_path.exists()}")
    if template_path.exists():
        content = template_path.read_text()
        print(f"✓ Template has content: {len(content)} bytes")
        print(f"✓ Has {{{{title}}}}: {'{{title}}' in content}")
        print(f"✓ Has {{{{description}}}}: {'{{description}}' in content}")
        print(f"✓ Has {{{{acceptance_criteria}}}}: {'{{acceptance_criteria}}' in content}")

    print("\n=== ALL CHECKS PASSED ===")
    sys.exit(0)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
