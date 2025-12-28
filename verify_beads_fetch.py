#!/usr/bin/env python3
"""Quick verification script to check fetch_beads_task implementation."""

import sys

try:
    # Test imports
    from jean_claude.core.beads import fetch_beads_task, BeadsTask, BeadsTaskStatus
    print("✓ All imports successful")

    # Check function signature
    import inspect
    sig = inspect.signature(fetch_beads_task)
    print(f"✓ Function signature: {sig}")

    # Check return type annotation
    annotations = inspect.get_annotations(fetch_beads_task)
    print(f"✓ Return type: {annotations.get('return', 'Not specified')}")

    # Verify it's callable
    assert callable(fetch_beads_task)
    print("✓ fetch_beads_task is callable")

    # Verify BeadsTask has required fields
    required_fields = ['id', 'title', 'description', 'status', 'acceptance_criteria']
    for field in required_fields:
        assert hasattr(BeadsTask.model_fields, field) or field in BeadsTask.model_fields
    print(f"✓ BeadsTask has all required fields: {required_fields}")

    print("\n✅ All verifications passed!")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ Verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
