#!/usr/bin/env python
"""Run tests for commit features."""

import sys
import pytest

if __name__ == "__main__":
    # Run all relevant tests
    print("Running tests for completed commit features...")
    print()

    test_files = [
        "tests/test_commit_message_formatter.py",
        "tests/test_conventional_commit_parser.py",
    ]

    exit_code = pytest.main([
        *test_files,
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
