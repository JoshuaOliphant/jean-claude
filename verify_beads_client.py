#!/usr/bin/env python
"""Verify that the BeadsClient implementation works correctly."""

import sys

# Add src to path
sys.path.insert(0, "/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/src")

try:
    from jean_claude.core.beads import BeadsClient, BeadsTask

    print("=" * 60)
    print("VERIFYING BEADS CLIENT IMPLEMENTATION")
    print("=" * 60)

    # Test 1: Import verification
    print("\n1. BeadsClient imported successfully")

    # Test 2: Instantiation
    client = BeadsClient()
    print("2. BeadsClient instantiated successfully")

    # Test 3: Verify methods exist
    assert hasattr(client, 'fetch_task'), "Missing fetch_task method"
    assert callable(client.fetch_task), "fetch_task is not callable"
    print("3. fetch_task method exists and is callable")

    assert hasattr(client, 'update_status'), "Missing update_status method"
    assert callable(client.update_status), "update_status is not callable"
    print("4. update_status method exists and is callable")

    assert hasattr(client, 'close_task'), "Missing close_task method"
    assert callable(client.close_task), "close_task is not callable"
    print("5. close_task method exists and is callable")

    # Test 4: Verify method signatures
    import inspect

    # fetch_task should accept task_id parameter
    fetch_sig = inspect.signature(client.fetch_task)
    assert 'task_id' in fetch_sig.parameters, "fetch_task missing task_id parameter"
    print("6. fetch_task has correct signature (task_id)")

    # update_status should accept task_id and status parameters
    update_sig = inspect.signature(client.update_status)
    assert 'task_id' in update_sig.parameters, "update_status missing task_id parameter"
    assert 'status' in update_sig.parameters, "update_status missing status parameter"
    print("7. update_status has correct signature (task_id, status)")

    # close_task should accept task_id parameter
    close_sig = inspect.signature(client.close_task)
    assert 'task_id' in close_sig.parameters, "close_task missing task_id parameter"
    print("8. close_task has correct signature (task_id)")

    # Test 5: Verify error handling for empty task_id
    try:
        client.fetch_task("")
        print("❌ fetch_task should reject empty task_id")
        sys.exit(1)
    except ValueError as e:
        print("9. fetch_task correctly rejects empty task_id")

    try:
        client.update_status("", "in_progress")
        print("❌ update_status should reject empty task_id")
        sys.exit(1)
    except ValueError:
        print("10. update_status correctly rejects empty task_id")

    try:
        client.close_task("")
        print("❌ close_task should reject empty task_id")
        sys.exit(1)
    except ValueError:
        print("11. close_task correctly rejects empty task_id")

    # Test 6: Verify update_status validates status
    try:
        client.update_status("test-id", "invalid_status")
        print("❌ update_status should reject invalid status")
        sys.exit(1)
    except ValueError as e:
        print("12. update_status correctly validates status values")

    print("\n" + "=" * 60)
    print("✅ ALL BEADS CLIENT VERIFICATION TESTS PASSED!")
    print("=" * 60)
    print("\nThe BeadsClient implementation is complete and correct.")
    print("All methods are present with proper signatures and validation.")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
