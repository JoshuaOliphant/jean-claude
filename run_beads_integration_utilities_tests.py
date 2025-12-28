#!/usr/bin/env python
"""Run beads-integration-utilities tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run beads integration tests
    exit_code = pytest.main([
        "tests/core/test_beads.py",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL BEADS INTEGRATION UTILITIES TESTS PASSED!")
        print("="*60)
        print("\nVerified functionality:")
        print("  - fetch_beads_task(task_id)")
        print("  - update_beads_status(task_id, status)")
        print("  - close_beads_task(task_id)")
        print("  - Error handling for missing bd command")
        print("  - Error handling for invalid task IDs")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME BEADS INTEGRATION UTILITIES TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
