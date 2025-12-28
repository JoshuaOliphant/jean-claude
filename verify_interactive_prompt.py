#!/usr/bin/env python3
"""Verify interactive prompt handler implementation."""

import sys
from unittest.mock import patch, MagicMock
from io import StringIO

# Import the modules
try:
    from jean_claude.core.interactive_prompt_handler import InteractivePromptHandler, PromptAction
    from jean_claude.core.task_validator import ValidationResult
    print("✓ Imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 1: PromptAction enum
print("\nTest 1: PromptAction enum values")
try:
    assert PromptAction.PROCEED is not None
    assert PromptAction.EDIT is not None
    assert PromptAction.CANCEL is not None
    assert PromptAction.PROCEED != PromptAction.EDIT
    assert PromptAction.PROCEED != PromptAction.CANCEL
    assert PromptAction.EDIT != PromptAction.CANCEL
    print("✓ PromptAction enum works correctly")
except AssertionError as e:
    print(f"✗ PromptAction enum failed: {e}")
    sys.exit(1)

# Test 2: Handler initialization
print("\nTest 2: Handler initialization")
try:
    handler = InteractivePromptHandler()
    assert handler is not None
    assert handler.formatter is not None
    print("✓ Handler initializes correctly")
except Exception as e:
    print(f"✗ Handler initialization failed: {e}")
    sys.exit(1)

# Test 3: Input parsing
print("\nTest 3: Input parsing")
try:
    handler = InteractivePromptHandler()

    # Test numeric inputs
    assert handler._parse_input("1") == PromptAction.PROCEED
    assert handler._parse_input("2") == PromptAction.EDIT
    assert handler._parse_input("3") == PromptAction.CANCEL

    # Test text inputs
    assert handler._parse_input("proceed") == PromptAction.PROCEED
    assert handler._parse_input("edit") == PromptAction.EDIT
    assert handler._parse_input("cancel") == PromptAction.CANCEL

    # Test case insensitivity
    assert handler._parse_input("PROCEED") == PromptAction.PROCEED
    assert handler._parse_input("Edit") == PromptAction.EDIT

    # Test whitespace handling
    assert handler._parse_input(" 1 ") == PromptAction.PROCEED

    # Test invalid input
    assert handler._parse_input("invalid") is None
    assert handler._parse_input("0") is None
    assert handler._parse_input("4") is None

    print("✓ Input parsing works correctly")
except AssertionError as e:
    print(f"✗ Input parsing failed: {e}")
    sys.exit(1)

# Test 4: Prompt with mocked input
print("\nTest 4: Prompt with mocked input")
try:
    handler = InteractivePromptHandler()
    result = ValidationResult(warnings=["Test warning"])

    # Mock input to return "1"
    with patch('builtins.input', return_value='1'):
        with patch('sys.stdout', new_callable=StringIO):
            action = handler.prompt(result)
            assert action == PromptAction.PROCEED

    # Mock input to return "2"
    with patch('builtins.input', return_value='2'):
        with patch('sys.stdout', new_callable=StringIO):
            action = handler.prompt(result)
            assert action == PromptAction.EDIT

    # Mock input to return "3"
    with patch('builtins.input', return_value='3'):
        with patch('sys.stdout', new_callable=StringIO):
            action = handler.prompt(result)
            assert action == PromptAction.CANCEL

    print("✓ Prompt returns correct actions")
except Exception as e:
    print(f"✗ Prompt failed: {e}")
    sys.exit(1)

# Test 5: Prompt with invalid then valid input
print("\nTest 5: Prompt with retry on invalid input")
try:
    handler = InteractivePromptHandler()
    result = ValidationResult(warnings=["Test warning"])

    # Mock input to return invalid then valid
    with patch('builtins.input', side_effect=['invalid', '1']):
        with patch('sys.stdout', new_callable=StringIO):
            action = handler.prompt(result)
            assert action == PromptAction.PROCEED

    print("✓ Prompt retries on invalid input")
except Exception as e:
    print(f"✗ Retry logic failed: {e}")
    sys.exit(1)

# Test 6: Prompt displays validation results
print("\nTest 6: Prompt displays validation results")
try:
    handler = InteractivePromptHandler()
    result = ValidationResult(warnings=["Test warning message"])

    with patch('builtins.input', return_value='1'):
        mock_stdout = StringIO()
        with patch('sys.stdout', mock_stdout):
            action = handler.prompt(result)
            output = mock_stdout.getvalue()
            assert "Test warning message" in output
            assert "proceed" in output.lower() or "[1]" in output
            assert "edit" in output.lower() or "[2]" in output
            assert "cancel" in output.lower() or "[3]" in output

    print("✓ Prompt displays validation results and options")
except Exception as e:
    print(f"✗ Display test failed: {e}")
    sys.exit(1)

# Test 7: KeyboardInterrupt handling
print("\nTest 7: KeyboardInterrupt handling")
try:
    handler = InteractivePromptHandler()
    result = ValidationResult(warnings=["Warning"])

    with patch('builtins.input', side_effect=KeyboardInterrupt()):
        with patch('sys.stdout', new_callable=StringIO):
            action = handler.prompt(result)
            assert action == PromptAction.CANCEL

    print("✓ KeyboardInterrupt handled correctly")
except Exception as e:
    print(f"✗ KeyboardInterrupt handling failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("All tests passed! ✓")
print("="*50)
