#!/usr/bin/env python
"""Run tests for GitFileStager feature."""

import sys
import pytest

if __name__ == "__main__":
    print("Running tests for GitFileStager feature...")
    print()

    exit_code = pytest.main([
        "tests/test_git_file_stager.py",
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
