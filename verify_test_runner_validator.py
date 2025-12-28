#!/usr/bin/env python3
"""Verify TestRunnerValidator implementation."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def verify_import():
    """Verify that TestRunnerValidator can be imported."""
    try:
        from jean_claude.core.test_runner_validator import TestRunnerValidator
        print("✅ TestRunnerValidator imports successfully")
        return TestRunnerValidator
    except ImportError as e:
        print(f"❌ Failed to import TestRunnerValidator: {e}")
        return None

def verify_instantiation(TestRunnerValidator):
    """Verify that TestRunnerValidator can be instantiated."""
    try:
        validator = TestRunnerValidator()
        print("✅ TestRunnerValidator instantiates with defaults")

        validator_custom = TestRunnerValidator(
            test_command="python -m pytest",
            timeout=60
        )
        print("✅ TestRunnerValidator instantiates with custom params")
        return validator
    except Exception as e:
        print(f"❌ Failed to instantiate TestRunnerValidator: {e}")
        return None

def verify_methods(validator):
    """Verify that TestRunnerValidator has required methods."""
    methods = ['run_tests', 'parse_output', 'validate', 'get_error_message']

    all_present = True
    for method in methods:
        if hasattr(validator, method) and callable(getattr(validator, method)):
            print(f"✅ Method '{method}' exists")
        else:
            print(f"❌ Method '{method}' missing")
            all_present = False

    return all_present

def verify_attributes(validator):
    """Verify that TestRunnerValidator has required attributes."""
    attributes = ['test_command', 'repo_path', 'timeout']

    all_present = True
    for attr in attributes:
        if hasattr(validator, attr):
            print(f"✅ Attribute '{attr}' exists: {getattr(validator, attr)}")
        else:
            print(f"❌ Attribute '{attr}' missing")
            all_present = False

    return all_present

def verify_module_exports():
    """Verify that TestRunnerValidator is exported from core module."""
    try:
        from jean_claude.core import TestRunnerValidator
        print("✅ TestRunnerValidator is exported from jean_claude.core")
        return True
    except ImportError as e:
        print(f"❌ TestRunnerValidator not exported from core: {e}")
        return False

def main():
    """Run all verification checks."""
    print("=" * 70)
    print("Verifying TestRunnerValidator Implementation")
    print("=" * 70)
    print()

    # Import check
    TestRunnerValidator = verify_import()
    if not TestRunnerValidator:
        return 1

    print()

    # Instantiation check
    validator = verify_instantiation(TestRunnerValidator)
    if not validator:
        return 1

    print()

    # Methods check
    if not verify_methods(validator):
        return 1

    print()

    # Attributes check
    if not verify_attributes(validator):
        return 1

    print()

    # Module exports check
    if not verify_module_exports():
        return 1

    print()
    print("=" * 70)
    print("✅ All verification checks passed!")
    print("=" * 70)
    print()
    print("Next step: Run pytest tests to ensure all functionality works correctly")
    print("Command: python run_test_runner_validator_tests.py")

    return 0

if __name__ == "__main__":
    sys.exit(main())
