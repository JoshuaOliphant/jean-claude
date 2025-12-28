#!/usr/bin/env python
"""Validate the Beads status lifecycle implementation."""

import sys
from unittest.mock import Mock, patch

from click.testing import CliRunner

# Import the work command and BeadsTask
from jean_claude.cli.commands.work import work
from jean_claude.core.beads import BeadsTask


def test_status_update_called():
    """Test that update_beads_status is called with 'in_progress'."""
    mock_task = BeadsTask(
        id="test-123.1",
        title="Test Task",
        description="Test description",
        acceptance_criteria=["AC 1"],
        status="not_started"
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test"):
                with patch('jean_claude.cli.commands.work.update_beads_status') as mock_update:
                    with patch('jean_claude.cli.commands.work.WorkflowState') as mock_state_class:
                        mock_state_instance = Mock()
                        mock_state_class.return_value = mock_state_instance

                        result = runner.invoke(work, ["test-123.1"])

                        # Check that update_beads_status was called
                        if mock_update.called:
                            call_args = mock_update.call_args
                            if call_args[0] == ("test-123.1", "in_progress"):
                                print("✓ update_beads_status called correctly with 'in_progress'")
                                return True
                            else:
                                print(f"✗ update_beads_status called with wrong args: {call_args}")
                                return False
                        else:
                            print("✗ update_beads_status was not called")
                            return False


def test_graceful_error_handling():
    """Test that status update failures are handled gracefully."""
    mock_task = BeadsTask(
        id="test-456.2",
        title="Test Task",
        description="Test",
        acceptance_criteria=[],
        status="not_started"
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_task):
            with patch('jean_claude.cli.commands.work.update_beads_status', side_effect=RuntimeError("Update failed")):
                with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test"):
                    with patch('jean_claude.cli.commands.work.WorkflowState') as mock_state_class:
                        mock_state_instance = Mock()
                        mock_state_class.return_value = mock_state_instance

                        result = runner.invoke(work, ["test-456.2"])

                        # Should continue execution and show warning
                        if "warning" in result.output.lower() or "failed" in result.output.lower():
                            print("✓ Status update failure handled gracefully with warning")
                            return True
                        else:
                            print(f"✗ No warning shown for status update failure")
                            print(f"Output: {result.output}")
                            return False


def test_imports():
    """Test that all required functions are imported."""
    try:
        from jean_claude.cli.commands.work import (
            fetch_beads_task,
            generate_spec_from_beads,
            update_beads_status,
            close_beads_task,
        )
        print("✓ All required functions imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import required functions: {e}")
        return False


def main():
    """Run all validation tests."""
    print("="*60)
    print("Validating Beads Status Lifecycle Implementation")
    print("="*60)
    print()

    tests = [
        ("Import validation", test_imports),
        ("Status update call", test_status_update_called),
        ("Graceful error handling", test_graceful_error_handling),
    ]

    results = []
    for name, test_func in tests:
        print(f"Testing: {name}")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
        print()

    print("="*60)
    if all(results):
        print("✅ ALL VALIDATION TESTS PASSED!")
        print("="*60)
        return 0
    else:
        print("❌ SOME VALIDATION TESTS FAILED!")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
