#!/usr/bin/env python
"""Verify that test framework setup is complete."""

import sys
from pathlib import Path

def verify_framework_setup():
    """Check that all test framework components are in place."""
    project_root = Path(__file__).parent
    errors = []

    # Check pyproject.toml exists and has pytest config
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        errors.append("❌ pyproject.toml not found")
    else:
        content = pyproject.read_text()
        if "[tool.pytest.ini_options]" not in content:
            errors.append("❌ pytest configuration not found in pyproject.toml")
        else:
            print("✅ pyproject.toml has pytest configuration")

    # Check tests directory exists
    tests_dir = project_root / "tests"
    if not tests_dir.exists():
        errors.append("❌ tests directory not found")
    elif not tests_dir.is_dir():
        errors.append("❌ tests is not a directory")
    else:
        print("✅ tests directory exists")

    # Check conftest.py exists
    conftest = tests_dir / "conftest.py"
    if not conftest.exists():
        errors.append("❌ conftest.py not found")
    else:
        content = conftest.read_text()
        # Check for some expected fixtures
        if "@pytest.fixture" not in content:
            errors.append("❌ conftest.py doesn't contain fixtures")
        else:
            print("✅ conftest.py exists with fixtures")

    # Check test_framework_setup.py exists
    test_file = tests_dir / "test_framework_setup.py"
    if not test_file.exists():
        errors.append("❌ test_framework_setup.py not found")
    else:
        content = test_file.read_text()
        # Check for test classes
        if "class Test" not in content:
            errors.append("❌ test_framework_setup.py doesn't contain test classes")
        else:
            print("✅ test_framework_setup.py exists with tests")

    # Summary
    print("\n" + "="*60)
    if errors:
        print("VERIFICATION FAILED:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("✅ ALL CHECKS PASSED - Test framework setup is complete!")
        return True

if __name__ == "__main__":
    success = verify_framework_setup()
    sys.exit(0 if success else 1)
