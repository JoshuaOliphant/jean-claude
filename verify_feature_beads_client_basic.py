#!/usr/bin/env python3
"""Verify that BeadsClient class meets feature requirements for beads-client-basic."""

import sys


def verify_beads_client():
    """Verify BeadsClient class implementation."""
    print("=" * 60)
    print("VERIFYING BEADS CLIENT BASIC FEATURE")
    print("=" * 60)

    results = []

    # Test 1: Check that BeadsClient can be imported
    print("\n1. Checking BeadsClient import...")
    try:
        from jean_claude.core.beads import BeadsClient, BeadsTask
        print("   ✓ BeadsClient can be imported")
        results.append(True)
    except ImportError as e:
        print(f"   ✗ Failed to import BeadsClient: {e}")
        results.append(False)
        return False

    # Test 2: Check that BeadsClient can be instantiated
    print("\n2. Checking BeadsClient instantiation...")
    try:
        client = BeadsClient()
        print("   ✓ BeadsClient can be instantiated")
        results.append(True)
    except Exception as e:
        print(f"   ✗ Failed to instantiate BeadsClient: {e}")
        results.append(False)
        return False

    # Test 3: Check that BeadsClient has fetch_task method
    print("\n3. Checking fetch_task method exists...")
    if hasattr(client, 'fetch_task') and callable(client.fetch_task):
        print("   ✓ fetch_task method exists and is callable")
        results.append(True)
    else:
        print("   ✗ fetch_task method not found")
        results.append(False)

    # Test 4: Check that BeadsClient has parse_task_json method
    print("\n4. Checking parse_task_json method exists...")
    if hasattr(client, 'parse_task_json') and callable(client.parse_task_json):
        print("   ✓ parse_task_json method exists and is callable")
        results.append(True)
    else:
        print("   ✗ parse_task_json method not found")
        results.append(False)

    # Test 5: Check BeadsTask has required fields
    print("\n5. Checking BeadsTask has required fields...")
    import json
    from unittest.mock import patch, MagicMock

    try:
        # Create a mock task to verify fields
        mock_data = {
            "id": "test-123",
            "title": "Test Task",
            "description": "Test description",
            "status": "open",
            "acceptance_criteria": ["AC1", "AC2"]
        }

        # Parse using parse_task_json
        task = client.parse_task_json(json.dumps(mock_data))

        # Verify all required fields exist
        has_id = hasattr(task, 'id') and task.id == "test-123"
        has_title = hasattr(task, 'title') and task.title == "Test Task"
        has_description = hasattr(task, 'description') and task.description == "Test description"
        has_status = hasattr(task, 'status')
        has_acceptance_criteria = hasattr(task, 'acceptance_criteria') and len(task.acceptance_criteria) == 2

        if all([has_id, has_title, has_description, has_status, has_acceptance_criteria]):
            print("   ✓ BeadsTask has all required fields: id, title, description, status, acceptance_criteria")
            results.append(True)
        else:
            print("   ✗ BeadsTask missing required fields")
            print(f"     - has_id: {has_id}")
            print(f"     - has_title: {has_title}")
            print(f"     - has_description: {has_description}")
            print(f"     - has_status: {has_status}")
            print(f"     - has_acceptance_criteria: {has_acceptance_criteria}")
            results.append(False)
    except Exception as e:
        print(f"   ✗ Error verifying BeadsTask fields: {e}")
        results.append(False)

    # Test 6: Check that fetch_task uses 'bd show --json <task-id>'
    print("\n6. Checking fetch_task uses correct bd command...")
    try:
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout=json.dumps([mock_data]),
                stderr="",
                returncode=0
            )

            client.fetch_task("test-123")

            # Verify the command was called correctly
            mock_run.assert_called_once_with(
                ['bd', 'show', '--json', 'test-123'],
                capture_output=True,
                text=True,
                check=True
            )
            print("   ✓ fetch_task uses 'bd show --json <task-id>' command")
            results.append(True)
    except Exception as e:
        print(f"   ✗ fetch_task doesn't use correct command: {e}")
        results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total} checks")

    if all(results):
        print("\n✅ ALL CHECKS PASSED - Feature beads-client-basic is complete!")
        return True
    else:
        print("\n❌ SOME CHECKS FAILED - Feature needs fixes")
        return False


if __name__ == "__main__":
    success = verify_beads_client()
    sys.exit(0 if success else 1)
