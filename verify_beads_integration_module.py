#!/usr/bin/env python3
"""Verify the beads integration module exists and has the required components."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def verify_module():
    """Verify beads integration module has required components."""
    print("Verifying beads integration module...")

    # Import the module
    try:
        from jean_claude.core.beads import (
            BeadsTask,
            fetch_beads_task,
            update_beads_status,
            close_beads_task
        )
        print("✓ Module imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import module: {e}")
        return False

    # Verify BeadsTask dataclass exists
    try:
        assert hasattr(BeadsTask, 'id')
        assert hasattr(BeadsTask, 'title')
        assert hasattr(BeadsTask, 'description')
        assert hasattr(BeadsTask, 'status')
        print("✓ BeadsTask dataclass has required fields")
    except AssertionError:
        print("✗ BeadsTask is missing required fields")
        return False

    # Verify functions exist and are callable
    try:
        assert callable(fetch_beads_task)
        assert callable(update_beads_status)
        assert callable(close_beads_task)
        print("✓ All required functions are callable")
    except AssertionError:
        print("✗ Some functions are missing or not callable")
        return False

    # Check test file exists
    test_file = Path(__file__).parent / "tests" / "core" / "test_beads.py"
    if test_file.exists():
        print(f"✓ Test file exists at {test_file}")
    else:
        print(f"✗ Test file not found at {test_file}")
        return False

    print("\n✅ All verifications passed!")
    return True

if __name__ == "__main__":
    success = verify_module()
    sys.exit(0 if success else 1)
