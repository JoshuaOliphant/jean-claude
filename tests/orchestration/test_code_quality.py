"""Tests for code quality verification in orchestration modules.

This test suite verifies that the modified orchestration modules
(auto_continue.py and two_agent.py) maintain code quality standards
after refactoring.
"""

import subprocess
from pathlib import Path
import pytest


# Paths to the modified files
AUTO_CONTINUE_PATH = "src/jean_claude/orchestration/auto_continue.py"
TWO_AGENT_PATH = "src/jean_claude/orchestration/two_agent.py"


def run_ruff_check(file_path: str) -> tuple[bool, str, str]:
    """Run ruff check on a specific file.

    Args:
        file_path: Path to the file to check

    Returns:
        Tuple of (passed, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "check", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # ruff returns 0 if no errors, non-zero if errors found
        passed = result.returncode == 0
        return passed, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Ruff check timed out"
    except Exception as e:
        return False, "", str(e)


def run_ruff_format_check(file_path: str) -> tuple[bool, str, str]:
    """Run ruff format check on a specific file.

    Args:
        file_path: Path to the file to check

    Returns:
        Tuple of (passed, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "format", "--check", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # ruff format --check returns 0 if properly formatted
        passed = result.returncode == 0
        return passed, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Ruff format check timed out"
    except Exception as e:
        return False, "", str(e)


class TestAutoContinueCodeQuality:
    """Test code quality for auto_continue.py."""

    def test_auto_continue_no_linting_errors(self):
        """Verify auto_continue.py has no linting errors."""
        passed, stdout, stderr = run_ruff_check(AUTO_CONTINUE_PATH)

        error_msg = f"Ruff found linting errors in {AUTO_CONTINUE_PATH}:\n"
        if stdout:
            error_msg += f"STDOUT:\n{stdout}\n"
        if stderr:
            error_msg += f"STDERR:\n{stderr}\n"

        assert passed, error_msg

    def test_auto_continue_formatting(self):
        """Verify auto_continue.py follows formatting standards."""
        passed, stdout, stderr = run_ruff_format_check(AUTO_CONTINUE_PATH)

        error_msg = f"Ruff found formatting issues in {AUTO_CONTINUE_PATH}:\n"
        if stdout:
            error_msg += f"STDOUT:\n{stdout}\n"
        if stderr:
            error_msg += f"STDERR:\n{stderr}\n"

        assert passed, error_msg


class TestTwoAgentCodeQuality:
    """Test code quality for two_agent.py."""

    def test_two_agent_no_linting_errors(self):
        """Verify two_agent.py has no linting errors."""
        passed, stdout, stderr = run_ruff_check(TWO_AGENT_PATH)

        error_msg = f"Ruff found linting errors in {TWO_AGENT_PATH}:\n"
        if stdout:
            error_msg += f"STDOUT:\n{stdout}\n"
        if stderr:
            error_msg += f"STDERR:\n{stderr}\n"

        assert passed, error_msg

    def test_two_agent_formatting(self):
        """Verify two_agent.py follows formatting standards."""
        passed, stdout, stderr = run_ruff_format_check(TWO_AGENT_PATH)

        error_msg = f"Ruff found formatting issues in {TWO_AGENT_PATH}:\n"
        if stdout:
            error_msg += f"STDOUT:\n{stdout}\n"
        if stderr:
            error_msg += f"STDERR:\n{stderr}\n"

        assert passed, error_msg


class TestCombinedCodeQuality:
    """Test code quality for all modified files together."""

    def test_all_modified_files_pass_linting(self):
        """Verify all modified files pass linting together."""
        files = [AUTO_CONTINUE_PATH, TWO_AGENT_PATH]
        all_passed = True
        error_messages = []

        for file_path in files:
            passed, stdout, stderr = run_ruff_check(file_path)
            if not passed:
                all_passed = False
                msg = f"\n{file_path} failed linting:"
                if stdout:
                    msg += f"\n  STDOUT: {stdout}"
                if stderr:
                    msg += f"\n  STDERR: {stderr}"
                error_messages.append(msg)

        error_msg = "Linting errors found in modified files:" + "".join(error_messages)
        assert all_passed, error_msg

    def test_all_modified_files_properly_formatted(self):
        """Verify all modified files are properly formatted."""
        files = [AUTO_CONTINUE_PATH, TWO_AGENT_PATH]
        all_passed = True
        error_messages = []

        for file_path in files:
            passed, stdout, stderr = run_ruff_format_check(file_path)
            if not passed:
                all_passed = False
                msg = f"\n{file_path} has formatting issues:"
                if stdout:
                    msg += f"\n  STDOUT: {stdout}"
                if stderr:
                    msg += f"\n  STDERR: {stderr}"
                error_messages.append(msg)

        error_msg = "Formatting issues found in modified files:" + "".join(error_messages)
        assert all_passed, error_msg
