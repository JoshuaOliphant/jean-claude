#!/usr/bin/env python
"""Verify BeadsClient implementation by importing and running basic checks."""

import sys
import traceback

def verify_beads_client():
    """Verify BeadsClient can be imported and has required methods."""
    try:
        print("=" * 60)
        print("VERIFYING BEADS CLIENT IMPLEMENTATION")
        print("=" * 60)

        # Import the module
        print("\n1. Importing BeadsClient...")
        from jean_claude.core.beads import BeadsClient, BeadsTask
        print("   ✅ Successfully imported BeadsClient and BeadsTask")

        # Verify BeadsClient can be instantiated
        print("\n2. Instantiating BeadsClient...")
        client = BeadsClient()
        print("   ✅ Successfully instantiated BeadsClient")

        # Verify methods exist
        print("\n3. Checking required methods...")
        required_methods = ['fetch_task', 'update_status', 'close_task']
        for method in required_methods:
            if not hasattr(client, method):
                print(f"   ❌ Missing method: {method}")
                return False
            if not callable(getattr(client, method)):
                print(f"   ❌ Method not callable: {method}")
                return False
            print(f"   ✅ Method exists and is callable: {method}")

        # Verify BeadsTask model
        print("\n4. Checking BeadsTask model...")
        print("   ✅ BeadsTask model is available")

        print("\n" + "=" * 60)
        print("✅ BEADS CLIENT VERIFICATION PASSED!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_beads_client()
    sys.exit(0 if success else 1)
