# ABOUTME: Tests for workflow_utils module structure and imports for WorkflowState
# ABOUTME: Ensures proper module organization and correct imports are in place

"""Tests for jean_claude.core.workflow_utils module structure and imports."""

import ast
import inspect
from pathlib import Path

import pytest

from jean_claude.core import workflow_utils
from jean_claude.core.state import WorkflowState


def test_workflow_utils_module_exists():
    """Test that workflow_utils module exists and can be imported."""
    assert workflow_utils is not None
    assert hasattr(workflow_utils, '__name__')
    assert workflow_utils.__name__ == 'jean_claude.core.workflow_utils'


def test_workflow_utils_has_proper_docstring():
    """Test that workflow_utils module has a proper module docstring."""
    assert workflow_utils.__doc__ is not None
    assert len(workflow_utils.__doc__.strip()) > 0
    assert "workflow" in workflow_utils.__doc__.lower()
    assert "utility" in workflow_utils.__doc__.lower()


def test_workflow_utils_imports_workflow_state():
    """Test that workflow_utils properly imports WorkflowState."""
    # Check that WorkflowState is accessible from the module
    source_file = Path(workflow_utils.__file__)
    source_content = source_file.read_text()

    # Parse the AST to check imports
    tree = ast.parse(source_content)

    # Look for import statements
    import_statements = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]

    # Check that WorkflowState is imported
    workflow_state_imported = False
    for import_node in import_statements:
        if isinstance(import_node, ast.ImportFrom):
            if (import_node.module == 'jean_claude.core.state' and
                any(alias.name == 'WorkflowState' for alias in import_node.names)):
                workflow_state_imported = True
                break

    assert workflow_state_imported, "WorkflowState should be imported from jean_claude.core.state"


def test_workflow_utils_has_required_functions():
    """Test that workflow_utils has all required functions."""
    # Check that find_most_recent_workflow exists
    assert hasattr(workflow_utils, 'find_most_recent_workflow')
    assert callable(workflow_utils.find_most_recent_workflow)

    # Check function signature
    sig = inspect.signature(workflow_utils.find_most_recent_workflow)
    params = list(sig.parameters.keys())
    assert 'project_root' in params

    # Check return annotation
    assert sig.return_annotation is not None


def test_workflow_utils_imports_pathlib():
    """Test that workflow_utils imports necessary standard library modules."""
    source_file = Path(workflow_utils.__file__)
    source_content = source_file.read_text()

    # Check for pathlib import
    assert "from pathlib import Path" in source_content
    # Check for typing imports
    assert "from typing import" in source_content or "import typing" in source_content
    # Check for datetime imports
    assert "from datetime import" in source_content or "import datetime" in source_content


def test_workflow_utils_function_has_proper_docstring():
    """Test that find_most_recent_workflow has proper documentation."""
    func = workflow_utils.find_most_recent_workflow
    assert func.__doc__ is not None
    assert len(func.__doc__.strip()) > 0

    # Check that docstring contains key information
    docstring = func.__doc__.lower()
    assert "workflow" in docstring
    assert "recent" in docstring
    assert "args:" in docstring
    assert "returns:" in docstring


def test_workflow_utils_file_structure():
    """Test that the workflow_utils.py file has the expected structure."""
    source_file = Path(workflow_utils.__file__)
    assert source_file.exists()
    assert source_file.name == "workflow_utils.py"
    assert source_file.parent.name == "core"

    source_content = source_file.read_text()

    # Should have ABOUTME comments
    assert "# ABOUTME:" in source_content

    # Should have proper module docstring
    lines = source_content.split('\n')
    docstring_start = None
    for i, line in enumerate(lines):
        if '"""' in line:
            docstring_start = i
            break

    assert docstring_start is not None, "Module should have a docstring"


def test_workflow_utils_can_use_workflow_state():
    """Test that workflow_utils can actually use WorkflowState class."""
    # This is an integration test to ensure the import actually works
    from jean_claude.core.workflow_utils import find_most_recent_workflow
    from jean_claude.core.state import WorkflowState

    # Check that WorkflowState is available in the workflow_utils module context
    # by checking the source to see if it's used properly
    source_file = Path(workflow_utils.__file__)
    source_content = source_file.read_text()

    # Should reference WorkflowState in the implementation
    assert "WorkflowState" in source_content
    # Should use it for loading state files
    assert "WorkflowState.load_from_file" in source_content


def test_workflow_utils_has_proper_typing():
    """Test that workflow_utils uses proper type annotations."""
    func = workflow_utils.find_most_recent_workflow
    sig = inspect.signature(func)

    # Check parameter types
    project_root_param = sig.parameters['project_root']
    assert project_root_param.annotation is not None

    # Check return type
    assert sig.return_annotation is not None

    # Check that Optional is used (since function can return None)
    source_file = Path(workflow_utils.__file__)
    source_content = source_file.read_text()
    assert "Optional" in source_content