"""Commit error handler for providing clear error messages and recovery suggestions.

This module provides utilities for handling various commit-related errors
and providing clear, actionable error messages with recovery suggestions.
"""

from typing import Dict, Any, Optional
import re


class CommitErrorHandler:
    """Handles commit errors and provides recovery suggestions.

    This class analyzes different types of commit failures and provides
    clear error messages along with actionable recovery suggestions to help
    the agent understand what went wrong and how to fix it.
    """

    @staticmethod
    def handle_test_failure(test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle test failure and provide recovery suggestions.

        Args:
            test_result: Result from TestRunnerValidator containing test failure details

        Returns:
            Dictionary with enhanced error message and recovery suggestions
        """
        failed_count = test_result.get("failed_tests", 0)
        total_count = test_result.get("total_tests", 0)
        error_details = test_result.get("error_details", {})

        # Build detailed error message
        error_msg = f"Cannot commit: {failed_count} of {total_count} tests failed"

        # Add specific failed test names if available
        if "failed_tests" in error_details:
            failed_test_names = error_details["failed_tests"]
            if failed_test_names:
                error_msg += f"\nFailed tests: {', '.join(failed_test_names[:5])}"
                if len(failed_test_names) > 5:
                    error_msg += f" (and {len(failed_test_names) - 5} more)"

        # Add recovery suggestions
        recovery_suggestions = [
            "Fix the failing tests before attempting to commit",
            "Run tests locally to identify the root cause",
            "Check test output for assertion errors or exceptions"
        ]

        # Check for timeout
        if error_details.get("timeout"):
            recovery_suggestions.append(
                "Tests timed out - consider optimizing slow tests or increasing timeout"
            )

        return {
            "error": error_msg,
            "recovery_suggestions": recovery_suggestions,
            "error_type": "test_failure"
        }

    @staticmethod
    def handle_no_files_to_stage() -> Dict[str, Any]:
        """Handle 'no files to stage' error.

        Returns:
            Dictionary with error message and recovery suggestions
        """
        error_msg = "Cannot commit: No files to stage"

        recovery_suggestions = [
            "Verify that changes were made to the codebase",
            "Check if files are already committed (run 'git status')",
            "Ensure file modifications are saved",
            "Review the feature implementation to confirm files were actually modified"
        ]

        return {
            "error": error_msg,
            "recovery_suggestions": recovery_suggestions,
            "error_type": "no_files_to_stage"
        }

    @staticmethod
    def handle_git_conflict(git_error: str) -> Dict[str, Any]:
        """Handle git conflict errors.

        Args:
            git_error: Error message from git command

        Returns:
            Dictionary with error message and recovery suggestions
        """
        # Extract conflict file if mentioned in error
        conflict_files = []
        if "conflict" in git_error.lower():
            # Try to extract file paths
            file_match = re.findall(r'(?:conflict|CONFLICT).*?([a-zA-Z0-9_/.\-]+\.[a-zA-Z0-9]+)', git_error, re.IGNORECASE)
            conflict_files = file_match

        error_msg = "Cannot commit: Git repository has conflicts"

        if conflict_files:
            error_msg += f"\nConflicting files: {', '.join(conflict_files[:3])}"

        recovery_suggestions = [
            "Resolve merge conflicts before committing",
            "Run 'git status' to see which files have conflicts",
            "Edit conflicting files to resolve markers (<<<<<<, ======, >>>>>>)",
            "After resolving, stage the files with 'git add'",
            "Alternatively, abort the merge with 'git merge --abort'"
        ]

        return {
            "error": error_msg,
            "recovery_suggestions": recovery_suggestions,
            "error_type": "git_conflict"
        }

    @staticmethod
    def handle_permission_error(git_error: str) -> Dict[str, Any]:
        """Handle permission errors during git operations.

        Args:
            git_error: Error message from git command

        Returns:
            Dictionary with error message and recovery suggestions
        """
        error_msg = "Cannot commit: Insufficient permissions"

        recovery_suggestions = [
            "Check file and directory permissions in the repository",
            "Ensure you have write access to the .git directory",
            "Verify ownership of repository files (may need 'sudo chown')",
            "Check if .git directory is read-only",
            "Ensure no other process has locked the repository"
        ]

        # Add specific suggestions based on error details
        if "permission denied" in git_error.lower():
            recovery_suggestions.insert(1, "Some files or directories are not writable by your user")
        elif "insufficient permission" in git_error.lower():
            recovery_suggestions.insert(1, "Git database permissions are incorrect")

        return {
            "error": error_msg,
            "recovery_suggestions": recovery_suggestions,
            "error_type": "permission_error"
        }

    @staticmethod
    def handle_git_hook_failure(git_error: str) -> Dict[str, Any]:
        """Handle git hook failures (pre-commit, commit-msg, etc.).

        Args:
            git_error: Error message from git command

        Returns:
            Dictionary with error message and recovery suggestions
        """
        # Identify which hook failed
        hook_type = "unknown"
        if "pre-commit" in git_error.lower():
            hook_type = "pre-commit"
        elif "commit-msg" in git_error.lower():
            hook_type = "commit-msg"
        elif "prepare-commit-msg" in git_error.lower():
            hook_type = "prepare-commit-msg"

        error_msg = f"Cannot commit: {hook_type} hook failed"

        recovery_suggestions = [
            f"Fix the issues reported by the {hook_type} hook",
            "Review hook output for specific validation errors",
            "Common issues: code formatting, linting errors, test requirements",
        ]

        # Add hook-specific suggestions
        if hook_type == "pre-commit":
            recovery_suggestions.extend([
                "Check for linting errors (pylint, flake8, black, etc.)",
                "Ensure code formatting meets standards",
                "If needed, bypass hook temporarily with 'git commit --no-verify' (not recommended)"
            ])
        elif hook_type == "commit-msg":
            recovery_suggestions.extend([
                "Verify commit message format meets repository standards",
                "Check for required trailers or conventional commit format"
            ])

        return {
            "error": error_msg,
            "recovery_suggestions": recovery_suggestions,
            "error_type": "git_hook_failure"
        }

    @staticmethod
    def handle_invalid_beads_id(beads_id: str) -> Dict[str, Any]:
        """Handle invalid Beads ID errors.

        Args:
            beads_id: The invalid Beads ID

        Returns:
            Dictionary with error message and recovery suggestions
        """
        error_msg = f"Cannot commit: Invalid Beads task ID: '{beads_id}'"

        recovery_suggestions = [
            "Ensure Beads task ID is provided and not empty",
            "Verify the task ID format matches expected pattern",
            "Check task metadata to ensure ID was properly set",
            "Valid format example: 'task-name-abc.123'"
        ]

        return {
            "error": error_msg,
            "recovery_suggestions": recovery_suggestions,
            "error_type": "invalid_beads_id"
        }

    @staticmethod
    def handle_git_error(git_error: str, operation: str = "commit") -> Dict[str, Any]:
        """Handle generic git errors with intelligent categorization.

        Args:
            git_error: Error message from git command
            operation: Git operation that failed (commit, add, etc.)

        Returns:
            Dictionary with error message and recovery suggestions
        """
        git_error_lower = git_error.lower()

        # Try to categorize the error
        if "conflict" in git_error_lower or "merge" in git_error_lower:
            return CommitErrorHandler.handle_git_conflict(git_error)
        elif "permission" in git_error_lower or "denied" in git_error_lower:
            return CommitErrorHandler.handle_permission_error(git_error)
        elif "hook" in git_error_lower:
            return CommitErrorHandler.handle_git_hook_failure(git_error)
        elif "not a git repository" in git_error_lower:
            return {
                "error": f"Cannot {operation}: Not a git repository",
                "recovery_suggestions": [
                    "Initialize a git repository with 'git init'",
                    "Verify you're in the correct directory",
                    "Check if .git directory exists"
                ],
                "error_type": "not_a_repository"
            }
        elif "nothing to commit" in git_error_lower:
            return CommitErrorHandler.handle_no_files_to_stage()
        else:
            # Generic git error
            return {
                "error": f"Git {operation} failed: {git_error.strip()}",
                "recovery_suggestions": [
                    "Review the git error message above",
                    "Run 'git status' to check repository state",
                    "Ensure repository is in a clean state",
                    "Check git configuration and permissions"
                ],
                "error_type": "git_error"
            }

    @staticmethod
    def format_error_result(
        step: str,
        error_msg: str,
        recovery_suggestions: Optional[list] = None,
        error_type: Optional[str] = None,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format a complete error result with consistent structure.

        Args:
            step: The step where the error occurred
            error_msg: The error message
            recovery_suggestions: Optional list of recovery suggestions
            error_type: Optional error type classification
            additional_details: Optional additional error details

        Returns:
            Formatted error result dictionary
        """
        result = {
            "success": False,
            "commit_sha": None,
            "error": error_msg,
            "step": step
        }

        if recovery_suggestions:
            result["recovery_suggestions"] = recovery_suggestions

        if error_type:
            result["error_type"] = error_type

        if additional_details:
            result["details"] = additional_details

        return result

    @staticmethod
    def enhance_error_message(base_error: str, recovery_suggestions: list) -> str:
        """Enhance error message by appending recovery suggestions.

        Args:
            base_error: The base error message
            recovery_suggestions: List of recovery suggestions

        Returns:
            Enhanced error message with suggestions
        """
        enhanced = base_error

        if recovery_suggestions:
            enhanced += "\n\nRecovery suggestions:"
            for i, suggestion in enumerate(recovery_suggestions, 1):
                enhanced += f"\n  {i}. {suggestion}"

        return enhanced
