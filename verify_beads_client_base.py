#!/usr/bin/env python3
"""Verify the BeadsClient base implementation."""

import sys

def main():
    """Verify BeadsClient implementation."""
    print("Verifying BeadsClient base implementation...")

    try:
        # Import the BeadsClient
        from jean_claude.core.beads import BeadsClient

        # Create a client instance
        client = BeadsClient()

        # Check that _run_bd_command method exists
        if not hasattr(client, '_run_bd_command'):
            print("❌ BeadsClient missing _run_bd_command method")
            return False

        # Check that it's callable
        if not callable(client._run_bd_command):
            print("❌ _run_bd_command is not callable")
            return False

        # Check method signature
        import inspect
        sig = inspect.signature(client._run_bd_command)
        params = list(sig.parameters.keys())

        if 'args' not in params:
            print("❌ _run_bd_command missing 'args' parameter")
            return False

        print("✅ BeadsClient has _run_bd_command method")
        print("✅ _run_bd_command is callable")
        print(f"✅ _run_bd_command signature: {sig}")

        # Check all expected methods exist
        expected_methods = ['fetch_task', 'update_status', 'close_task', 'parse_task_json', '_run_bd_command']
        for method in expected_methods:
            if not hasattr(client, method):
                print(f"❌ BeadsClient missing {method} method")
                return False
            if not callable(getattr(client, method)):
                print(f"❌ {method} is not callable")
                return False

        print(f"✅ All expected methods exist: {', '.join(expected_methods)}")

        print("\n✅ BeadsClient base implementation verified successfully!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
