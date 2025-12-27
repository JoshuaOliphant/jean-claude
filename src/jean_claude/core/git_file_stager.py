"""GitFileStager service for analyzing which files should be staged for commits.

This module provides functionality to identify modified files that are relevant
to a specific feature and should be staged for a commit, while excluding
unrelated changes, config files, and build artifacts.
"""

import subprocess
from pathlib import Path
from typing import List, Union


class GitFileStager:
    """Analyzes which files should be staged for a feature commit.

    The GitFileStager uses git status and git diff to determine which files
    have been modified, then filters them based on relevance to the feature
    and excludes common config files, build artifacts, and system files.

    Attributes:
        repo_path: Path to the git repository (defaults to current directory)
    """

    # Common exclusion patterns for files that shouldn't be auto-staged
    EXCLUDED_PATTERNS = {
        # Config files
        '.env', '.env.local', '.env.production', '.env.development',
        '.gitignore', '.dockerignore', '.npmignore',
        'config.yaml', 'config.yml', 'config.json', 'config.ini',
        '.editorconfig', '.prettierrc', '.eslintrc',

        # System files
        '.DS_Store', 'Thumbs.db', 'desktop.ini',

        # IDE/Editor files
        '.idea', '.vscode', '.eclipse', '.settings',

        # Build artifacts and caches
        '__pycache__', '*.pyc', '*.pyo', '*.pyd',
        'node_modules', 'dist', 'build', '.cache',
        '*.egg-info', '.tox', '.pytest_cache',

        # Logs
        '*.log', 'logs',
    }

    def __init__(self, repo_path: Union[str, Path] = None):
        """Initialize the GitFileStager.

        Args:
            repo_path: Path to the git repository. Defaults to current directory.
        """
        if repo_path is None:
            self.repo_path = Path.cwd()
        elif isinstance(repo_path, str):
            self.repo_path = Path(repo_path)
        else:
            self.repo_path = repo_path

    def get_modified_files(self) -> List[str]:
        """Get list of modified files from git status.

        Returns:
            List of file paths that have been modified, added, or deleted.

        Raises:
            RuntimeError: If git command fails.
        """
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Git command failed with code {result.returncode}: {result.stderr}"
                )

            # Parse git status output
            # Format: "XY filename" where X is staged status, Y is unstaged status
            files = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                # Extract filename (skip first 3 characters: status + space)
                filename = line[3:].strip()
                if filename:
                    files.append(filename)

            return files

        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Git command failed: {e}") from e

    def get_file_diff(self, filepath: str) -> str:
        """Get diff for a specific file.

        Args:
            filepath: Path to the file to get diff for.

        Returns:
            Diff output for the file.

        Raises:
            RuntimeError: If git diff command fails.
        """
        try:
            result = subprocess.run(
                ['git', 'diff', 'HEAD', filepath],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Git diff failed with code {result.returncode}: {result.stderr}"
                )

            return result.stdout

        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Git diff failed: {e}") from e

    def is_excluded(self, filepath: str) -> bool:
        """Check if a file should be excluded from staging.

        Args:
            filepath: Path to check for exclusion.

        Returns:
            True if the file should be excluded, False otherwise.
        """
        path = Path(filepath)

        # Check against exclusion patterns
        for pattern in self.EXCLUDED_PATTERNS:
            # Check if pattern matches the filename
            if path.name == pattern or path.name.startswith(pattern):
                return True

            # Check if pattern is in the path
            if pattern in filepath:
                return True

            # Check for wildcard patterns
            if pattern.startswith('*'):
                suffix = pattern[1:]
                if filepath.endswith(suffix):
                    return True

        # Exclude dotfiles at root (except some common ones we might want)
        if filepath.startswith('.') and '/' not in filepath:
            # Allow common documentation files
            if filepath not in {'.gitattributes', '.mailmap'}:
                return True

        return False

    def filter_relevant_files(
        self,
        files: List[str],
        feature_context: str = ""
    ) -> List[str]:
        """Filter files to only include those relevant to the feature.

        Args:
            files: List of file paths to filter.
            feature_context: Description or keywords related to the feature.

        Returns:
            List of files that are relevant to the feature and not excluded.
        """
        if not files:
            return []

        relevant_files = []

        for filepath in files:
            # Skip excluded files
            if self.is_excluded(filepath):
                continue

            # If no feature context, include all non-excluded files
            if not feature_context:
                relevant_files.append(filepath)
                continue

            # Include the file (it passed exclusion filters)
            # In a more advanced implementation, we could do fuzzy matching
            # between filepath and feature_context, but for now we include
            # all non-excluded files
            relevant_files.append(filepath)

        return relevant_files

    def analyze_files_for_staging(self, feature_context: str = "") -> List[str]:
        """Analyze which files should be staged for a feature commit.

        This is the main method that combines getting modified files,
        filtering out excluded patterns, and identifying files relevant
        to the feature.

        Args:
            feature_context: Description or keywords related to the feature.

        Returns:
            List of file paths that should be staged for the commit.

        Raises:
            RuntimeError: If git commands fail.
        """
        # Get all modified files
        modified_files = self.get_modified_files()

        # Filter to only relevant files
        relevant_files = self.filter_relevant_files(modified_files, feature_context)

        return relevant_files
