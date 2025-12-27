# ABOUTME: Tests for CommitBodyGenerator
# ABOUTME: Consolidated tests for git diff parsing and commit body generation

"""Tests for CommitBodyGenerator.

Consolidated from 29 separate tests to focused tests covering
essential behaviors without per-category redundancy.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from jean_claude.core.commit_body_generator import CommitBodyGenerator


class TestCommitBodyGeneratorInit:
    """Test CommitBodyGenerator initialization - consolidated from 3 tests to 1."""

    def test_init_with_various_path_options(self, tmp_path):
        """Test initialization with defaults, custom path, and string path."""
        # Default path
        generator1 = CommitBodyGenerator()
        assert generator1.repo_path == Path.cwd()

        # Custom path
        generator2 = CommitBodyGenerator(repo_path=tmp_path)
        assert generator2.repo_path == tmp_path

        # String converted to Path
        generator3 = CommitBodyGenerator(repo_path="/tmp/test")
        assert isinstance(generator3.repo_path, Path)
        assert generator3.repo_path == Path("/tmp/test")


class TestCommitBodyGeneratorGetDiff:
    """Test getting git diff output - consolidated from 3 tests to 1."""

    @patch('subprocess.run')
    def test_get_diff_success_and_staged_flag(self, mock_run):
        """Test getting diff successfully and with --cached flag."""
        expected_diff = """diff --git a/src/main.py b/src/main.py
new file mode 100644
--- /dev/null
+++ b/src/main.py
+def hello():
+    print("Hello")
"""
        mock_run.return_value = Mock(returncode=0, stdout=expected_diff, stderr="")

        generator = CommitBodyGenerator()

        # Basic diff
        diff = generator.get_diff()
        assert diff == expected_diff
        mock_run.assert_called()

        # Staged only uses --cached
        generator.get_diff(staged_only=True)
        call_args = mock_run.call_args[0][0]
        assert '--cached' in call_args

    @patch('subprocess.run')
    def test_get_diff_handles_git_error(self, mock_run):
        """Test handling git diff errors."""
        mock_run.return_value = Mock(returncode=128, stdout="", stderr="fatal: not a git repository")

        generator = CommitBodyGenerator()
        with pytest.raises(RuntimeError, match="Git diff failed"):
            generator.get_diff()


class TestCommitBodyGeneratorParseDiff:
    """Test parsing git diff output - consolidated from 10 tests to 3."""

    def test_parse_identifies_file_changes(self):
        """Test identifying new, modified, and deleted files."""
        diff = """diff --git a/src/new.py b/src/new.py
new file mode 100644
--- /dev/null
+++ b/src/new.py
+def new_function():
+    pass
diff --git a/src/modified.py b/src/modified.py
index 1234567..abcdefg 100644
--- a/src/modified.py
+++ b/src/modified.py
@@ -10,5 +10,8 @@
+def added_function():
+    pass
diff --git a/src/deleted.py b/src/deleted.py
deleted file mode 100644
--- a/src/deleted.py
+++ /dev/null
"""
        generator = CommitBodyGenerator()
        parsed = generator.parse_diff(diff)

        assert "src/new.py" in parsed["new_files"]
        assert "src/modified.py" in parsed["modified_files"]
        assert "src/deleted.py" in parsed["deleted_files"]

    def test_parse_identifies_code_elements(self):
        """Test identifying functions, classes, dependencies, and imports."""
        diff = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,15 @@
 from typing import Any
+from pathlib import Path
+import subprocess
+
+class NewModel:
+    def __init__(self):
+        pass
+
+def new_function():
+    return True
+
+async def async_function():
+    pass
diff --git a/requirements.txt b/requirements.txt
--- a/requirements.txt
+++ b/requirements.txt
@@ -1 +1,3 @@
 requests==2.28.0
+fastapi==0.95.0
+uvicorn==0.21.0
"""
        generator = CommitBodyGenerator()
        parsed = generator.parse_diff(diff)

        # Functions detected
        assert len(parsed["added_functions"]) >= 2

        # Classes detected
        assert len(parsed["added_classes"]) >= 1

        # Dependencies detected
        assert "fastapi==0.95.0" in parsed["added_dependencies"]
        assert "uvicorn==0.21.0" in parsed["added_dependencies"]

        # Imports detected
        assert len(parsed["added_imports"]) >= 1

    def test_parse_handles_empty_and_complex_diffs(self):
        """Test empty diffs and complex multi-file diffs."""
        generator = CommitBodyGenerator()

        # Empty diff
        parsed = generator.parse_diff("")
        assert parsed["new_files"] == []
        assert parsed["modified_files"] == []
        assert parsed["deleted_files"] == []

        # Complex multi-file diff
        complex_diff = """diff --git a/auth.py b/auth.py
new file mode 100644
--- /dev/null
+++ b/auth.py
+def authenticate(): pass
diff --git a/main.py b/main.py
index 222..333 100644
--- a/main.py
+++ b/main.py
+import sys
diff --git a/old.py b/old.py
deleted file mode 100644
"""
        parsed = generator.parse_diff(complex_diff)
        assert len(parsed["new_files"]) >= 1
        assert len(parsed["modified_files"]) >= 1
        assert len(parsed["deleted_files"]) >= 1


