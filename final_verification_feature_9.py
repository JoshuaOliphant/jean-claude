#!/usr/bin/env python3
"""Final verification for feature 9: interactive-prompt-handler."""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*60)
print("FEATURE 9 VERIFICATION: interactive-prompt-handler")
print("="*60)

# Part 1: Verify implementation file exists
print("\n1. Checking implementation file...")
impl_file = "src/jean_claude/core/interactive_prompt_handler.py"
if os.path.exists(impl_file):
    print(f"   ✓ {impl_file} exists")
else:
    print(f"   ✗ {impl_file} not found")
    sys.exit(1)

# Part 2: Verify test file exists
print("\n2. Checking test file...")
test_file = "tests/test_interactive_prompt.py"
if os.path.exists(test_file):
    print(f"   ✓ {test_file} exists")
else:
    print(f"   ✗ {test_file} not found")
    sys.exit(1)

# Part 3: Verify imports work
print("\n3. Verifying imports...")
try:
    from jean_claude.core.interactive_prompt_handler import InteractivePromptHandler, PromptAction
    from jean_claude.core.task_validator import ValidationResult
    print("   ✓ All imports successful")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Part 4: Verify PromptAction enum
print("\n4. Verifying PromptAction enum...")
try:
    assert hasattr(PromptAction, 'PROCEED')
    assert hasattr(PromptAction, 'EDIT')
    assert hasattr(PromptAction, 'CANCEL')
    assert PromptAction.PROCEED.value == "proceed"
    assert PromptAction.EDIT.value == "edit"
    assert PromptAction.CANCEL.value == "cancel"
    print("   ✓ PromptAction enum has correct values")
except AssertionError as e:
    print(f"   ✗ PromptAction enum validation failed: {e}")
    sys.exit(1)

# Part 5: Verify InteractivePromptHandler initialization
print("\n5. Verifying InteractivePromptHandler initialization...")
try:
    handler = InteractivePromptHandler()
    assert handler is not None
    assert hasattr(handler, 'formatter')
    assert hasattr(handler, 'prompt')
    assert hasattr(handler, '_parse_input')
    print("   ✓ Handler initializes with correct attributes")
except Exception as e:
    print(f"   ✗ Handler initialization failed: {e}")
    sys.exit(1)

# Part 6: Verify _parse_input method
print("\n6. Verifying input parsing...")
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
    assert handler._parse_input(" proceed ") == PromptAction.PROCEED

    # Test invalid inputs
    assert handler._parse_input("invalid") is None
    assert handler._parse_input("0") is None
    assert handler._parse_input("4") is None
    assert handler._parse_input("") is None

    print("   ✓ Input parsing works correctly")
except AssertionError as e:
    print(f"   ✗ Input parsing test failed: {e}")
    sys.exit(1)

# Part 7: Verify integration with ValidationResult
print("\n7. Verifying integration with ValidationResult...")
try:
    from unittest.mock import patch, StringIO

    handler = InteractivePromptHandler()
    result = ValidationResult(warnings=["Test warning"])

    # Mock input to avoid actual user interaction
    with patch('builtins.input', return_value='1'):
        with patch('sys.stdout', StringIO()):
            action = handler.prompt(result)
            assert action == PromptAction.PROCEED

    print("   ✓ Handler works with ValidationResult")
except Exception as e:
    print(f"   ✗ Integration test failed: {e}")
    sys.exit(1)

# Part 8: Verify formatter usage
print("\n8. Verifying formatter usage...")
try:
    from jean_claude.core.validation_output_formatter import ValidationOutputFormatter

    formatter = ValidationOutputFormatter(use_color=False)
    handler = InteractivePromptHandler(formatter=formatter)
    assert handler.formatter is formatter

    print("   ✓ Custom formatter can be passed to handler")
except Exception as e:
    print(f"   ✗ Formatter test failed: {e}")
    sys.exit(1)

# Part 9: Verify display output
print("\n9. Verifying display output...")
try:
    from unittest.mock import patch
    from io import StringIO

    handler = InteractivePromptHandler()
    result = ValidationResult(warnings=["Test warning message"])

    with patch('builtins.input', return_value='1'):
        mock_stdout = StringIO()
        with patch('sys.stdout', mock_stdout):
            action = handler.prompt(result)
            output = mock_stdout.getvalue()

            # Verify output contains expected elements
            assert "Test warning message" in output
            assert "1" in output or "proceed" in output.lower()
            assert "2" in output or "edit" in output.lower()
            assert "3" in output or "cancel" in output.lower()

    print("   ✓ Handler displays validation results and options")
except Exception as e:
    print(f"   ✗ Display output test failed: {e}")
    sys.exit(1)

# Part 10: Verify retry logic
print("\n10. Verifying retry logic on invalid input...")
try:
    from unittest.mock import patch
    from io import StringIO

    handler = InteractivePromptHandler()
    result = ValidationResult(warnings=["Warning"])

    # Simulate invalid input followed by valid input
    with patch('builtins.input', side_effect=['invalid', 'xyz', '1']):
        with patch('sys.stdout', StringIO()):
            action = handler.prompt(result)
            assert action == PromptAction.PROCEED

    print("   ✓ Handler retries on invalid input")
except Exception as e:
    print(f"   ✗ Retry logic test failed: {e}")
    sys.exit(1)

# Part 11: Verify KeyboardInterrupt handling
print("\n11. Verifying KeyboardInterrupt handling...")
try:
    from unittest.mock import patch
    from io import StringIO

    handler = InteractivePromptHandler()
    result = ValidationResult(warnings=["Warning"])

    with patch('builtins.input', side_effect=KeyboardInterrupt()):
        with patch('sys.stdout', StringIO()):
            action = handler.prompt(result)
            assert action == PromptAction.CANCEL

    print("   ✓ Handler handles KeyboardInterrupt correctly")
except Exception as e:
    print(f"   ✗ KeyboardInterrupt test failed: {e}")
    sys.exit(1)

# Part 12: Check file line counts
print("\n12. Checking implementation completeness...")
try:
    with open(impl_file, 'r') as f:
        impl_lines = len([l for l in f.readlines() if l.strip() and not l.strip().startswith('#')])

    with open(test_file, 'r') as f:
        test_lines = len([l for l in f.readlines() if l.strip() and not l.strip().startswith('#')])

    print(f"   ✓ Implementation: ~{impl_lines} lines of code")
    print(f"   ✓ Tests: ~{test_lines} lines of code")

    if impl_lines < 50:
        print(f"   ⚠ Warning: Implementation seems small ({impl_lines} lines)")
    if test_lines < 100:
        print(f"   ⚠ Warning: Tests seem limited ({test_lines} lines)")

except Exception as e:
    print(f"   ✗ File reading failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("ALL VERIFICATION CHECKS PASSED! ✓")
print("="*60)
print("\nFeature Summary:")
print("  - Implementation file: ✓")
print("  - Test file: ✓")
print("  - PromptAction enum: ✓")
print("  - InteractivePromptHandler class: ✓")
print("  - Input parsing: ✓")
print("  - ValidationResult integration: ✓")
print("  - Formatter integration: ✓")
print("  - Display output: ✓")
print("  - Retry logic: ✓")
print("  - Error handling: ✓")
print("\nFeature 9 (interactive-prompt-handler) is COMPLETE!")
print("="*60)
