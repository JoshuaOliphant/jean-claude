#!/usr/bin/env python3
"""Run tests for completed features before starting feature 4."""

import subprocess
import sys

def run_tests():
    """Run tests for the first three completed features."""
    test_files = [
        "tests/test_commit_message_formatter.py",
        "tests/test_conventional_commit_parser.py",
        "tests/test_git_file_stager.py",
    ]

    print("Running tests for completed features...")
    print("=" * 60)

    for test_file in test_files:
        print(f"\nRunning {test_file}...")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v"],
            capture_output=True,
            text=True
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:
            print(f"❌ Tests failed for {test_file}")
            return False
        else:
            print(f"✅ Tests passed for {test_file}")

    print("\n" + "=" * 60)
    print("✅ All existing feature tests passed!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
