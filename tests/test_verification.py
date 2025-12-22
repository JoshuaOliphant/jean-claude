"""Tests for verification-first mode."""

import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from jean_claude.core.state import WorkflowState, Feature
from jean_claude.core.verification import (
    VerificationResult,
    run_verification,
    should_verify,
    _parse_failed_tests,
)


class TestVerificationResult:
    """Test VerificationResult model."""

    def test_passed_result(self):
        """Test creating a passed verification result."""
        result = VerificationResult(
            passed=True,
            test_output="All tests passed",
            duration_ms=1500,
            tests_run=5,
        )
        assert result.passed
        assert result.duration_ms == 1500
        assert result.tests_run == 5
        assert len(result.failed_tests) == 0
        assert not result.skipped

    def test_failed_result(self):
        """Test creating a failed verification result."""
        result = VerificationResult(
            passed=False,
            test_output="Test failed",
            failed_tests=["tests/test_foo.py::test_bar", "tests/test_baz.py::test_qux"],
            duration_ms=2000,
            tests_run=10,
        )
        assert not result.passed
        assert len(result.failed_tests) == 2
        assert "tests/test_foo.py::test_bar" in result.failed_tests

    def test_skipped_result(self):
        """Test creating a skipped verification result."""
        result = VerificationResult(
            passed=True,
            test_output="No tests to run",
            duration_ms=0,
            skipped=True,
            skip_reason="No completed features",
        )
        assert result.skipped
        assert result.skip_reason == "No completed features"


class TestParseFailedTests:
    """Test pytest output parsing."""

    def test_parse_single_failure(self):
        """Test parsing a single failed test."""
        output = """============================= test session starts ==============================
FAILED tests/test_auth.py::test_login - AssertionError: Invalid token
=========================== 1 failed in 0.12s ==============================="""
        failed = _parse_failed_tests(output)
        assert len(failed) == 1
        assert "tests/test_auth.py::test_login" in failed

    def test_parse_multiple_failures(self):
        """Test parsing multiple failed tests."""
        output = """FAILED tests/test_auth.py::test_login - AssertionError
FAILED tests/test_auth.py::test_logout - KeyError: 'user'
FAILED tests/test_billing.py::test_payment - ValueError"""
        failed = _parse_failed_tests(output)
        assert len(failed) == 3
        assert "tests/test_auth.py::test_login" in failed
        assert "tests/test_billing.py::test_payment" in failed

    def test_parse_no_failures(self):
        """Test parsing output with no failures."""
        output = """
        ============================= test session starts ==============================
        collected 5 items
        tests/test_auth.py .....                                                  [100%]
        ============================== 5 passed in 0.23s ===============================
        """
        failed = _parse_failed_tests(output)
        assert len(failed) == 0


class TestRunVerification:
    """Test run_verification function."""

    def test_no_completed_features(self, tmp_path):
        """Test verification with no completed features."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )
        state.add_feature("Feature 1", "Description", "tests/test_one.py")

        result = run_verification(state, tmp_path)

        assert result.passed
        assert result.skipped
        assert result.skip_reason == "No completed features"

    def test_completed_features_no_test_files(self, tmp_path):
        """Test verification with completed features but no test files."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )
        feature = state.add_feature("Feature 1", "Description", None)
        feature.status = "completed"

        result = run_verification(state, tmp_path)

        assert result.passed
        assert result.skipped
        assert result.skip_reason == "No test files found"

    def test_test_files_dont_exist(self, tmp_path):
        """Test verification when test files don't exist yet."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )
        feature = state.add_feature("Feature 1", "Description", "tests/test_missing.py")
        feature.status = "completed"

        result = run_verification(state, tmp_path)

        assert result.passed
        assert result.skipped
        assert "Test files not created yet" in result.skip_reason

    @patch("jean_claude.core.verification.subprocess.run")
    def test_successful_verification(self, mock_run, tmp_path):
        """Test successful verification with passing tests."""
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

        # Mock successful pytest run
        mock_run.return_value = Mock(
            returncode=0,
            stdout="5 passed in 0.23s",
            stderr="",
        )

        result = run_verification(state, tmp_path)

        assert result.passed
        assert not result.skipped
        assert result.tests_run == 1
        assert len(result.failed_tests) == 0
        assert "pytest" in mock_run.call_args[0][0][0]

    @patch("jean_claude.core.verification.subprocess.run")
    def test_failed_verification(self, mock_run, tmp_path):
        """Test failed verification with failing tests."""
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

        # Mock failed pytest run
        mock_run.return_value = Mock(
            returncode=1,
            stdout="FAILED tests/test_feature.py::test_example - AssertionError",
            stderr="",
        )

        result = run_verification(state, tmp_path)

        assert not result.passed
        assert len(result.failed_tests) == 1
        assert "tests/test_feature.py::test_example" in result.failed_tests

    @patch("jean_claude.core.verification.subprocess.run")
    def test_pytest_not_found(self, mock_run, tmp_path):
        """Test verification when pytest is not installed."""
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

        # Mock FileNotFoundError
        mock_run.side_effect = FileNotFoundError("pytest not found")

        result = run_verification(state, tmp_path)

        assert not result.passed
        assert "pytest not found" in result.test_output
        assert "pytest_not_found" in result.failed_tests


class TestShouldVerify:
    """Test should_verify function."""

    def test_no_completed_features(self):
        """Test should_verify with no completed features."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )
        state.add_feature("Feature 1", "Description", "tests/test_one.py")

        assert not should_verify(state)

    def test_completed_features_no_test_files(self):
        """Test should_verify with completed features but no test files."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )
        feature = state.add_feature("Feature 1", "Description", None)
        feature.status = "completed"

        assert not should_verify(state)

    def test_never_verified_should_verify(self):
        """Test should_verify when never verified before."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )
        feature = state.add_feature("Feature 1", "Description", "tests/test_one.py")
        feature.status = "completed"

        assert should_verify(state)

    def test_recently_verified_should_not_verify(self):
        """Test should_verify when recently verified (< 5 minutes)."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )
        feature = state.add_feature("Feature 1", "Description", "tests/test_one.py")
        feature.status = "completed"

        last_verified = time.time()  # Just now
        assert not should_verify(state, last_verified)

    def test_old_verification_should_verify(self):
        """Test should_verify when last verified > 5 minutes ago."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )
        feature = state.add_feature("Feature 1", "Description", "tests/test_one.py")
        feature.status = "completed"

        last_verified = time.time() - 400  # 6+ minutes ago
        assert should_verify(state, last_verified)


class TestWorkflowStateVerification:
    """Test WorkflowState verification methods."""

    def test_should_verify_method_no_features(self):
        """Test WorkflowState.should_verify with no completed features."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )
        assert not state.should_verify()

    def test_should_verify_method_never_verified(self):
        """Test WorkflowState.should_verify when never verified."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )
        feature = state.add_feature("Feature 1", "Description", "tests/test_one.py")
        feature.status = "completed"

        assert state.should_verify()

    def test_mark_verification(self):
        """Test WorkflowState.mark_verification updates state."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="chore",
        )

        assert state.verification_count == 0
        assert state.last_verification_at is None
        assert state.last_verification_passed is True

        state.mark_verification(passed=True)

        assert state.verification_count == 1
        assert state.last_verification_at is not None
        assert state.last_verification_passed is True

        state.mark_verification(passed=False)

        assert state.verification_count == 2
        assert state.last_verification_passed is False
