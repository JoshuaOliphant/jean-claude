#!/usr/bin/env python
"""Validate that ValidationOutputFormatter works correctly."""

import sys

# Test imports
try:
    from jean_claude.core.task_validator import ValidationResult
    from jean_claude.core.validation_output_formatter import ValidationOutputFormatter
    print("✓ Imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test basic functionality
try:
    formatter = ValidationOutputFormatter()
    print("✓ Formatter initialized")
except Exception as e:
    print(f"✗ Initialization failed: {e}")
    sys.exit(1)

# Test format with no issues
try:
    result = ValidationResult()
    output = formatter.format(result)
    assert "No issues" in output or "valid" in output.lower()
    print("✓ Format no issues works")
except Exception as e:
    print(f"✗ Format no issues failed: {e}")
    sys.exit(1)

# Test format with warnings
try:
    result = ValidationResult(warnings=["Warning 1", "Warning 2"])
    output = formatter.format(result)
    assert "Warning 1" in output
    assert "Warning 2" in output
    assert "1." in output  # Numbering
    print("✓ Format with warnings works")
except Exception as e:
    print(f"✗ Format with warnings failed: {e}")
    sys.exit(1)

# Test format with errors
try:
    result = ValidationResult(is_valid=False, errors=["Error 1", "Error 2"])
    output = formatter.format(result)
    assert "Error 1" in output
    assert "Error 2" in output
    print("✓ Format with errors works")
except Exception as e:
    print(f"✗ Format with errors failed: {e}")
    sys.exit(1)

# Test format_with_options
try:
    result = ValidationResult(warnings=["Warning"])
    output = formatter.format_with_options(result)
    assert "Warning" in output
    assert "[1]" in output or "1)" in output
    assert "[2]" in output or "2)" in output
    assert "[3]" in output or "3)" in output
    assert "proceed" in output.lower() or "continue" in output.lower()
    assert "edit" in output.lower()
    assert "cancel" in output.lower()
    print("✓ Format with options works")
except Exception as e:
    print(f"✗ Format with options failed: {e}")
    sys.exit(1)

# Test no color mode
try:
    formatter_no_color = ValidationOutputFormatter(use_color=False)
    result = ValidationResult(warnings=["Warning"])
    output = formatter_no_color.format(result)
    assert "\033[" not in output
    assert "\x1b[" not in output
    print("✓ No color mode works")
except Exception as e:
    print(f"✗ No color mode failed: {e}")
    sys.exit(1)

# Test custom indentation
try:
    formatter_custom = ValidationOutputFormatter(indent="    ")
    result = ValidationResult(warnings=["Warning"])
    output = formatter_custom.format(result)
    assert "    " in output
    print("✓ Custom indentation works")
except Exception as e:
    print(f"✗ Custom indentation failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("All validation checks passed! ✓")
print("=" * 60)
