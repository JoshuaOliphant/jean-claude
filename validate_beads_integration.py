#!/usr/bin/env python
"""Validate beads integration implementation and tests."""

import sys
import importlib.util

def check_module_exists(module_path):
    """Check if a module file exists and can be imported."""
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        if spec is None:
            return False, "Module spec is None"

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True, "Module loaded successfully"
    except Exception as e:
        return False, str(e)

def validate_beads_module():
    """Validate the beads.py module."""
    print("Validating beads.py module...")

    try:
        from jean_claude.core.beads import (
            BeadsTask,
            fetch_beads_task,
            update_beads_status,
            close_beads_task,
            generate_spec_from_beads
        )

        print("✅ All required functions found:")
        print("  - BeadsTask model")
        print("  - fetch_beads_task()")
        print("  - update_beads_status()")
        print("  - close_beads_task()")
        print("  - generate_spec_from_beads()")
        return True
    except ImportError as e:
        print(f"❌ Failed to import beads module: {e}")
        return False

def validate_test_file():
    """Validate the test file syntax."""
    print("\nValidating test_beads_integration.py...")

    success, msg = check_module_exists("tests/test_beads_integration.py")
    if success:
        print("✅ Test file is syntactically correct")
        return True
    else:
        print(f"❌ Test file has errors: {msg}")
        return False

def main():
    """Main validation function."""
    print("="*60)
    print("BEADS INTEGRATION VALIDATION")
    print("="*60)

    beads_ok = validate_beads_module()
    test_ok = validate_test_file()

    print("\n" + "="*60)
    if beads_ok and test_ok:
        print("✅ ALL VALIDATIONS PASSED!")
        print("="*60)
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
