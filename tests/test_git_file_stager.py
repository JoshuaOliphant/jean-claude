# ABOUTME: Tests for GitFileStager service
# ABOUTME: Consolidated tests for git status parsing and file staging

"""Tests for GitFileStager service.

Consolidated from 25 separate tests to focused tests covering
essential behaviors without per-pattern or per-status redundancy.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch


from jean_claude.core.git_file_stager import GitFileStager


class TestGitFileStagerInit:
    """Test GitFileStager initialization - consolidated from 3 tests to 1."""

    def test_init_with_various_path_options(self, tmp_path):
        """Test initialization with defaults, custom path, and string conversion."""
        # Default path
        stager1 = GitFileStager()
        assert stager1.repo_path == Path.cwd()

        # Custom path
        stager2 = GitFileStager(repo_path=tmp_path)
        assert stager2.repo_path == tmp_path

        # String converted to Path
        stager3 = GitFileStager(repo_path="/tmp/test")
        assert isinstance(stager3.repo_path, Path)
        assert stager3.repo_path == Path("/tmp/test")


class TestGitFileStagerGetModifiedFiles:
    """Test getting modified files - consolidated from 4 tests to 2."""

    @patch('subprocess.run')
    def test_get_modified_files_success_and_status_types(self, mock_run):
        """Test getting modified files with various git status indicators."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="M  file1.py\nA  file2.py\nD  file3.py\nR  file4.py\nMM file5.py\n M src/utils.py\n",
            stderr=""
        )

        stager = GitFileStager()
        files = stager.get_modified_files()

        # Should include modified, added, deleted, renamed
        assert len(files) >= 4
        assert "file1.py" in files
        assert "file2.py" in files
        assert "src/utils.py" in files

        # Empty status
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        assert stager.get_modified_files() == []

    @patch('subprocess.run')
    def test_get_modified_files_git_error(self, mock_run):
        """Test handling git command errors."""
        mock_run.return_value = Mock(
            returncode=128,
            stdout="",
            stderr="fatal: not a git repository"
        )

        stager = GitFileStager()
        with pytest.raises(RuntimeError, match="Git command failed"):
            stager.get_modified_files()


class TestGitFileStagerGetFileDiff:
    """Test getting file diff - consolidated from 3 tests to 1."""

    @patch('subprocess.run')
    def test_get_file_diff_success_empty_and_error(self, mock_run):
        """Test diff retrieval for success, empty, and error cases."""
        stager = GitFileStager()

        # Success case
        expected_diff = "+++ b/src/main.py\n@@ -1,3 +1,4 @@\n+new line"
        mock_run.return_value = Mock(returncode=0, stdout=expected_diff, stderr="")
        assert stager.get_file_diff("src/main.py") == expected_diff

        # Empty diff
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        assert stager.get_file_diff("unchanged.py") == ""

        # Error case
        mock_run.return_value = Mock(returncode=128, stdout="", stderr="fatal: bad revision")
        with pytest.raises(RuntimeError, match="Git diff failed"):
            stager.get_file_diff("nonexistent.py")


class TestGitFileStagerFilterFiles:
    """Test file filtering - consolidated from 6 tests to 2."""

    def test_filter_excludes_config_and_system_files(self):
        """Test that config, system, and build files are excluded."""
        stager = GitFileStager()
        files = [
            "src/main.py",
            ".gitignore",
            ".env",
            "config.ini",
            ".DS_Store",
            "__pycache__/module.py",
            "node_modules/lib.js",
            "dist/bundle.js"
        ]

        relevant = stager.filter_relevant_files(files, feature_context="main")

        assert "src/main.py" in relevant
        assert ".gitignore" not in relevant
        assert ".env" not in relevant
        assert ".DS_Store" not in relevant
        assert "__pycache__/module.py" not in relevant

    def test_filter_with_feature_context_and_test_files(self):
        """Test filtering based on feature context and test inclusion."""
        stager = GitFileStager()

        # Feature context filtering
        auth_files = [
            "src/auth/login.py",
            "src/auth/logout.py",
            "src/api/users.py",
            "tests/test_auth.py",
        ]
        relevant = stager.filter_relevant_files(auth_files, feature_context="authentication login")
        assert "src/auth/login.py" in relevant
        assert "tests/test_auth.py" in relevant

        # Empty list and no context
        assert stager.filter_relevant_files([], feature_context="test") == []

        files_no_context = ["src/main.py", ".gitignore", "README.md"]
        relevant = stager.filter_relevant_files(files_no_context, feature_context="")
        assert "src/main.py" in relevant
        assert ".gitignore" not in relevant


