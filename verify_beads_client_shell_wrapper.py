#!/usr/bin/env python
"""Verify BeadsClient shell wrapper feature implementation."""

import json
import sys
from unittest.mock import MagicMock, patch


def verify_implementation():
    """Verify the BeadsClient implementation."""
    print("="*60)
    print("Verifying BeadsClient Shell Wrapper Feature")
    print("="*60)

    # Step 1: Check import
    print("\n1. Checking BeadsClient import...")
    try:
        from jean_claude.core.beads import BeadsClient, BeadsTask
        print("   ✅ BeadsClient imported successfully")
    except ImportError as e:
        print(f"   ❌ Failed to import BeadsClient: {e}")
        return False

    # Step 2: Check class exists
    print("\n2. Checking BeadsClient class...")
    try:
        client = BeadsClient()
        print("   ✅ BeadsClient instantiated successfully")
    except Exception as e:
        print(f"   ❌ Failed to instantiate BeadsClient: {e}")
        return False

    # Step 3: Check fetch_task method exists
    print("\n3. Checking fetch_task method...")
    if not hasattr(client, 'fetch_task'):
        print("   ❌ fetch_task method not found")
        return False
    if not callable(client.fetch_task):
        print("   ❌ fetch_task is not callable")
        return False
    print("   ✅ fetch_task method exists and is callable")

    # Step 4: Test fetch_task with mocked subprocess
    print("\n4. Testing fetch_task with mocked 'bd show --json' command...")
    try:
        mock_output = json.dumps([{
            "id": "test-123",
            "title": "Test Task",
            "description": "A test task for verification",
            "acceptance_criteria": ["Criterion 1", "Criterion 2"],
            "status": "open"
        }])

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout=mock_output,
                stderr="",
                returncode=0
            )

            task = client.fetch_task("test-123")

            # Verify the task was parsed correctly
            assert task.id == "test-123", f"Expected id 'test-123', got '{task.id}'"
            assert task.title == "Test Task", f"Expected title 'Test Task', got '{task.title}'"
            assert task.description == "A test task for verification"
            assert len(task.acceptance_criteria) == 2

            # Verify subprocess was called with correct arguments
            mock_run.assert_called_once_with(
                ['bd', 'show', '--json', 'test-123'],
                capture_output=True,
                text=True,
                check=True
            )

        print("   ✅ fetch_task works correctly with valid JSON response")
    except Exception as e:
        print(f"   ❌ fetch_task test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: Test error handling for empty task_id
    print("\n5. Testing error handling for empty task_id...")
    try:
        try:
            client.fetch_task("")
            print("   ❌ Should have raised ValueError for empty task_id")
            return False
        except ValueError as e:
            if "task_id cannot be empty" in str(e):
                print("   ✅ Correctly raises ValueError for empty task_id")
            else:
                print(f"   ❌ ValueError has wrong message: {e}")
                return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

    # Step 6: Test error handling for invalid JSON
    print("\n6. Testing error handling for invalid JSON...")
    try:
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="Not valid JSON",
                stderr="",
                returncode=0
            )

            try:
                client.fetch_task("test-456")
                print("   ❌ Should have raised JSONDecodeError for invalid JSON")
                return False
            except json.JSONDecodeError:
                print("   ✅ Correctly raises JSONDecodeError for invalid JSON")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 7: Test error handling for missing task
    print("\n7. Testing error handling for missing task (empty array)...")
    try:
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="[]",
                stderr="",
                returncode=0
            )

            try:
                client.fetch_task("test-789")
                print("   ❌ Should have raised RuntimeError for empty array")
                return False
            except RuntimeError as e:
                if "No task found with ID" in str(e):
                    print("   ✅ Correctly raises RuntimeError for missing task")
                else:
                    print(f"   ❌ RuntimeError has wrong message: {e}")
                    return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 8: Check test file exists
    print("\n8. Checking test file exists...")
    import os
    test_file = "tests/core/test_beads_client.py"
    if os.path.exists(test_file):
        print(f"   ✅ Test file exists: {test_file}")
    else:
        print(f"   ❌ Test file not found: {test_file}")
        return False

    return True


if __name__ == "__main__":
    print("\nBeadsClient Shell Wrapper Feature Verification")
    print("=" * 60)

    success = verify_implementation()

    print("\n" + "="*60)
    if success:
        print("✅ ALL VERIFICATION CHECKS PASSED!")
        print("="*60)
        print("\nThe BeadsClient shell wrapper feature is complete:")
        print("  • BeadsClient class wraps 'bd' CLI commands")
        print("  • fetch_task() method runs 'bd show <task-id> --json'")
        print("  • Parses JSON output correctly")
        print("  • Error handling for missing tasks")
        print("  • Error handling for invalid JSON")
        print("  • Comprehensive test coverage")
        sys.exit(0)
    else:
        print("❌ VERIFICATION FAILED!")
        print("="*60)
        sys.exit(1)
