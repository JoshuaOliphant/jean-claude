#!/usr/bin/env python3
"""Quick test to verify status update functions can be imported."""

import sys

def main():
    """Test importing the status update functions."""
    print("Testing imports from jean_claude.core.beads...")

    try:
        from jean_claude.core.beads import update_beads_status, close_beads_task
        print("✅ Successfully imported update_beads_status")
        print("✅ Successfully imported close_beads_task")
        print(f"\nupdate_beads_status: {update_beads_status}")
        print(f"close_beads_task: {close_beads_task}")
        print("\n✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
