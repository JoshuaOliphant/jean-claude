# ABOUTME: Tests for verification-first mode
# ABOUTME: Consolidated tests for test running and verification logic

"""Tests for verification-first mode.

Consolidated from 20 separate tests to focused tests covering
essential behaviors without per-status redundancy.
"""

import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from jean_claude.core.state import WorkflowState
from jean_claude.core.verification import (
    VerificationResult,
    run_verification,
    should_verify,
    _parse_failed_tests,
)


class TestVerificationResult:
    """Test VerificationResult model - consolidated from 3 tests to 1."""

    def test_verification_result_all_states(self):
        """Test passed, failed, and skipped verification results."""
        # Passed result
        passed = VerificationResult(
            passed=True,
            test_output="All tests passed",
            duration_ms=1500,
            tests_run=5,
        )
        assert passed.passed
        assert passed.duration_ms == 1500
        assert passed.tests_run == 5
        assert len(passed.failed_tests) == 0
        assert not passed.skipped

        # Failed result
        failed = VerificationResult(
            passed=False,
            test_output="Test failed",
            failed_tests=["tests/test_foo.py::test_bar", "tests/test_baz.py::test_qux"],
            duration_ms=2000,
            tests_run=10,
        )
        assert not failed.passed
        assert len(failed.failed_tests) == 2
        assert "tests/test_foo.py::test_bar" in failed.failed_tests

        # Skipped result
        skipped = VerificationResult(
            passed=True,
            test_output="No tests to run",
            duration_ms=0,
            skipped=True,
            skip_reason="No completed features",
        )
        assert skipped.skipped
        assert skipped.skip_reason == "No completed features"


class TestParseFailedTests:
    """Test pytest output parsing - consolidated from 3 tests to 1."""

    def test_parse_failed_tests_all_cases(self):
        """Test parsing single, multiple, and no failures."""
        # Single failure
        single = """============================= test session starts ==============================
FAILED tests/test_auth.py::test_login - AssertionError: Invalid token
=========================== 1 failed in 0.12s ==============================="""
        failed = _parse_failed_tests(single)
        assert len(failed) == 1
        assert "tests/test_auth.py::test_login" in failed

        # Multiple failures
        multiple = """FAILED tests/test_auth.py::test_login - AssertionError
FAILED tests/test_auth.py::test_logout - KeyError: 'user'
FAILED tests/test_billing.py::test_payment - ValueError"""
        failed = _parse_failed_tests(multiple)
        assert len(failed) == 3
        assert "tests/test_billing.py::test_payment" in failed

        # No failures
        passing = """
        ============================= test session starts ==============================
        collected 5 items
        tests/test_auth.py .....                                                  [100%]
        ============================== 5 passed in 0.23s ===============================
        """
        assert len(_parse_failed_tests(passing)) == 0


class TestRunVerification:
    """Test run_verification function - consolidated from 6 tests to 2."""

    def test_run_verification_skip_cases(self, tmp_path):
        """Test verification skip cases: no features, no test files, files don't exist."""
        # No completed features
        state1 = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )
        state1.add_feature("Feature 1", "Description", "tests/test_one.py")
        result = run_verification(state1, tmp_path)
        assert result.passed
        assert result.skipped
        assert result.skip_reason == "No completed features"

        # Completed but no test files
        state2 = WorkflowState(
            workflow_id="test-456",
            workflow_name="Test",
            workflow_type="chore",
        )
        feature = state2.add_feature("Feature 1", "Description", None)
        feature.status = "completed"
        result = run_verification(state2, tmp_path)
        assert result.passed
        assert result.skipped
        assert result.skip_reason == "No test files found"

        # Test files don't exist yet
        state3 = WorkflowState(
            workflow_id="test-789",
            workflow_name="Test",
            workflow_type="chore",
        )
        feature = state3.add_feature("Feature 1", "Description", "tests/test_missing.py")
        feature.status = "completed"
        result = run_verification(state3, tmp_path)
        assert result.passed
        assert result.skipped
        assert "Test files not created yet" in result.skip_reason

    @patch("jean_claude.core.verification.subprocess.run")
    def test_run_verification_success_failure_and_errors(self, mock_run, tmp_path):
        """Test verification success, failure, and error cases."""
        # Create test files
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_feature.py"
        test_file.write_text("def test_example(): pass")

        # Setup state
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )
        feature = state.add_feature("Feature 1", "Description", "tests/test_feature.py")
        feature.status = "completed"

        # Success case
        mock_run.return_value = Mock(returncode=0, stdout="5 passed in 0.23s", stderr="")
        result = run_verification(state, tmp_path)
        assert result.passed
        assert not result.skipped
        assert "uv" in mock_run.call_args[0][0]
        assert "pytest" in mock_run.call_args[0][0]

        # Failure case
        mock_run.return_value = Mock(
            returncode=1,
            stdout="FAILED tests/test_feature.py::test_example - AssertionError",
            stderr=""
        )
        result = run_verification(state, tmp_path)
        assert not result.passed
        assert "tests/test_feature.py::test_example" in result.failed_tests

        # pytest not found
        mock_run.side_effect = FileNotFoundError("uv not found")
        result = run_verification(state, tmp_path)
        assert not result.passed
        assert "uv or pytest not found" in result.test_output


class TestShouldVerify:
    """Test should_verify function - consolidated from 5 tests to 1."""

    def test_should_verify_all_cases(self):
        """Test all should_verify conditions."""
        # No completed features
        state1 = WorkflowState(
            workflow_id="test-1",
            workflow_name="Test",
            workflow_type="chore",
        )
        state1.add_feature("Feature 1", "Description", "tests/test_one.py")
        assert not should_verify(state1)

        # Completed but no test files
        state2 = WorkflowState(
            workflow_id="test-2",
            workflow_name="Test",
            workflow_type="chore",
        )
        feature = state2.add_feature("Feature 1", "Description", None)
        feature.status = "completed"
        assert not should_verify(state2)

        # Never verified - should verify
        state3 = WorkflowState(
            workflow_id="test-3",
            workflow_name="Test",
            workflow_type="chore",
        )
        feature = state3.add_feature("Feature 1", "Description", "tests/test_one.py")
        feature.status = "completed"
        assert should_verify(state3)

        # Recently verified - should not verify
        assert not should_verify(state3, time.time())

        # Old verification - should verify
        assert should_verify(state3, time.time() - 400)


class TestWorkflowStateVerification:
    """Test WorkflowState verification methods - consolidated from 3 tests to 1."""

    def test_workflow_state_verification_methods(self):
        """Test WorkflowState should_verify and mark_verification."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )

        # No features - should not verify
        assert not state.should_verify()

        # Add completed feature
        feature = state.add_feature("Feature 1", "Description", "tests/test_one.py")
        feature.status = "completed"
        assert state.should_verify()

        # Initial state
        assert state.verification_count == 0
        assert state.last_verification_at is None
        assert state.last_verification_passed is True

        # Mark passed verification
        state.mark_verification(passed=True)
        assert state.verification_count == 1
        assert state.last_verification_at is not None
        assert state.last_verification_passed is True

        # Mark failed verification
        state.mark_verification(passed=False)
        assert state.verification_count == 2
        assert state.last_verification_passed is False
