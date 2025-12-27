"""CommitBodyGenerator for analyzing feature implementation and generating commit body bullets.

This module provides functionality to parse git diff output, identify key changes
(new files, modified functions, added dependencies), and format them as meaningful
bullet points describing what was done in the commit.
"""

import subprocess
import re
from pathlib import Path
from typing import Dict, List, Union, Optional


class CommitBodyGenerator:
    """Analyzes feature implementation to generate meaningful commit body bullets.

    The CommitBodyGenerator parses git diff output to identify key changes such as:
    - New files created
    - Modified files
    - Deleted files
    - New functions and classes
    - Added dependencies
    - New imports

    It then formats these changes as bullet points suitable for a commit message body.

    Attributes:
        repo_path: Path to the git repository (defaults to current directory)
    """

    def __init__(self, repo_path: Union[str, Path, None] = None):
        """Initialize the CommitBodyGenerator.

        Args:
            repo_path: Path to the git repository. Defaults to current directory.
        """
        if repo_path is None:
            self.repo_path = Path.cwd()
        elif isinstance(repo_path, str):
            self.repo_path = Path(repo_path)
        else:
            self.repo_path = repo_path

    def get_diff(self, staged_only: bool = False) -> str:
        """Get git diff output.

        Args:
            staged_only: If True, only get diff of staged files (--cached).
                        If False, get diff of all changes.

        Returns:
            Git diff output as a string.

        Raises:
            RuntimeError: If git diff command fails.
        """
        try:
            cmd = ['git', 'diff']
            if staged_only:
                cmd.append('--cached')

            result = subprocess.run(
                cmd,
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

    def parse_diff(self, diff: str) -> Dict[str, List[str]]:
        """Parse git diff output to identify key changes.

        Args:
            diff: Git diff output to parse.

        Returns:
            Dictionary containing:
                - new_files: List of newly created files
                - modified_files: List of modified files
                - deleted_files: List of deleted files
                - added_functions: List of new function names
                - added_classes: List of new class names
                - added_dependencies: List of new dependencies
                - added_imports: List of new imports

        Example:
            >>> generator = CommitBodyGenerator()
            >>> parsed = generator.parse_diff(diff_output)
            >>> print(parsed["new_files"])
            ['src/auth.py', 'tests/test_auth.py']
        """
        parsed = {
            "new_files": [],
            "modified_files": [],
            "deleted_files": [],
            "added_functions": [],
            "added_classes": [],
            "added_dependencies": [],
            "added_imports": []
        }

        if not diff:
            return parsed

        # Split diff into individual file diffs
        file_diffs = re.split(r'^diff --git ', diff, flags=re.MULTILINE)

        for file_diff in file_diffs:
            if not file_diff.strip():
                continue

            # Extract filename from the first line
            # Format: "a/path/to/file b/path/to/file"
            filename_match = re.match(r'a/([\w/._-]+)\s+b/([\w/._-]+)', file_diff)
            if not filename_match:
                continue

            filename = filename_match.group(1)

            # Check if it's a new file
            if 'new file mode' in file_diff:
                parsed["new_files"].append(filename)
            # Check if it's a deleted file
            elif 'deleted file mode' in file_diff:
                parsed["deleted_files"].append(filename)
            # Otherwise, it's a modified file
            elif 'index' in file_diff:
                parsed["modified_files"].append(filename)

            # Look for added lines (starting with +)
            added_lines = re.findall(r'^\+(.*)$', file_diff, re.MULTILINE)

            for line in added_lines:
                # Skip diff markers
                if line.startswith('++'):
                    continue

                # Detect new functions
                # Patterns: "def function_name(" or "async def function_name("
                func_match = re.search(r'(?:async\s+)?def\s+([\w_]+)\s*\(', line)
                if func_match:
                    func_name = func_match.group(1)
                    # Avoid duplicates and skip magic methods
                    if func_name not in parsed["added_functions"] and not func_name.startswith('__'):
                        parsed["added_functions"].append(func_name)

                # Detect new classes
                # Pattern: "class ClassName" or "class ClassName(BaseClass)"
                class_match = re.search(r'class\s+([\w_]+)(?:\s*\(|:)', line)
                if class_match:
                    class_name = class_match.group(1)
                    if class_name not in parsed["added_classes"]:
                        parsed["added_classes"].append(class_name)

                # Detect new dependencies (in requirements.txt or similar)
                if filename in ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile']:
                    # Look for package names with versions
                    dep_match = re.search(r'([\w\-_]+(?:==|>=|<=|~=|>|<)[\d.]+)', line)
                    if dep_match:
                        dep = dep_match.group(1)
                        if dep not in parsed["added_dependencies"]:
                            parsed["added_dependencies"].append(dep)

                # Detect new imports
                # Patterns: "import module" or "from module import ..."
                import_match = re.search(r'(?:from\s+([\w._]+)\s+import|import\s+([\w._]+))', line)
                if import_match:
                    module = import_match.group(1) or import_match.group(2)
                    # Extract base module name
                    base_module = module.split('.')[0]
                    if base_module not in parsed["added_imports"] and base_module not in ['typing', '__future__']:
                        parsed["added_imports"].append(base_module)

        return parsed

    def format_bullets(self, parsed: Dict[str, List[str]]) -> List[str]:
        """Format parsed diff data as commit body bullet points.

        Args:
            parsed: Dictionary containing parsed diff information.

        Returns:
            List of formatted bullet point strings.

        Example:
            >>> generator = CommitBodyGenerator()
            >>> bullets = generator.format_bullets(parsed_data)
            >>> for bullet in bullets:
            ...     print(f"- {bullet}")
        """
        bullets = []

        # Format new files
        if parsed["new_files"]:
            if len(parsed["new_files"]) == 1:
                bullets.append(f"Add new file: {parsed['new_files'][0]}")
            elif len(parsed["new_files"]) <= 3:
                bullets.append(f"Add new files: {', '.join(parsed['new_files'])}")
            else:
                bullets.append(f"Add {len(parsed['new_files'])} new files")
                # Optionally list first few
                sample = parsed['new_files'][:3]
                bullets.append(f"  Including: {', '.join(sample)}")

        # Format new classes
        if parsed["added_classes"]:
            if len(parsed["added_classes"]) == 1:
                bullets.append(f"Implement {parsed['added_classes'][0]} class")
            elif len(parsed["added_classes"]) <= 3:
                bullets.append(f"Implement classes: {', '.join(parsed['added_classes'])}")
            else:
                bullets.append(f"Implement {len(parsed['added_classes'])} new classes")

        # Format new functions
        if parsed["added_functions"]:
            # Filter out test functions for cleaner output
            non_test_functions = [f for f in parsed["added_functions"] if not f.startswith('test_')]

            if non_test_functions:
                if len(non_test_functions) == 1:
                    bullets.append(f"Add {non_test_functions[0]} function")
                elif len(non_test_functions) <= 3:
                    bullets.append(f"Add functions: {', '.join(non_test_functions)}")
                else:
                    bullets.append(f"Add {len(non_test_functions)} new functions")

            # Mention test functions separately if significant
            test_functions = [f for f in parsed["added_functions"] if f.startswith('test_')]
            if len(test_functions) >= 3:
                bullets.append(f"Add {len(test_functions)} test functions")

        # Format new dependencies
        if parsed["added_dependencies"]:
            if len(parsed["added_dependencies"]) == 1:
                bullets.append(f"Add dependency: {parsed['added_dependencies'][0]}")
            elif len(parsed["added_dependencies"]) <= 3:
                bullets.append(f"Add dependencies: {', '.join(parsed['added_dependencies'])}")
            else:
                bullets.append(f"Add {len(parsed['added_dependencies'])} new dependencies")

        # Format modified files (only if no new files/classes/functions mentioned)
        if parsed["modified_files"] and not (parsed["new_files"] or parsed["added_classes"] or parsed["added_functions"]):
            if len(parsed["modified_files"]) == 1:
                bullets.append(f"Update {parsed['modified_files'][0]}")
            elif len(parsed["modified_files"]) <= 3:
                bullets.append(f"Update files: {', '.join(parsed['modified_files'])}")
            else:
                bullets.append(f"Update {len(parsed['modified_files'])} files")

        # Format deleted files
        if parsed["deleted_files"]:
            if len(parsed["deleted_files"]) == 1:
                bullets.append(f"Remove {parsed['deleted_files'][0]}")
            elif len(parsed["deleted_files"]) <= 3:
                bullets.append(f"Remove files: {', '.join(parsed['deleted_files'])}")
            else:
                bullets.append(f"Remove {len(parsed['deleted_files'])} files")

        # Format imports (only mention if significant and no other changes)
        if parsed["added_imports"] and len(bullets) == 0:
            significant_imports = [imp for imp in parsed["added_imports"]
                                 if imp not in ['os', 'sys', 're', 'json']]
            if significant_imports:
                if len(significant_imports) <= 3:
                    bullets.append(f"Add imports: {', '.join(significant_imports)}")
                else:
                    bullets.append(f"Add {len(significant_imports)} new imports")

        return bullets

    def generate(self, staged_only: bool = False) -> List[str]:
        """Generate commit body bullet points from git diff.

        This is the main method that combines getting the diff, parsing it,
        and formatting it into bullet points.

        Args:
            staged_only: If True, only analyze staged changes.
                        If False, analyze all changes.

        Returns:
            List of formatted bullet point strings suitable for commit body.

        Raises:
            RuntimeError: If git diff command fails.

        Example:
            >>> generator = CommitBodyGenerator()
            >>> bullets = generator.generate(staged_only=True)
            >>> for bullet in bullets:
            ...     print(f"- {bullet}")
        """
        # Get the diff
        diff = self.get_diff(staged_only=staged_only)

        # Parse the diff
        parsed = self.parse_diff(diff)

        # Format as bullets
        bullets = self.format_bullets(parsed)

        return bullets
