"""Tests for FeatureCommitOrchestrator class."""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

from jean_claude.core.feature_commit_orchestrator import FeatureCommitOrchestrator


class TestFeatureCommitOrchestrator:
    """Test FeatureCommitOrchestrator class."""

    def test_init_with_defaults(self):
        """Test initializing orchestrator with default parameters."""
        orchestrator = FeatureCommitOrchestrator()

        assert orchestrator.repo_path == Path.cwd()
        assert orchestrator.test_command == "pytest"
        assert orchestrator.timeout is None

    def test_init_with_custom_params(self):
        """Test initializing orchestrator with custom parameters."""
        repo_path = Path("/tmp/test-repo")
        test_command = "python -m pytest -v"
        timeout = 300

        orchestrator = FeatureCommitOrchestrator(
            repo_path=repo_path,
            test_command=test_command,
            timeout=timeout
        )

        assert orchestrator.repo_path == repo_path
        assert orchestrator.test_command == test_command
        assert orchestrator.timeout == timeout

    @patch('jean_claude.core.feature_commit_orchestrator.TestRunnerValidator')
    def test_run_tests_passes(self, mock_validator_class):
        """Test that run_tests returns True when tests pass."""
        # Setup mock
        mock_validator = MagicMock()
        mock_validator.validate.return_value = {
            "can_commit": True,
            "passed": True,
            "message": "All tests passed! (5 tests)",
            "total_tests": 5,
            "failed_tests": 0
        }
        mock_validator_class.return_value = mock_validator

        orchestrator = FeatureCommitOrchestrator()
        result = orchestrator.run_tests()

        assert result["passed"] is True
        assert result["can_commit"] is True
        assert "All tests passed" in result["message"]

    @patch('jean_claude.core.feature_commit_orchestrator.TestRunnerValidator')
    def test_run_tests_fails(self, mock_validator_class):
        """Test that run_tests returns False when tests fail."""
        # Setup mock
        mock_validator = MagicMock()
        mock_validator.validate.return_value = {
            "can_commit": False,
            "passed": False,
            "message": "Tests failed: 2 of 5 tests failed",
            "total_tests": 5,
            "failed_tests": 2,
            "error_details": {
                "failed_tests": ["test_one", "test_two"]
            }
        }
        mock_validator_class.return_value = mock_validator

        orchestrator = FeatureCommitOrchestrator()
        result = orchestrator.run_tests()

        assert result["passed"] is False
        assert result["can_commit"] is False
        assert "failed" in result["message"].lower()

    @patch('jean_claude.core.feature_commit_orchestrator.GitFileStager')
    def test_stage_files_success(self, mock_stager_class):
        """Test staging files for commit."""
        # Setup mock
        mock_stager = MagicMock()
        mock_stager.analyze_files_for_staging.return_value = [
            "src/feature.py",
            "tests/test_feature.py"
        ]
        mock_stager_class.return_value = mock_stager

        orchestrator = FeatureCommitOrchestrator()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = orchestrator.stage_files(feature_context="test feature")

            assert result["success"] is True
            assert len(result["staged_files"]) == 2
            assert "src/feature.py" in result["staged_files"]

            # Verify git add was called
            mock_run.assert_called()

    @patch('jean_claude.core.feature_commit_orchestrator.GitFileStager')
    def test_stage_files_no_files(self, mock_stager_class):
        """Test staging when no files to stage."""
        # Setup mock
        mock_stager = MagicMock()
        mock_stager.analyze_files_for_staging.return_value = []
        mock_stager_class.return_value = mock_stager

        orchestrator = FeatureCommitOrchestrator()
        result = orchestrator.stage_files()

        assert result["success"] is False
        assert result["error"] == "No files to stage"
        assert result["staged_files"] == []

    @patch('jean_claude.core.feature_commit_orchestrator.ConventionalCommitParser')
    @patch('jean_claude.core.feature_commit_orchestrator.CommitBodyGenerator')
    @patch('jean_claude.core.feature_commit_orchestrator.CommitMessageFormatter')
    def test_generate_commit_message(self, mock_formatter_class, mock_body_gen_class, mock_parser_class):
        """Test generating commit message."""
        # Setup mocks
        mock_parser = MagicMock()
        mock_parser.parse.return_value = {"type": "feat", "scope": "auth"}
        mock_parser_class.return_value = mock_parser

        mock_body_gen = MagicMock()
        mock_body_gen.generate.return_value = ["Add login functionality", "Add JWT support"]
        mock_body_gen_class.return_value = mock_body_gen

        mock_formatter = MagicMock()
        mock_formatter.format.return_value = "feat(auth): add login\n\n- Add login functionality\n- Add JWT support\n\nBeads-Task-Id: test.1\nFeature-Number: 1"
        mock_formatter_class.return_value = mock_formatter

        orchestrator = FeatureCommitOrchestrator()
        result = orchestrator.generate_commit_message(
            feature_name="add login",
            feature_description="Add login functionality",
            beads_task_id="test.1",
            feature_number=1,
            total_features=10
        )

        assert result["success"] is True
        assert "feat(auth): add login" in result["message"]

    @patch('subprocess.run')
    def test_execute_commit_success(self, mock_run):
        """Test executing git commit successfully."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[main abc1234] feat(auth): add login\n 2 files changed, 50 insertions(+)"
        mock_run.return_value = mock_result

        orchestrator = FeatureCommitOrchestrator()
        result = orchestrator.execute_commit("feat(auth): add login\n\nTest commit")

        assert result["success"] is True
        assert result["commit_sha"] is not None
        assert "abc1234" in result["commit_sha"]

    @patch('subprocess.run')
    def test_execute_commit_failure(self, mock_run):
        """Test handling commit execution failure."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "fatal: unable to commit"
        mock_run.return_value = mock_result

        orchestrator = FeatureCommitOrchestrator()
        result = orchestrator.execute_commit("test commit message")

        assert result["success"] is False
        assert "error" in result
        assert "unable to commit" in result["error"]

    @patch('subprocess.run')
    def test_rollback_staged_files(self, mock_run):
        """Test rolling back staged files."""
        mock_run.return_value = MagicMock(returncode=0)

        orchestrator = FeatureCommitOrchestrator()
        orchestrator.rollback_staged_files()

        # Verify git reset was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "reset" in args

    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.run_tests')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.stage_files')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.generate_commit_message')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.execute_commit')
    def test_commit_feature_success(self, mock_commit, mock_generate, mock_stage, mock_tests):
        """Test complete commit workflow succeeds."""
        # Setup mocks
        mock_tests.return_value = {"passed": True, "can_commit": True, "message": "Tests passed"}
        mock_stage.return_value = {"success": True, "staged_files": ["file.py"]}
        mock_generate.return_value = {"success": True, "message": "feat: test"}
        mock_commit.return_value = {"success": True, "commit_sha": "abc1234"}

        orchestrator = FeatureCommitOrchestrator()
        result = orchestrator.commit_feature(
            feature_name="test-feature",
            feature_description="Test feature",
            beads_task_id="test.1",
            feature_number=1,
            total_features=10
        )

        assert result["success"] is True
        assert result["commit_sha"] == "abc1234"

        # Verify all steps were called
        mock_tests.assert_called_once()
        mock_stage.assert_called_once()
        mock_generate.assert_called_once()
        mock_commit.assert_called_once()

    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.run_tests')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.rollback_staged_files')
    def test_commit_feature_tests_fail(self, mock_rollback, mock_tests):
        """Test commit workflow fails when tests fail."""
        # Setup mock
        mock_tests.return_value = {
            "passed": False,
            "can_commit": False,
            "message": "Tests failed: 2 of 5 tests failed",
            "error_details": {"failed_tests": ["test_one"]}
        }

        orchestrator = FeatureCommitOrchestrator()
        result = orchestrator.commit_feature(
            feature_name="test-feature",
            feature_description="Test feature",
            beads_task_id="test.1",
            feature_number=1,
            total_features=10
        )

        assert result["success"] is False
        assert "tests" in result["error"].lower()

        # Rollback should not be called since nothing was staged yet
        mock_rollback.assert_not_called()

    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.run_tests')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.stage_files')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.rollback_staged_files')
    def test_commit_feature_no_files_to_stage(self, mock_rollback, mock_stage, mock_tests):
        """Test commit workflow fails when no files to stage."""
        # Setup mocks
        mock_tests.return_value = {"passed": True, "can_commit": True}
        mock_stage.return_value = {"success": False, "error": "No files to stage", "staged_files": []}

        orchestrator = FeatureCommitOrchestrator()
        result = orchestrator.commit_feature(
            feature_name="test-feature",
            feature_description="Test feature",
            beads_task_id="test.1",
            feature_number=1,
            total_features=10
        )

        assert result["success"] is False
        assert "no files" in result["error"].lower()

    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.run_tests')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.stage_files')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.generate_commit_message')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.execute_commit')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.rollback_staged_files')
    def test_commit_feature_commit_fails_with_rollback(
        self, mock_rollback, mock_commit, mock_generate, mock_stage, mock_tests
    ):
        """Test commit workflow rolls back when commit execution fails."""
        # Setup mocks
        mock_tests.return_value = {"passed": True, "can_commit": True}
        mock_stage.return_value = {"success": True, "staged_files": ["file.py"]}
        mock_generate.return_value = {"success": True, "message": "feat: test"}
        mock_commit.return_value = {"success": False, "error": "Commit failed"}

        orchestrator = FeatureCommitOrchestrator()
        result = orchestrator.commit_feature(
            feature_name="test-feature",
            feature_description="Test feature",
            beads_task_id="test.1",
            feature_number=1,
            total_features=10
        )

        assert result["success"] is False
        assert "commit failed" in result["error"].lower()

        # Rollback should be called
        mock_rollback.assert_called_once()

    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.run_tests')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.stage_files')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.generate_commit_message')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.rollback_staged_files')
    def test_commit_feature_message_generation_fails_with_rollback(
        self, mock_rollback, mock_generate, mock_stage, mock_tests
    ):
        """Test commit workflow rolls back when message generation fails."""
        # Setup mocks
        mock_tests.return_value = {"passed": True, "can_commit": True}
        mock_stage.return_value = {"success": True, "staged_files": ["file.py"]}
        mock_generate.return_value = {"success": False, "error": "Failed to generate message"}

        orchestrator = FeatureCommitOrchestrator()
        result = orchestrator.commit_feature(
            feature_name="test-feature",
            feature_description="Test feature",
            beads_task_id="test.1",
            feature_number=1,
            total_features=10
        )

        assert result["success"] is False
        assert "failed to generate message" in result["error"].lower()

        # Rollback should be called
        mock_rollback.assert_called_once()

    def test_extract_commit_sha_from_output(self):
        """Test extracting commit SHA from git commit output."""
        orchestrator = FeatureCommitOrchestrator()

        # Test various output formats
        outputs = [
            "[main abc1234] feat: test commit",
            "[feature-branch def5678] fix(auth): bug fix",
            "[dev 9876543] refactor: cleanup\n 5 files changed",
        ]

        expected_shas = ["abc1234", "def5678", "9876543"]

        for output, expected_sha in zip(outputs, expected_shas):
            sha = orchestrator.extract_commit_sha(output)
            assert sha == expected_sha

    def test_extract_commit_sha_no_match(self):
        """Test extracting commit SHA when no match found."""
        orchestrator = FeatureCommitOrchestrator()

        sha = orchestrator.extract_commit_sha("No SHA in this output")
        assert sha is None

    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.run_tests')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.stage_files')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.generate_commit_message')
    @patch('jean_claude.core.feature_commit_orchestrator.FeatureCommitOrchestrator.execute_commit')
    def test_commit_feature_with_feature_context(self, mock_commit, mock_generate, mock_stage, mock_tests):
        """Test commit feature passes context correctly."""
        # Setup mocks
        mock_tests.return_value = {"passed": True, "can_commit": True}
        mock_stage.return_value = {"success": True, "staged_files": ["file.py"]}
        mock_generate.return_value = {"success": True, "message": "feat: test"}
        mock_commit.return_value = {"success": True, "commit_sha": "abc1234"}

        orchestrator = FeatureCommitOrchestrator()
        result = orchestrator.commit_feature(
            feature_name="auth-feature",
            feature_description="Add authentication",
            beads_task_id="test.1",
            feature_number=2,
            total_features=10,
            feature_context="authentication system"
        )

        assert result["success"] is True

        # Verify stage_files was called with context
        mock_stage.assert_called_once()
        call_kwargs = mock_stage.call_args[1]
        assert call_kwargs.get("feature_context") == "authentication system"

    def test_init_with_string_repo_path(self):
        """Test initializing with string repo path converts to Path."""
        orchestrator = FeatureCommitOrchestrator(repo_path="/tmp/test")

        assert isinstance(orchestrator.repo_path, Path)
        assert str(orchestrator.repo_path) == "/tmp/test"

    @patch('subprocess.run')
    def test_execute_commit_extracts_sha(self, mock_run):
        """Test that execute_commit properly extracts SHA from output."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[main 1a2b3c4] feat: new feature\n 3 files changed, 100 insertions(+)"
        mock_run.return_value = mock_result

        orchestrator = FeatureCommitOrchestrator()
        result = orchestrator.execute_commit("feat: new feature")

        assert result["success"] is True
        assert result["commit_sha"] == "1a2b3c4"
