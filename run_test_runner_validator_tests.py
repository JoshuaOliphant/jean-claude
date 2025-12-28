#!/usr/bin/env python3
"""Run tests for TestRunnerValidator feature."""

import subprocess
import sys

def main():
    """Run tests for TestRunnerValidator."""
    print("=" * 70)
    print("Running tests for Feature 4: test-runner-validator")
    print("=" * 70)
    print()

    # Run the tests
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_test_runner_validator.py", "-v", "--tb=short"],
        capture_output=False,
        text=True
    )

    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✅ All TestRunnerValidator tests passed!")
    else:
        print("❌ Some tests failed. Please fix them before proceeding.")
    print("=" * 70)

    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