class TestCommitBodyGeneratorFormatBullets:
    """Test formatting as commit body bullets - consolidated from 7 tests to 1."""

    def test_format_bullets_for_all_change_types(self):
        """Test formatting bullets for all types of changes."""
        generator = CommitBodyGenerator()

        # New files
        parsed_new = {
            "new_files": ["src/auth.py", "tests/test_auth.py"],
            "modified_files": [], "deleted_files": [],
            "added_functions": [], "added_classes": [],
            "added_dependencies": [], "added_imports": []
        }
        bullets = generator.format_bullets(parsed_new)
        assert isinstance(bullets, list)
        assert all(isinstance(b, str) for b in bullets)

        # Modified files with functions
        parsed_mod = {
            "new_files": [],
            "modified_files": ["src/main.py"],
            "deleted_files": [],
            "added_functions": ["process_data", "validate_input"],
            "added_classes": ["UserModel"],
            "added_dependencies": ["fastapi==0.95.0"],
            "added_imports": ["pathlib"]
        }
        bullets = generator.format_bullets(parsed_mod)
        bullet_text = "\n".join(bullets)
        assert len(bullets) > 0

        # Deleted files
        parsed_del = {
            "new_files": [],
            "modified_files": [],
            "deleted_files": ["src/old.py"],
            "added_functions": [], "added_classes": [],
            "added_dependencies": [], "added_imports": []
        }
        bullets = generator.format_bullets(parsed_del)
        assert isinstance(bullets, list)

        # Empty - should not crash
        parsed_empty = {
            "new_files": [], "modified_files": [], "deleted_files": [],
            "added_functions": [], "added_classes": [],
            "added_dependencies": [], "added_imports": []
        }
        bullets = generator.format_bullets(parsed_empty)
        assert isinstance(bullets, list)


class TestCommitBodyGeneratorGenerate:
    """Test the main generate method - consolidated from 4 tests to 2."""

    @patch('subprocess.run')
    def test_generate_returns_bullets_and_uses_staged_flag(self, mock_run):
        """Test generate returns list and respects staged_only flag."""
        diff = """diff --git a/src/feature.py b/src/feature.py
new file mode 100644
--- /dev/null
+++ b/src/feature.py
+def new_feature():
+    pass
"""
        mock_run.return_value = Mock(returncode=0, stdout=diff, stderr="")

        generator = CommitBodyGenerator()

        # Basic generate
        bullets = generator.generate()
        assert isinstance(bullets, list)
        for bullet in bullets:
            assert isinstance(bullet, str)

        # Staged only
        bullets = generator.generate(staged_only=True)
        call_args = mock_run.call_args[0][0]
        assert '--cached' in call_args

    @patch('subprocess.run')
    def test_generate_handles_errors_and_complex_diffs(self, mock_run):
        """Test error handling and complex diff generation."""
        # Error case
        mock_run.return_value = Mock(returncode=128, stdout="", stderr="fatal: error")
        generator = CommitBodyGenerator()
        with pytest.raises(RuntimeError):
            generator.generate()

        # Complex diff
        complex_diff = """diff --git a/src/auth/login.py b/src/auth/login.py
new file mode 100644
--- /dev/null
+++ b/src/auth/login.py
+from typing import Optional
+import jwt
+class LoginHandler:
+    def authenticate(self): return True
diff --git a/requirements.txt b/requirements.txt
--- a/requirements.txt
+++ b/requirements.txt
+pyjwt==2.6.0
diff --git a/tests/test_login.py b/tests/test_login.py
new file mode 100644
--- /dev/null
+++ b/tests/test_login.py
+def test_authenticate(): assert True
"""
        mock_run.return_value = Mock(returncode=0, stdout=complex_diff, stderr="")
        bullets = generator.generate()
        assert len(bullets) > 0


class TestCommitBodyGeneratorIntegration:
    """Integration tests - consolidated from 2 tests to 1."""

    @patch('subprocess.run')
    def test_full_workflow_new_feature_and_refactoring(self, mock_run):
        """Test complete workflow for new features and refactoring."""
        generator = CommitBodyGenerator()

        # New feature workflow
        new_feature_diff = """diff --git a/src/api/endpoints.py b/src/api/endpoints.py
new file mode 100644
--- /dev/null
+++ b/src/api/endpoints.py
+from fastapi import APIRouter
+router = APIRouter()
+@router.get("/users")
+async def get_users(): return []
diff --git a/requirements.txt b/requirements.txt
--- a/requirements.txt
+++ b/requirements.txt
+fastapi==0.95.0
"""
        mock_run.return_value = Mock(returncode=0, stdout=new_feature_diff, stderr="")
        bullets = generator.generate()
        assert len(bullets) > 0

        # Refactoring workflow
        refactor_diff = """diff --git a/src/utils/helpers.py b/src/utils/helpers.py
index 111..222 100644
--- a/src/utils/helpers.py
+++ b/src/utils/helpers.py
-def deprecated_function(): pass
+def improved_function(): return True
+class HelperClass:
+    def process(self): pass
"""
        mock_run.return_value = Mock(returncode=0, stdout=refactor_diff, stderr="")
        bullets = generator.generate()
        assert len(bullets) > 0