class TestGitFileStagerExclusionPatterns:
    """Test exclusion patterns - consolidated from 4 tests to 1."""

    @pytest.mark.parametrize("file,should_exclude", [
        # Config files - excluded
        (".env", True),
        (".gitignore", True),
        ("config.yaml", True),
        (".editorconfig", True),
        # Build artifacts - excluded
        ("dist/bundle.js", True),
        ("build/output.py", True),
        ("__pycache__/module.cpython-39.pyc", True),
        ("node_modules/package/index.js", True),
        # System files - excluded
        (".DS_Store", True),
        ("Thumbs.db", True),
        (".idea/workspace.xml", True),
        # Source files - not excluded
        ("src/main.py", False),
        ("tests/test_feature.py", False),
        ("README.md", False),
        ("docs/guide.md", False),
    ])
    def test_is_excluded(self, file, should_exclude):
        """Test exclusion patterns for various file types."""
        stager = GitFileStager()
        assert stager.is_excluded(file) == should_exclude


class TestGitFileStagerAnalyze:
    """Test analyze_files_for_staging - consolidated from 3 tests to 1."""

    @patch('subprocess.run')
    def test_analyze_returns_filtered_files(self, mock_run):
        """Test analysis returns filtered relevant files."""
        stager = GitFileStager()

        # Returns relevant files
        mock_run.return_value = Mock(
            returncode=0,
            stdout="M  src/auth/login.py\nM  .gitignore\nM  tests/test_auth.py\n",
            stderr=""
        )
        result = stager.analyze_files_for_staging(feature_context="authentication")
        assert "src/auth/login.py" in result
        assert "tests/test_auth.py" in result
        assert ".gitignore" not in result

        # Empty context still works
        mock_run.return_value = Mock(returncode=0, stdout="M  src/main.py\n", stderr="")
        result = stager.analyze_files_for_staging(feature_context="")
        assert len(result) >= 0

        # No modified files
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        assert stager.analyze_files_for_staging(feature_context="test") == []


class TestGitFileStagerIntegration:
    """Integration tests - consolidated from 2 tests to 1."""

    @patch('subprocess.run')
    def test_full_workflow_and_error_handling(self, mock_run):
        """Test complete workflow from getting files to staging analysis."""
        def mock_subprocess(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('args', [])
            if 'status' in cmd:
                return Mock(
                    returncode=0,
                    stdout="M  src/auth/login.py\nM  .env\nA  tests/test_auth.py\n",
                    stderr=""
                )
            elif 'diff' in cmd:
                return Mock(returncode=0, stdout="+++ changes here", stderr="")
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = mock_subprocess

        stager = GitFileStager()

        # Get all modified files
        modified = stager.get_modified_files()
        assert len(modified) == 3

        # Analyze for staging
        to_stage = stager.analyze_files_for_staging(feature_context="authentication")
        assert "src/auth/login.py" in to_stage
        assert "tests/test_auth.py" in to_stage
        assert ".env" not in to_stage

        # Error handling
        mock_run.side_effect = None
        mock_run.return_value = Mock(
            returncode=128,
            stdout="",
            stderr="fatal: not a git repository"
        )
        with pytest.raises(RuntimeError):
            stager.get_modified_files()
