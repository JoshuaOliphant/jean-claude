#!/usr/bin/env python
"""Run commit message formatter tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run commit message formatter tests
    exit_code = pytest.main([
        "tests/test_commit_message_formatter.py",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL COMMIT MESSAGE FORMATTER TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
