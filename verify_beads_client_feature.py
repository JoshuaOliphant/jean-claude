#!/usr/bin/env python
"""Comprehensive verification of BeadsClient feature implementation."""

import sys
import json
import subprocess
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, 'src')

from jean_claude.core.beads import BeadsClient, BeadsTask, BeadsTaskStatus

print("="*70)
print("BEADS CLIENT FEATURE VERIFICATION")
print("="*70)

errors = []
passed = 0

def test(description):
    """Decorator for test functions."""
    def decorator(func):
        def wrapper():
            global passed
            try:
                func()
                print(f"✅ {description}")
                passed += 1
            except Exception as e:
                print(f"❌ {description}")
                errors.append(f"{description}: {str(e)}")
        return wrapper
    return decorator

# Test 1: BeadsClient instantiation
@test("BeadsClient can be instantiated")
def test_instantiation():
    client = BeadsClient()
    assert isinstance(client, BeadsClient)

# Test 2: BeadsClient has required methods
@test("BeadsClient has fetch_task method")
def test_has_fetch_task():
    client = BeadsClient()
    assert hasattr(client, 'fetch_task')
    assert callable(client.fetch_task)

@test("BeadsClient has update_status method")
def test_has_update_status():
    client = BeadsClient()
    assert hasattr(client, 'update_status')
    assert callable(client.update_status)

@test("BeadsClient has close_task method")
def test_has_close_task():
    client = BeadsClient()
    assert hasattr(client, 'close_task')
    assert callable(client.close_task)

# Test 3: fetch_task validates empty task_id
@test("fetch_task raises ValueError for empty task_id")
def test_fetch_task_empty_id():
    client = BeadsClient()
    try:
        client.fetch_task("")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "task_id cannot be empty" in str(e)

# Test 4: fetch_task with mocked subprocess
@test("fetch_task calls subprocess correctly")
def test_fetch_task_subprocess():
    client = BeadsClient()
    mock_output = json.dumps([{
        "id": "test-1",
        "title": "Test Task",
        "description": "A test task",
        "status": "todo"
    }])

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            stdout=mock_output,
            stderr="",
            returncode=0
        )

        task = client.fetch_task("test-1")
        assert isinstance(task, BeadsTask)
        assert task.id == "test-1"
        assert task.title == "Test Task"

# Test 5: update_status validates empty task_id
@test("update_status raises ValueError for empty task_id")
def test_update_status_empty_id():
    client = BeadsClient()
    try:
        client.update_status("", "in_progress")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "task_id cannot be empty" in str(e)

# Test 6: update_status validates empty status
@test("update_status raises ValueError for empty status")
def test_update_status_empty_status():
    client = BeadsClient()
    try:
        client.update_status("test-1", "")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "status cannot be empty" in str(e)

# Test 7: update_status validates invalid status
@test("update_status raises ValueError for invalid status")
def test_update_status_invalid():
    client = BeadsClient()
    try:
        client.update_status("test-1", "invalid_status")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "Invalid status" in str(e)

# Test 8: update_status calls subprocess correctly
@test("update_status calls subprocess correctly")
def test_update_status_subprocess():
    client = BeadsClient()

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="",
            returncode=0
        )

        result = client.update_status("test-1", "in_progress")
        assert result is None
        mock_run.assert_called_once_with(
            ['bd', 'update', '--status', 'in_progress', 'test-1'],
            capture_output=True,
            text=True,
            check=True
        )

# Test 9: close_task validates empty task_id
@test("close_task raises ValueError for empty task_id")
def test_close_task_empty_id():
    client = BeadsClient()
    try:
        client.close_task("")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "task_id cannot be empty" in str(e)

# Test 10: close_task calls subprocess correctly
@test("close_task calls subprocess correctly")
def test_close_task_subprocess():
    client = BeadsClient()

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="",
            returncode=0
        )

        result = client.close_task("test-1")
        assert result is None
        mock_run.assert_called_once_with(
            ['bd', 'close', 'test-1'],
            capture_output=True,
            text=True,
            check=True
        )

# Test 11: fetch_task handles subprocess errors
@test("fetch_task handles subprocess errors gracefully")
def test_fetch_task_subprocess_error():
    client = BeadsClient()

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ['bd', 'show'], stderr="Task not found"
        )

        try:
            client.fetch_task("test-1")
            raise AssertionError("Should have raised RuntimeError")
        except RuntimeError as e:
            assert "Failed to fetch task" in str(e)

# Test 12: update_status handles subprocess errors
@test("update_status handles subprocess errors gracefully")
def test_update_status_subprocess_error():
    client = BeadsClient()

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ['bd', 'update'], stderr="Update failed"
        )

        try:
            client.update_status("test-1", "done")
            raise AssertionError("Should have raised RuntimeError")
        except RuntimeError as e:
            assert "Failed to update status" in str(e)

# Test 13: close_task handles subprocess errors
@test("close_task handles subprocess errors gracefully")
def test_close_task_subprocess_error():
    client = BeadsClient()

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ['bd', 'close'], stderr="Close failed"
        )

        try:
            client.close_task("test-1")
            raise AssertionError("Should have raised RuntimeError")
        except RuntimeError as e:
            assert "Failed to close task" in str(e)

# Run all tests
print()
test_instantiation()
test_has_fetch_task()
test_has_update_status()
test_has_close_task()
test_fetch_task_empty_id()
test_fetch_task_subprocess()
test_update_status_empty_id()
test_update_status_empty_status()
test_update_status_invalid()
test_update_status_subprocess()
test_close_task_empty_id()
test_close_task_subprocess()
test_fetch_task_subprocess_error()
test_update_status_subprocess_error()
test_close_task_subprocess_error()

print()
print("="*70)
print(f"RESULTS: {passed} tests passed")
if errors:
    print(f"{len(errors)} tests failed:")
    for error in errors:
        print(f"  - {error}")
    print("="*70)
    sys.exit(1)
else:
    print("✅ ALL BEADS CLIENT FEATURES VERIFIED!")
    print("="*70)
    sys.exit(0)
