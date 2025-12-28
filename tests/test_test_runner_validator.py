# ABOUTME: Tests for TestRunnerValidator class
# ABOUTME: Consolidated test suite for test execution and validation

"""Tests for TestRunnerValidator class.

Consolidated from 32 separate tests to focused tests covering
essential behaviors without redundant pattern testing.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

from jean_claude.core.test_runner_validator import TestRunnerValidator


class TestTestRunnerValidatorInit:
    """Test TestRunnerValidator initialization - consolidated from 4 tests to 1."""

    def test_init_with_various_options(self, tmp_path):
        """Test initialization with defaults, custom command, and custom path."""
        # Default initialization
        validator1 = TestRunnerValidator()
        assert validator1.test_command == "pytest"
        assert validator1.repo_path == Path.cwd()

        # Custom command
        validator2 = TestRunnerValidator(test_command="python -m pytest")
        assert validator2.test_command == "python -m pytest"

        # Custom path (string converted to Path)
        validator3 = TestRunnerValidator(repo_path=tmp_path)
        assert validator3.repo_path == tmp_path

        # String path converted
        validator4 = TestRunnerValidator(repo_path="/tmp/test")
        assert isinstance(validator4.repo_path, Path)


class TestTestRunnerValidatorRunTests:
    """Test running tests - consolidated from 6 tests to 2."""

    @pytest.mark.parametrize("returncode,stdout,stderr,expected_passed", [
        (0, "===== 10 passed in 2.34s =====", "", True),
        (1, "===== 2 failed, 8 passed in 3.45s =====", "", False),
        (2, "", "ERROR: Test collection failed", False),
        (1, "===== 1 failed =====", "DeprecationWarning: old API", False),
    ])
    @patch('subprocess.run')
    def test_run_tests_returns_correct_result(self, mock_run, returncode, stdout, stderr, expected_passed):
        """Test that run_tests returns correct result for various scenarios."""
        mock_run.return_value = Mock(returncode=returncode, stdout=stdout, stderr=stderr)

        validator = TestRunnerValidator()
        result = validator.run_tests()

        assert result["passed"] is expected_passed
        assert result["exit_code"] == returncode

    @pytest.mark.parametrize("error_type,error_msg", [
        (subprocess.SubprocessError, "Command not found"),
        (subprocess.TimeoutExpired, "timeout"),
        (PermissionError, "Permission denied"),
        (FileNotFoundError, "pytest not found"),
    ])
    @patch('subprocess.run')
    def test_run_tests_handles_errors(self, mock_run, error_type, error_msg):
        """Test that run_tests handles various errors gracefully."""
        if error_type == subprocess.TimeoutExpired:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=30)
        else:
            mock_run.side_effect = error_type(error_msg)

        validator = TestRunnerValidator(timeout=30)
        result = validator.run_tests()

        assert result["passed"] is False
        assert result["error"] is not None


class TestTestRunnerValidatorParseOutput:
    """Test parsing output - consolidated from 5 tests to 1."""

    @pytest.mark.parametrize("output,exit_code,expected", [
        ("===== 15 passed in 3.45s =====", 0, {"passed": True, "total_tests": 15, "failed_tests": 0}),
        ("===== 3 failed, 12 passed in 4.56s =====", 1, {"passed": False, "total_tests": 15, "failed_tests": 3}),
        ("ERROR: file not found", 2, {"passed": False}),
        ("===== 10 passed, 1 warning in 2.00s =====", 0, {"passed": True, "total_tests": 10}),
    ])
    def test_parse_output_various_formats(self, output, exit_code, expected):
        """Test parsing various pytest output formats."""
        validator = TestRunnerValidator()
        result = validator.parse_output(output, exit_code=exit_code)

        for key, value in expected.items():
            assert result.get(key) == value

    def test_parse_output_extracts_failed_test_names(self):
        """Test that failed test names are extracted."""
        validator = TestRunnerValidator()
        output = """
        FAILED tests/test_auth.py::test_login - AssertionError
        FAILED tests/test_api.py::test_endpoint - ValueError
        ===== 2 failed, 8 passed in 3.00s =====
        """

        result = validator.parse_output(output, exit_code=1)

        assert result["passed"] is False
        assert len(result["failed_test_names"]) == 2
        assert "test_login" in str(result["failed_test_names"])


class TestTestRunnerValidatorValidate:
    """Test validation method - consolidated from 5 tests to 2."""

    @patch('subprocess.run')
    def test_validate_success_and_failure(self, mock_run):
        """Test validation with passing and failing tests."""
        # Success case
        mock_run.return_value = Mock(
            returncode=0, stdout="===== 20 passed in 5.00s =====", stderr=""
        )
        validator = TestRunnerValidator()
        result = validator.validate()
        assert result["can_commit"] is True
        assert result["passed"] is True
        assert "pass" in result["message"].lower()

        # Failure case
        mock_run.return_value = Mock(
            returncode=1, stdout="===== 5 failed, 15 passed in 6.00s =====", stderr=""
        )
        result = validator.validate()
        assert result["can_commit"] is False
        assert result["passed"] is False
        assert "fail" in result["message"].lower()

    @patch('subprocess.run')
    def test_validate_edge_cases(self, mock_run):
        """Test validation edge cases."""
        # No tests found
        mock_run.return_value = Mock(
            returncode=5, stdout="===== no tests ran in 0.01s =====", stderr=""
        )
        validator = TestRunnerValidator()
        result = validator.validate()
        assert result["can_commit"] is False

        # Subprocess error
        mock_run.side_effect = subprocess.SubprocessError("pytest not found")
        result = validator.validate()
        assert result["can_commit"] is False


class TestTestRunnerValidatorCustomCommands:
    """Test custom commands - consolidated from 3 tests to 1."""

    @pytest.mark.parametrize("command,stdout", [
        ("python -m pytest -v", "===== 10 passed in 2.00s ====="),
        ("python -m unittest", "Ran 15 tests in 3.456s\n\nOK"),
        ("npm test", "All tests passed"),
    ])
    @patch('subprocess.run')
    def test_various_test_commands(self, mock_run, command, stdout):
        """Test running with various test frameworks."""
        mock_run.return_value = Mock(returncode=0, stdout=stdout, stderr="")

        validator = TestRunnerValidator(test_command=command)
        result = validator.run_tests()

        assert result["passed"] is True


class TestTestRunnerValidatorIntegration:
    """Integration tests - kept essential tests."""

    @patch('subprocess.run')
    def test_full_validation_workflow(self, mock_run):
        """Test complete validation workflow."""
        # Success workflow
        mock_run.return_value = Mock(
            returncode=0, stdout="===== 25 passed in 7.89s =====", stderr=""
        )

        validator = TestRunnerValidator()
        test_result = validator.run_tests()
        assert test_result["passed"] is True

        validation_result = validator.validate()
        assert validation_result["can_commit"] is True

        # Failure workflow
        mock_run.return_value = Mock(
            returncode=1,
            stdout="FAILED tests/test_feature.py::test_new_functionality\n===== 1 failed, 24 passed in 8.12s =====",
            stderr=""
        )

        test_result = validator.run_tests()
        assert test_result["passed"] is False

        validation_result = validator.validate()
        assert validation_result["can_commit"] is False
