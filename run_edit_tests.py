#!/usr/bin/env python
"""Quick script to test edit integration functionality."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    # Test imports
    print("Testing imports...")
    from jean_claude.core.edit_task_handler import EditTaskHandler
    from jean_claude.core.edit_and_revalidate import edit_and_revalidate
    from jean_claude.core.task_validator import TaskValidator, ValidationResult
    from jean_claude.core.interactive_prompt_handler import InteractivePromptHandler, PromptAction
    print("✓ All imports successful")

    # Test EditTaskHandler initialization
    print("\nTesting EditTaskHandler...")
    handler = EditTaskHandler()
    assert handler is not None
    assert handler.bd_path == "bd"
    print("✓ EditTaskHandler initializes correctly")

    # Test with custom bd_path
    handler2 = EditTaskHandler(bd_path="/custom/bd")
    assert handler2.bd_path == "/custom/bd"
    print("✓ EditTaskHandler accepts custom bd_path")

    # Test ValidationResult
    print("\nTesting ValidationResult...")
    result = ValidationResult()
    assert not result.has_warnings()
    assert not result.has_errors()
    print("✓ ValidationResult works")

    result_with_warnings = ValidationResult(warnings=["Test warning"])
    assert result_with_warnings.has_warnings()
    assert len(result_with_warnings.warnings) == 1
    print("✓ ValidationResult handles warnings")

    # Test PromptAction enum
    print("\nTesting PromptAction...")
    assert PromptAction.PROCEED is not None
    assert PromptAction.EDIT is not None
    assert PromptAction.CANCEL is not None
    assert PromptAction.PROCEED != PromptAction.EDIT
    print("✓ PromptAction enum works")

    print("\n" + "=" * 50)
    print("All basic tests passed!")
    print("=" * 50)

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
