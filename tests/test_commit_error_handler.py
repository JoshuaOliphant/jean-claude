# ABOUTME: Tests for CommitErrorHandler utility class
# ABOUTME: Consolidated tests for error categorization and recovery suggestions

"""Tests for CommitErrorHandler utility class.

Consolidated from 22 separate tests to focused tests covering
essential behaviors without per-error-type redundancy.
"""

import pytest
from jean_claude.core.commit_error_handler import CommitErrorHandler


class TestCommitErrorHandlerTestFailures:
    """Test handling test failures - consolidated from 3 tests to 1."""

    def test_handle_test_failure_basic_timeout_and_many_failed(self):
        """Test handling basic test failure, timeout, and many failed tests."""
        # Basic failure
        basic_result = {
            "passed": False,
            "can_commit": False,
            "message": "Tests failed",
            "total_tests": 10,
            "failed_tests": 3,
            "error_details": {"failed_tests": ["test_one", "test_two", "test_three"]}
        }
        result = CommitErrorHandler.handle_test_failure(basic_result)
        assert result["error_type"] == "test_failure"
        assert "3 of 10" in result["error"]
        assert len(result["recovery_suggestions"]) > 0

        # Timeout failure
        timeout_result = {
            "passed": False,
            "can_commit": False,
            "message": "Tests timed out",
            "total_tests": 5,
            "failed_tests": 0,
            "error_details": {"timeout": True, "duration": 300}
        }
        result = CommitErrorHandler.handle_test_failure(timeout_result)
        assert result["error_type"] == "test_failure"
        suggestions_text = " ".join(result["recovery_suggestions"]).lower()
        assert "timeout" in suggestions_text or "timed out" in suggestions_text

        # Many failed tests (should truncate)
        many_failed_result = {
            "passed": False,
            "can_commit": False,
            "message": "Tests failed",
            "total_tests": 20,
            "failed_tests": 10,
            "error_details": {"failed_tests": [f"test_{i}" for i in range(10)]}
        }
        result = CommitErrorHandler.handle_test_failure(many_failed_result)
        assert "and 5 more" in result["error"]


class TestCommitErrorHandlerGitErrors:
    """Test handling git errors - consolidated from 10 tests to 2."""

    @pytest.mark.parametrize("git_error,expected_type", [
        ("fatal: cannot commit because you have unmerged files", "git_conflict"),
        ("error: permission denied while writing to repository", "permission_error"),
        ("pre-commit hook failed", "git_hook_failure"),
        ("fatal: not a git repository (or any of the parent directories): .git", "not_a_repository"),
        ("nothing to commit, working tree clean", "no_files_to_stage"),
        ("some random git error", "git_error"),
    ])
    def test_handle_git_error_categorization(self, git_error, expected_type):
        """Test that handle_git_error categorizes errors correctly."""
        result = CommitErrorHandler.handle_git_error(git_error, "commit")
        assert result["error_type"] == expected_type

    def test_specific_error_handlers(self):
        """Test specific error handler methods."""
        # No files to stage
        result = CommitErrorHandler.handle_no_files_to_stage()
        assert result["error_type"] == "no_files_to_stage"
        assert "no files" in result["error"].lower()
        assert len(result["recovery_suggestions"]) >= 3

        # Git conflict with files
        git_error = "CONFLICT (content): Merge conflict in src/file1.py\nCONFLICT in src/file2.py"
        result = CommitErrorHandler.handle_git_conflict(git_error)
        assert result["error_type"] == "git_conflict"
        assert "conflict" in result["error"].lower()

        # Permission error
        result = CommitErrorHandler.handle_permission_error("permission denied")
        assert result["error_type"] == "permission_error"

        # Git hook failure (pre-commit and commit-msg)
        for hook_error in ["pre-commit hook failed: pylint checks failed", "commit-msg hook failed: invalid format"]:
            result = CommitErrorHandler.handle_git_hook_failure(hook_error)
            assert result["error_type"] == "git_hook_failure"

        # Invalid beads ID
        result = CommitErrorHandler.handle_invalid_beads_id("")
        assert result["error_type"] == "invalid_beads_id"
        assert "beads" in result["error"].lower()


class TestCommitErrorHandlerFormatting:
    """Test error result formatting - consolidated from 5 tests to 1."""

    def test_format_error_result_all_options(self):
        """Test formatting error results with various options."""
        # Basic
        result = CommitErrorHandler.format_error_result(
            step="test_validation",
            error_msg="Tests failed"
        )
        assert result["success"] is False
        assert result["commit_sha"] is None
        assert result["error"] == "Tests failed"
        assert result["step"] == "test_validation"

        # With suggestions and type
        suggestions = ["Fix tests", "Run locally"]
        result = CommitErrorHandler.format_error_result(
            step="test_validation",
            error_msg="Tests failed",
            recovery_suggestions=suggestions,
            error_type="test_failure"
        )
        assert result["recovery_suggestions"] == suggestions
        assert result["error_type"] == "test_failure"

        # With additional details
        details = {"failed_count": 3, "total_count": 10}
        result = CommitErrorHandler.format_error_result(
            step="test_validation",
            error_msg="Tests failed",
            additional_details=details
        )
        assert result["details"] == details


class TestCommitErrorHandlerEnhanceMessage:
    """Test error message enhancement - consolidated from 3 tests to 1."""

    def test_enhance_error_message(self):
        """Test enhancing error messages with suggestions."""
        base_error = "Cannot commit: Tests failed"
        suggestions = ["Fix the tests", "Run locally"]

        # With suggestions
        enhanced = CommitErrorHandler.enhance_error_message(base_error, suggestions)
        assert base_error in enhanced
        assert "Recovery suggestions:" in enhanced
        assert "1. Fix the tests" in enhanced
        assert "2. Run locally" in enhanced

        # No suggestions - returns base error
        assert CommitErrorHandler.enhance_error_message(base_error, []) == base_error

        # Preserves formatting
        multiline = "Cannot commit: Tests failed\nFailed tests: test_one, test_two"
        enhanced = CommitErrorHandler.enhance_error_message(multiline, ["Fix tests"])
        assert multiline in enhanced
        assert "test_one" in enhanced
