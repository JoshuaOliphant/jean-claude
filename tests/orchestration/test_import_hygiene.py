# ABOUTME: Consolidated import hygiene tests for orchestration modules
# ABOUTME: Verifies public API usage and no private imports in orchestration code

"""Consolidated import hygiene tests for orchestration modules.

Replaces test_auto_continue_imports.py, test_two_agent_imports.py, and
test_no_private_imports.py with a single parametrized test suite.
"""

import ast
from pathlib import Path

import pytest


ORCHESTRATION_DIR = Path(__file__).parent.parent.parent / "src" / "jean_claude" / "orchestration"


@pytest.mark.parametrize("module_name", ["auto_continue", "two_agent"])
def test_module_uses_public_execute_prompt_import(module_name):
    """Verify orchestration modules import execute_prompt_async from sdk_executor, not agent."""
    source_path = ORCHESTRATION_DIR / f"{module_name}.py"
    tree = ast.parse(source_path.read_text())

    found_public = False
    found_private = False

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "jean_claude.core.agent":
                if any(a.name == "execute_prompt_async" for a in node.names):
                    found_private = True
            if node.module == "jean_claude.core.sdk_executor":
                if any(a.name == "execute_prompt_async" for a in node.names):
                    found_public = True

    assert found_public, f"{module_name}.py should import execute_prompt_async from sdk_executor"
    assert not found_private, f"{module_name}.py should NOT import execute_prompt_async from agent"


def test_no_private_imports_in_orchestration():
    """Verify no orchestration module imports private functions (underscore-prefixed)."""
    violations = []

    for py_file in ORCHESTRATION_DIR.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        try:
            tree = ast.parse(py_file.read_text(), filename=str(py_file))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.names:
                for alias in node.names:
                    if alias.name.startswith("_"):
                        violations.append(
                            f"{py_file.name}:{node.lineno}: from {node.module} import {alias.name}"
                        )

    assert not violations, f"Private imports detected:\n" + "\n".join(violations)
