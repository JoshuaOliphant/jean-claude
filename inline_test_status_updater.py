#!/usr/bin/env python3
"""Inline test to verify status updater functionality without pytest."""

import subprocess
from unittest.mock import Mock, patch

def test_update_beads_status():
    """Test update_beads_status function."""
    from jean_claude.core.beads import update_beads_status

    print("\n" + "="*60)
    print("Testing update_beads_status()")
    print("="*60)

    # Test 1: Successful status update
    print("\nTest 1: Successful status update to in_progress")
    mock_result = Mock()
    mock_result.returncode = 0

    with patch('subprocess.run', return_value=mock_result) as mock_run:
        try:
            update_beads_status("test-123", "in_progress")
            print("✅ PASS: Status update executed successfully")

            # Verify the command
            call_args = mock_run.call_args
            expected_cmd = ['bd', 'update', '--status', 'in_progress', 'test-123']
            actual_cmd = call_args[0][0]
            if actual_cmd == expected_cmd:
                print(f"✅ PASS: Command correct: {actual_cmd}")
            else:
                print(f"❌ FAIL: Expected {expected_cmd}, got {actual_cmd}")
                return False
        except Exception as e:
            print(f"❌ FAIL: {e}")
            return False

    # Test 2: Empty task_id raises ValueError
    print("\nTest 2: Empty task_id raises ValueError")
    try:
        update_beads_status("", "in_progress")
        print("❌ FAIL: Should have raised ValueError")
        return False
    except ValueError as e:
        if "task_id cannot be empty" in str(e):
            print(f"✅ PASS: Correct ValueError raised: {e}")
        else:
            print(f"❌ FAIL: Wrong error message: {e}")
            return False

    # Test 3: Invalid status raises ValueError
    print("\nTest 3: Invalid status raises ValueError")
    try:
        update_beads_status("test-123", "invalid_status")
        print("❌ FAIL: Should have raised ValueError")
        return False
    except ValueError as e:
        if "Invalid status" in str(e):
            print(f"✅ PASS: Correct ValueError raised: {e}")
        else:
            print(f"❌ FAIL: Wrong error message: {e}")
            return False

    # Test 4: Command error raises RuntimeError
    print("\nTest 4: Command error raises RuntimeError")
    with patch('subprocess.run', side_effect=subprocess.CalledProcessError(
        returncode=1,
        cmd=['bd', 'update', '--status', 'in_progress', 'invalid-id'],
        stderr="Error: Task not found"
    )):
        try:
            update_beads_status("invalid-id", "in_progress")
            print("❌ FAIL: Should have raised RuntimeError")
            return False
        except RuntimeError as e:
            if "Failed to update status" in str(e):
                print(f"✅ PASS: Correct RuntimeError raised: {e}")
            else:
                print(f"❌ FAIL: Wrong error message: {e}")
                return False

    print("\n✅ All update_beads_status tests passed!")
    return True


def test_close_beads_task():
    """Test close_beads_task function."""
    from jean_claude.core.beads import close_beads_task

    print("\n" + "="*60)
    print("Testing close_beads_task()")
    print("="*60)

    # Test 1: Successful task close
    print("\nTest 1: Successful task close")
    mock_result = Mock()
    mock_result.returncode = 0

    with patch('subprocess.run', return_value=mock_result) as mock_run:
        try:
            close_beads_task("test-123")
            print("✅ PASS: Task close executed successfully")

            # Verify the command
            call_args = mock_run.call_args
            expected_cmd = ['bd', 'close', 'test-123']
            actual_cmd = call_args[0][0]
            if actual_cmd == expected_cmd:
                print(f"✅ PASS: Command correct: {actual_cmd}")
            else:
                print(f"❌ FAIL: Expected {expected_cmd}, got {actual_cmd}")
                return False
        except Exception as e:
            print(f"❌ FAIL: {e}")
            return False

    # Test 2: Empty task_id raises ValueError
    print("\nTest 2: Empty task_id raises ValueError")
    try:
        close_beads_task("")
        print("❌ FAIL: Should have raised ValueError")
        return False
    except ValueError as e:
        if "task_id cannot be empty" in str(e):
            print(f"✅ PASS: Correct ValueError raised: {e}")
        else:
            print(f"❌ FAIL: Wrong error message: {e}")
            return False

    # Test 3: Command error raises RuntimeError
    print("\nTest 3: Command error raises RuntimeError")
    with patch('subprocess.run', side_effect=subprocess.CalledProcessError(
        returncode=1,
        cmd=['bd', 'close', 'invalid-id'],
        stderr="Error: Task not found"
    )):
        try:
            close_beads_task("invalid-id")
            print("❌ FAIL: Should have raised RuntimeError")
            return False
        except RuntimeError as e:
            if "Failed to close task" in str(e):
                print(f"✅ PASS: Correct RuntimeError raised: {e}")
            else:
                print(f"❌ FAIL: Wrong error message: {e}")
                return False

    print("\n✅ All close_beads_task tests passed!")
    return True


def main():
    """Run all inline tests."""
    print("\n" + "="*60)
    print("INLINE STATUS UPDATER TESTS")
    print("="*60)

    # Test imports first
    try:
        from jean_claude.core.beads import update_beads_status, close_beads_task
        print("\n✅ Successfully imported functions")
    except ImportError as e:
        print(f"\n❌ Failed to import: {e}")
        return False

    # Run tests
    all_passed = True

    if not test_update_beads_status():
        all_passed = False

    if not test_close_beads_task():
        all_passed = False

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nThe beads-status-updater feature is working correctly!")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
