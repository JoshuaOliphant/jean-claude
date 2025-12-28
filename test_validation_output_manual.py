#!/usr/bin/env python
"""Manual test runner for ValidationOutputFormatter."""

from jean_claude.core.task_validator import ValidationResult
from jean_claude.core.validation_output_formatter import ValidationOutputFormatter


def test_basic_functionality():
    """Test basic formatter functionality."""
    print("=" * 60)
    print("TEST 1: No issues")
    print("=" * 60)
    formatter = ValidationOutputFormatter()
    result = ValidationResult()
    output = formatter.format(result)
    print(output)
    print()

    print("=" * 60)
    print("TEST 2: Warnings only")
    print("=" * 60)
    formatter = ValidationOutputFormatter()
    result = ValidationResult(
        warnings=[
            "Task description is short (25 chars). Consider adding more detail.",
            "No acceptance criteria found. Consider adding clear success criteria.",
            "No mention of testing or verification found."
        ]
    )
    output = formatter.format(result)
    print(output)
    print()

    print("=" * 60)
    print("TEST 3: Errors only")
    print("=" * 60)
    formatter = ValidationOutputFormatter()
    result = ValidationResult(
        is_valid=False,
        errors=[
            "Task priority is required.",
            "Task type must be set."
        ]
    )
    output = formatter.format(result)
    print(output)
    print()

    print("=" * 60)
    print("TEST 4: Both warnings and errors")
    print("=" * 60)
    formatter = ValidationOutputFormatter()
    result = ValidationResult(
        is_valid=False,
        warnings=["Description could be more detailed"],
        errors=["Critical: Task type is missing"]
    )
    output = formatter.format(result)
    print(output)
    print()

    print("=" * 60)
    print("TEST 5: With options menu")
    print("=" * 60)
    formatter = ValidationOutputFormatter()
    result = ValidationResult(
        warnings=[
            "Task description is short",
            "No acceptance criteria found"
        ]
    )
    output = formatter.format_with_options(result)
    print(output)
    print()

    print("=" * 60)
    print("TEST 6: No color mode")
    print("=" * 60)
    formatter = ValidationOutputFormatter(use_color=False)
    result = ValidationResult(
        warnings=["Warning message"]
    )
    output = formatter.format(result)
    print(output)
    # Verify no ANSI codes
    assert "\033[" not in output
    assert "\x1b[" not in output
    print("✓ No ANSI codes found")
    print()

    print("=" * 60)
    print("TEST 7: Custom indentation")
    print("=" * 60)
    formatter = ValidationOutputFormatter(indent="    ")
    result = ValidationResult(warnings=["Warning"])
    output = formatter.format(result)
    print(output)
    print()

    print("=" * 60)
    print("All manual tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_basic_functionality()
