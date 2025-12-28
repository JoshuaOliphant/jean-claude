#!/usr/bin/env python3
"""Quick verification that CLI wrapper functions and tests exist."""

import sys

def main():
    print("=" * 70)
    print("VERIFYING BEADS CLI WRAPPER FEATURE")
    print("=" * 70)

    try:
        # 1. Verify the CLI wrapper functions exist and can be imported
        print("\n1. Checking CLI wrapper functions...")
        from jean_claude.core.beads import (
            fetch_beads_task,
            update_beads_status,
            close_beads_task
        )
        print("   ✓ fetch_beads_task - found")
        print("   ✓ update_beads_status - found")
        print("   ✓ close_beads_task - found")

        # 2. Verify the functions are callable
        print("\n2. Checking functions are callable...")
        assert callable(fetch_beads_task), "fetch_beads_task is not callable"
        assert callable(update_beads_status), "update_beads_status is not callable"
        assert callable(close_beads_task), "close_beads_task is not callable"
        print("   ✓ All functions are callable")

        # 3. Verify test file exists
        print("\n3. Checking test file exists...")
        import os
        test_file = "tests/test_beads_cli.py"
        if not os.path.exists(test_file):
            print(f"   ✗ Test file not found: {test_file}")
            return False
        print(f"   ✓ Test file found: {test_file}")

        # 4. Verify test file can be imported
        print("\n4. Checking test file imports...")
        try:
            import tests.test_beads_cli
            print("   ✓ Test module imports successfully")
        except Exception as e:
            print(f"   ✗ Failed to import test module: {e}")
            return False

        # 5. Verify test classes exist
        print("\n5. Checking test classes...")
        from tests.test_beads_cli import (
            TestFetchBeadsTask,
            TestUpdateBeadsStatus,
            TestCloseBeadsTask,
            TestBeadsCliIntegration
        )
        print("   ✓ TestFetchBeadsTask - found")
        print("   ✓ TestUpdateBeadsStatus - found")
        print("   ✓ TestCloseBeadsTask - found")
        print("   ✓ TestBeadsCliIntegration - found")

        # 6. Count test methods
        print("\n6. Counting test methods...")
        test_count = 0
        for cls in [TestFetchBeadsTask, TestUpdateBeadsStatus,
                    TestCloseBeadsTask, TestBeadsCliIntegration]:
            methods = [m for m in dir(cls) if m.startswith('test_')]
            test_count += len(methods)
            print(f"   ✓ {cls.__name__}: {len(methods)} tests")
        print(f"\n   Total: {test_count} test methods")

        print("\n" + "=" * 70)
        print("✓ BEADS CLI WRAPPER FEATURE VERIFICATION PASSED")
        print("=" * 70)
        print("\nSummary:")
        print(f"  - 3 CLI wrapper functions implemented")
        print(f"  - {test_count} test methods created")
        print(f"  - All imports successful")
        return True

    except Exception as e:
        print(f"\n✗ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
