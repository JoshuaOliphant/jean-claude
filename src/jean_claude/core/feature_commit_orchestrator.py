"""FeatureCommitOrchestrator for coordinating the full commit workflow.

This module provides functionality to orchestrate the complete commit workflow:
1. Run tests to validate the implementation
2. Stage relevant files
3. Generate a conventional commit message
4. Execute the git commit
5. Handle errors with appropriate rollback
"""

import subprocess
import re
from pathlib import Path
from typing import Dict, Any, Optional, Union

from jean_claude.core.test_runner_validator import TestRunnerValidator
from jean_claude.core.git_file_stager import GitFileStager
from jean_claude.core.conventional_commit_parser import ConventionalCommitParser
from jean_claude.core.commit_body_generator import CommitBodyGenerator
from jean_claude.core.commit_message_formatter import CommitMessageFormatter
from jean_claude.core.commit_error_handler import CommitErrorHandler


class FeatureCommitOrchestrator:
    """Orchestrates the full commit workflow for a feature.

    The FeatureCommitOrchestrator coordinates all the components needed to create
    a well-formatted commit after a feature is complete. It ensures tests pass,
    stages the right files, generates a meaningful commit message, and executes
    the commit. If any step fails, it rolls back changes appropriately.

    The workflow:
    1. Run tests (TestRunnerValidator) - Block if tests fail
    2. Stage files (GitFileStager) - Identify and stage relevant files
    3. Generate commit message:
       a. Parse feature description for type/scope (ConventionalCommitParser)
       b. Generate body bullets from diff (CommitBodyGenerator)
       c. Format final message (CommitMessageFormatter)
    4. Execute git commit - Create the commit
    5. Return commit SHA on success

    If any step fails, staged files are rolled back.

    Attributes:
        repo_path: Path to the git repository
        test_command: Command to run tests
        timeout: Optional timeout for test execution
    """

    def __init__(
        self,
        repo_path: Union[str, Path, None] = None,
        test_command: str = "pytest",
        timeout: Optional[int] = None
    ):
        """Initialize the FeatureCommitOrchestrator.

        Args:
            repo_path: Path to the git repository. Defaults to current directory.
            test_command: Command to run tests (default: "pytest")
            timeout: Optional timeout in seconds for test execution
        """
        if repo_path is None:
            self.repo_path = Path.cwd()
        elif isinstance(repo_path, str):
            self.repo_path = Path(repo_path)
        else:
            self.repo_path = repo_path

        self.test_command = test_command
        self.timeout = timeout

    def run_tests(self) -> Dict[str, Any]:
        """Run tests before allowing commit.

        Returns:
            Dictionary containing:
                - passed: Boolean indicating if tests passed
                - can_commit: Boolean indicating if commit is allowed
                - message: Human-readable message
                - total_tests: Number of tests run
                - failed_tests: Number of failed tests
                - error_details: Optional error details if tests failed

        Example:
            >>> orchestrator = FeatureCommitOrchestrator()
            >>> result = orchestrator.run_tests()
            >>> if result["passed"]:
            ...     print("Tests passed, ready to commit!")
        """
        validator = TestRunnerValidator(
            test_command=self.test_command,
            repo_path=self.repo_path,
            timeout=self.timeout
        )

        result = validator.validate()
        return result

    def stage_files(self, feature_context: str = "") -> Dict[str, Any]:
        """Stage files for the commit.

        Args:
            feature_context: Optional context about the feature to help identify
                           relevant files.

        Returns:
            Dictionary containing:
                - success: Boolean indicating if staging succeeded
                - staged_files: List of files that were staged
                - error: Optional error message if staging failed

        Example:
            >>> orchestrator = FeatureCommitOrchestrator()
            >>> result = orchestrator.stage_files("authentication")
            >>> if result["success"]:
            ...     print(f"Staged {len(result['staged_files'])} files")
        """
        stager = GitFileStager(repo_path=self.repo_path)

        try:
            # Analyze which files should be staged
            files_to_stage = stager.analyze_files_for_staging(feature_context)

            if not files_to_stage:
                return {
                    "success": False,
                    "staged_files": [],
                    "error": "No files to stage"
                }

            # Stage the files using git add
            for filepath in files_to_stage:
                result = subprocess.run(
                    ['git', 'add', filepath],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=False
                )

                if result.returncode != 0:
                    return {
                        "success": False,
                        "staged_files": [],
                        "error": f"Failed to stage {filepath}: {result.stderr}"
                    }

            return {
                "success": True,
                "staged_files": files_to_stage,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "staged_files": [],
                "error": f"Error staging files: {str(e)}"
            }

    def generate_commit_message(
        self,
        feature_name: str,
        feature_description: str,
        beads_task_id: str,
        feature_number: int,
        total_features: int
    ) -> Dict[str, Any]:
        """Generate a conventional commit message.

        Args:
            feature_name: Name of the feature
            feature_description: Description of the feature
            beads_task_id: Beads task identifier
            feature_number: Current feature number
            total_features: Total number of features

        Returns:
            Dictionary containing:
                - success: Boolean indicating if generation succeeded
                - message: The generated commit message
                - error: Optional error message if generation failed

        Example:
            >>> orchestrator = FeatureCommitOrchestrator()
            >>> result = orchestrator.generate_commit_message(
            ...     feature_name="login",
            ...     feature_description="Add login functionality",
            ...     beads_task_id="task.1",
            ...     feature_number=1,
            ...     total_features=10
            ... )
            >>> print(result["message"])
        """
        try:
            # Parse feature description to get commit type and scope
            parser = ConventionalCommitParser()
            parsed = parser.parse(feature_description)

            commit_type = parsed["type"]
            scope = parsed["scope"]

            # Generate body bullets from git diff
            body_generator = CommitBodyGenerator(repo_path=self.repo_path)
            body_items = body_generator.generate(staged_only=True)

            # Format the final commit message
            formatter = CommitMessageFormatter(
                commit_type=commit_type,
                scope=scope,
                summary=feature_name,
                body_items=body_items,
                beads_task_id=beads_task_id,
                feature_number=feature_number
            )

            message = formatter.format()

            return {
                "success": True,
                "message": message,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "message": None,
                "error": f"Failed to generate commit message: {str(e)}"
            }

    def extract_commit_sha(self, output: str) -> Optional[str]:
        """Extract commit SHA from git commit output.

        Args:
            output: Git commit command output

        Returns:
            The commit SHA if found, None otherwise

        Example:
            >>> orchestrator = FeatureCommitOrchestrator()
            >>> sha = orchestrator.extract_commit_sha("[main abc1234] feat: test")
            >>> print(sha)
            abc1234
        """
        # Pattern: [branch_name SHA] commit message
        match = re.search(r'\[[\w\-/]+\s+([a-f0-9]{7})\]', output)
        if match:
            return match.group(1)
        return None

    def execute_commit(self, commit_message: str) -> Dict[str, Any]:
        """Execute the git commit.

        Args:
            commit_message: The commit message to use

        Returns:
            Dictionary containing:
                - success: Boolean indicating if commit succeeded
                - commit_sha: The SHA of the created commit (if successful)
                - error: Optional error message if commit failed

        Example:
            >>> orchestrator = FeatureCommitOrchestrator()
            >>> result = orchestrator.execute_commit("feat: add feature")
            >>> if result["success"]:
            ...     print(f"Committed as {result['commit_sha']}")
        """
        try:
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "commit_sha": None,
                    "error": f"Git commit failed: {result.stderr}"
                }

            # Extract commit SHA from output
            commit_sha = self.extract_commit_sha(result.stdout)

            return {
                "success": True,
                "commit_sha": commit_sha,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "commit_sha": None,
                "error": f"Error executing commit: {str(e)}"
            }

    def rollback_staged_files(self) -> None:
        """Roll back any staged files.

        This is called when an error occurs after files have been staged
        but before the commit succeeds.

        Example:
            >>> orchestrator = FeatureCommitOrchestrator()
            >>> orchestrator.rollback_staged_files()
        """
        try:
            subprocess.run(
                ['git', 'reset', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
        except Exception:
            # Best effort rollback, don't raise if it fails
            pass

    def commit_feature(
        self,
        feature_name: str,
        feature_description: str,
        beads_task_id: str,
        feature_number: int,
        total_features: int,
        feature_context: str = ""
    ) -> Dict[str, Any]:
        """Execute the complete commit workflow for a feature.

        This is the main entry point that orchestrates all steps:
        1. Run tests
        2. Stage files
        3. Generate commit message
        4. Execute commit
        5. Handle errors with rollback

        Args:
            feature_name: Name of the feature
            feature_description: Description of the feature
            beads_task_id: Beads task identifier
            feature_number: Current feature number
            total_features: Total number of features
            feature_context: Optional context about the feature

        Returns:
            Dictionary containing:
                - success: Boolean indicating if commit workflow succeeded
                - commit_sha: The SHA of the created commit (if successful)
                - error: Detailed error message if any step failed
                - step: Which step failed (if applicable)

        Example:
            >>> orchestrator = FeatureCommitOrchestrator()
            >>> result = orchestrator.commit_feature(
            ...     feature_name="login",
            ...     feature_description="Add login functionality",
            ...     beads_task_id="task.1",
            ...     feature_number=1,
            ...     total_features=10
            ... )
            >>> if result["success"]:
            ...     print(f"Feature committed: {result['commit_sha']}")
            ... else:
            ...     print(f"Commit failed at {result['step']}: {result['error']}")
        """
        # Step 0: Validate Beads ID
        if not beads_task_id or not beads_task_id.strip():
            error_info = CommitErrorHandler.handle_invalid_beads_id(beads_task_id)
            enhanced_error = CommitErrorHandler.enhance_error_message(
                error_info["error"],
                error_info["recovery_suggestions"]
            )
            return {
                "success": False,
                "commit_sha": None,
                "error": enhanced_error,
                "step": "validation",
                "recovery_suggestions": error_info["recovery_suggestions"],
                "error_type": error_info["error_type"]
            }

        # Step 1: Run tests
        test_result = self.run_tests()
        if not test_result["can_commit"]:
            # Use error handler to provide enhanced error message
            error_info = CommitErrorHandler.handle_test_failure(test_result)
            enhanced_error = CommitErrorHandler.enhance_error_message(
                error_info["error"],
                error_info["recovery_suggestions"]
            )
            return {
                "success": False,
                "commit_sha": None,
                "error": enhanced_error,
                "step": "test_validation",
                "details": test_result.get("error_details"),
                "recovery_suggestions": error_info["recovery_suggestions"],
                "error_type": error_info["error_type"]
            }

        # Step 2: Stage files
        stage_result = self.stage_files(feature_context=feature_context)
        if not stage_result["success"]:
            # Check if it's a "no files to stage" error or other error
            stage_error = stage_result.get("error", "")
            if "no files" in stage_error.lower():
                error_info = CommitErrorHandler.handle_no_files_to_stage()
                enhanced_error = CommitErrorHandler.enhance_error_message(
                    error_info["error"],
                    error_info["recovery_suggestions"]
                )
            else:
                # Try to categorize git error
                error_info = CommitErrorHandler.handle_git_error(stage_error, "stage")
                enhanced_error = CommitErrorHandler.enhance_error_message(
                    error_info["error"],
                    error_info["recovery_suggestions"]
                )

            return {
                "success": False,
                "commit_sha": None,
                "error": enhanced_error,
                "step": "file_staging",
                "recovery_suggestions": error_info["recovery_suggestions"],
                "error_type": error_info["error_type"]
            }

        # Step 3: Generate commit message
        message_result = self.generate_commit_message(
            feature_name=feature_name,
            feature_description=feature_description,
            beads_task_id=beads_task_id,
            feature_number=feature_number,
            total_features=total_features
        )

        if not message_result["success"]:
            # Rollback staged files
            self.rollback_staged_files()

            # Provide enhanced error message
            base_error = message_result.get("error", "Failed to generate commit message")
            recovery_suggestions = [
                "Verify feature description is valid and descriptive",
                "Check that git diff returns valid output",
                "Ensure ConventionalCommitParser can parse the feature type",
                "Review feature context for any unusual characters or format"
            ]
            enhanced_error = CommitErrorHandler.enhance_error_message(
                base_error,
                recovery_suggestions
            )

            return {
                "success": False,
                "commit_sha": None,
                "error": enhanced_error,
                "step": "message_generation",
                "recovery_suggestions": recovery_suggestions,
                "error_type": "message_generation_failure"
            }

        # Step 4: Execute commit
        commit_result = self.execute_commit(message_result["message"])

        if not commit_result["success"]:
            # Rollback staged files
            self.rollback_staged_files()

            # Provide enhanced error message based on git error
            git_error = commit_result.get("error", "")
            error_info = CommitErrorHandler.handle_git_error(git_error, "commit")
            enhanced_error = CommitErrorHandler.enhance_error_message(
                error_info["error"],
                error_info["recovery_suggestions"]
            )

            return {
                "success": False,
                "commit_sha": None,
                "error": enhanced_error,
                "step": "commit_execution",
                "recovery_suggestions": error_info["recovery_suggestions"],
                "error_type": error_info["error_type"]
            }

        # Success!
        return {
            "success": True,
            "commit_sha": commit_result["commit_sha"],
            "error": None,
            "step": None
        }
