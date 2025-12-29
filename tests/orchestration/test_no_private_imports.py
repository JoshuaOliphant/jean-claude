"""Test to ensure no private imports exist in orchestration modules."""

import ast
import os
from pathlib import Path


def test_no_private_imports():
    """Verify that no private function imports remain in orchestration modules.

    This test scans all Python files in src/jean_claude/orchestration/ and
    ensures that no imports of private functions (starting with underscore)
    exist. This enforces the use of public APIs only.
    """
    # Get the orchestration directory path
    project_root = Path(__file__).parent.parent.parent
    orchestration_dir = project_root / "src" / "jean_claude" / "orchestration"

    assert orchestration_dir.exists(), f"Orchestration directory not found: {orchestration_dir}"

    # Find all Python files in the orchestration directory
    python_files = list(orchestration_dir.glob("*.py"))
    assert len(python_files) > 0, "No Python files found in orchestration directory"

    # Track any violations found
    violations = []

    for py_file in python_files:
        # Skip __init__.py as it typically just exports
        if py_file.name == "__init__.py":
            continue

        with open(py_file, "r") as f:
            try:
                tree = ast.parse(f.read(), filename=str(py_file))
            except SyntaxError as e:
                violations.append(f"{py_file.name}: Syntax error - {e}")
                continue

        # Check all import statements
        for node in ast.walk(tree):
            # Check "from module import _private_func" style imports
            if isinstance(node, ast.ImportFrom):
                if node.names:
                    for alias in node.names:
                        if alias.name.startswith("_"):
                            violations.append(
                                f"{py_file.name}:{node.lineno}: "
                                f"Private import detected: from {node.module} import {alias.name}"
                            )

            # Check "import _private_module" style imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    # Check if the last component of the import path starts with _
                    parts = alias.name.split(".")
                    if any(part.startswith("_") for part in parts):
                        violations.append(
                            f"{py_file.name}:{node.lineno}: "
                            f"Private module import detected: import {alias.name}"
                        )

    # Assert no violations were found
    if violations:
        violation_msg = "\n".join(violations)
        assert False, f"Private imports detected in orchestration modules:\n{violation_msg}"


def test_orchestration_files_exist():
    """Verify that the expected orchestration files exist."""
    project_root = Path(__file__).parent.parent.parent
    orchestration_dir = project_root / "src" / "jean_claude" / "orchestration"

    expected_files = [
        "auto_continue.py",
        "two_agent.py",
    ]

    for expected_file in expected_files:
        file_path = orchestration_dir / expected_file
        assert file_path.exists(), f"Expected file not found: {expected_file}"


def test_public_imports_work():
    """Verify that the public imports are available and working."""
    # This test ensures the refactored code uses proper public imports
    try:
        from jean_claude.core.sdk_executor import execute_prompt_async
        assert callable(execute_prompt_async), "execute_prompt_async should be callable"
    except ImportError as e:
        assert False, f"Failed to import public function: {e}"
