"""Tests for two_agent.py import statements.

This test verifies that two_agent.py uses the correct public import
for execute_prompt_async instead of the private execute_prompt_async.
"""

import ast
from pathlib import Path


def test_two_agent_uses_public_import():
    """Verify two_agent.py imports execute_prompt_async from sdk_executor module."""
    # Read the two_agent.py source file
    two_agent_path = Path(__file__).parent.parent.parent / "src" / "jean_claude" / "orchestration" / "two_agent.py"

    with open(two_agent_path, "r") as f:
        source = f.read()

    # Parse the AST
    tree = ast.parse(source)

    # Track what we find
    found_public_import = False
    found_private_import = False

    # Check imports
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            # Check for the old private import
            if node.module == "jean_claude.core.agent":
                for alias in node.names:
                    if alias.name == "execute_prompt_async":
                        found_private_import = True

            # Check for the new public import
            if node.module == "jean_claude.core.sdk_executor":
                for alias in node.names:
                    if alias.name == "execute_prompt_async":
                        found_public_import = True

    # Assert that we use the public import and not the private one
    assert found_public_import, (
        "two_agent.py should import execute_prompt_async from jean_claude.core.sdk_executor"
    )
    assert not found_private_import, (
        "two_agent.py should NOT import execute_prompt_async from jean_claude.core.agent"
    )


def test_two_agent_imports_from_correct_module():
    """Verify imports are from the correct modules."""
    # Read the two_agent.py source file
    two_agent_path = Path(__file__).parent.parent.parent / "src" / "jean_claude" / "orchestration" / "two_agent.py"

    with open(two_agent_path, "r") as f:
        source = f.read()

    # Parse the AST
    tree = ast.parse(source)

    # Expected imports from jean_claude.core.agent (should still have these)
    expected_agent_imports = {"PromptRequest", "ExecutionResult"}
    found_agent_imports = set()

    # Check imports from agent module
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "jean_claude.core.agent":
                for alias in node.names:
                    found_agent_imports.add(alias.name)

    # Verify we still import PromptRequest and ExecutionResult from agent
    assert expected_agent_imports.issubset(found_agent_imports), (
        f"Missing expected imports from jean_claude.core.agent. "
        f"Expected {expected_agent_imports}, found {found_agent_imports}"
    )
