#!/usr/bin/env python3
"""Quick inline test for interactive prompt handler."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jean_claude.core.interactive_prompt_handler import InteractivePromptHandler, PromptAction
from jean_claude.core.task_validator import ValidationResult

print("Testing InteractivePromptHandler...")

# Test 1: Can create handler
handler = InteractivePromptHandler()
print("✓ Handler created")

# Test 2: Parse input
assert handler._parse_input("1") == PromptAction.PROCEED
assert handler._parse_input("2") == PromptAction.EDIT
assert handler._parse_input("3") == PromptAction.CANCEL
assert handler._parse_input("proceed") == PromptAction.PROCEED
assert handler._parse_input("EDIT") == PromptAction.EDIT
print("✓ Input parsing works")

# Test 3: Enum values
assert PromptAction.PROCEED.value == "proceed"
assert PromptAction.EDIT.value == "edit"
assert PromptAction.CANCEL.value == "cancel"
print("✓ Enum values correct")

print("\nAll inline tests passed!")
