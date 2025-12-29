"""Tests for auto_continue.py function calls.

This test verifies that auto_continue.py calls the correct public function
execute_prompt_async instead of the private execute_prompt_async.
"""

import ast
from pathlib import Path


def test_auto_continue_calls_execute_prompt_async():
    """Verify auto_continue.py calls execute_prompt_async, not execute_prompt_async."""
    # Read the auto_continue.py source file
    auto_continue_path = Path(__file__).parent.parent.parent / "src" / "jean_claude" / "orchestration" / "auto_continue.py"

    with open(auto_continue_path, "r") as f:
        source = f.read()

    # Parse the AST
    tree = ast.parse(source)

    # Track function calls
    found_public_call = False
    found_private_call = False
    private_call_locations = []

    # Check all function calls in the module
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check if it's a Name node (direct function call)
            if isinstance(node.func, ast.Name):
                if node.func.id == "execute_prompt_async":
                    found_public_call = True
                elif node.func.id == "execute_prompt_async":
                    found_private_call = True
                    private_call_locations.append(f"line {node.lineno}")

            # Check if it's an Attribute node (module.function call)
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr == "execute_prompt_async":
                    found_public_call = True
                elif node.func.attr == "execute_prompt_async":
                    found_private_call = True
                    private_call_locations.append(f"line {node.lineno}")

    # Check for await statements with function calls
    for node in ast.walk(tree):
        if isinstance(node, ast.Await):
            if isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    if node.value.func.id == "execute_prompt_async":
                        found_public_call = True
                    elif node.value.func.id == "execute_prompt_async":
                        found_private_call = True
                        private_call_locations.append(f"line {node.lineno}")

    # Assert that we call the public function and not the private one
    assert not found_private_call, (
        f"auto_continue.py should NOT call execute_prompt_async. "
        f"Found calls at: {', '.join(private_call_locations)}"
    )

    assert found_public_call, (
        "auto_continue.py should call execute_prompt_async instead of execute_prompt_async"
    )


def test_function_signatures_are_compatible():
    """Verify that execute_prompt_async has the same signature as execute_prompt_async.

    This ensures that replacing the function call won't break functionality.
    """
    # Read sdk_executor.py to check execute_prompt_async signature
    sdk_executor_path = Path(__file__).parent.parent.parent / "src" / "jean_claude" / "core" / "sdk_executor.py"

    with open(sdk_executor_path, "r") as f:
        source = f.read()

    tree = ast.parse(source)

    # Find the execute_prompt_async function definition
    execute_prompt_async_func = None

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "execute_prompt_async":
            execute_prompt_async_func = node
            break

    assert execute_prompt_async_func is not None, "Could not find execute_prompt_async function"

    # Check parameters
    args = execute_prompt_async_func.args
    param_names = [arg.arg for arg in args.args]

    # The function should accept 'request' and 'max_retries' at minimum
    assert "request" in param_names, "execute_prompt_async should have 'request' parameter"
    assert "max_retries" in param_names, "execute_prompt_async should have 'max_retries' parameter"

    # Check defaults
    defaults_count = len(args.defaults)

    # max_retries should have a default value of 3
    if "max_retries" in param_names:
        max_retries_idx = param_names.index("max_retries")
        # Calculate the position in defaults (defaults align to the right)
        defaults_idx = max_retries_idx - (len(param_names) - defaults_count)
        if defaults_idx >= 0:
            default_value = args.defaults[defaults_idx]
            if isinstance(default_value, ast.Constant):
                assert default_value.value == 3, "max_retries default should be 3"


def test_auto_continue_function_call_arguments():
    """Verify that the call to execute_prompt_async uses correct arguments."""
    # Read the auto_continue.py source file
    auto_continue_path = Path(__file__).parent.parent.parent / "src" / "jean_claude" / "orchestration" / "auto_continue.py"

    with open(auto_continue_path, "r") as f:
        source = f.read()

    # Parse the AST
    tree = ast.parse(source)

    # Find the call to execute_prompt_async
    found_call = False
    call_has_request = False
    call_has_max_retries = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Await):
            if isinstance(node.value, ast.Call):
                func_name = None
                if isinstance(node.value.func, ast.Name):
                    func_name = node.value.func.id
                elif isinstance(node.value.func, ast.Attribute):
                    func_name = node.value.func.attr

                if func_name == "execute_prompt_async":
                    found_call = True

                    # Check positional arguments
                    if node.value.args:
                        call_has_request = True

                    # Check keyword arguments
                    for keyword in node.value.keywords:
                        if keyword.arg == "request":
                            call_has_request = True
                        elif keyword.arg == "max_retries":
                            call_has_max_retries = True

    if found_call:
        assert call_has_request, "Call to execute_prompt_async should include 'request' argument"
        assert call_has_max_retries, "Call to execute_prompt_async should include 'max_retries' argument"
