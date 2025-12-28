#!/usr/bin/env python
"""Run work command tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run work command tests
    exit_code = pytest.main([
        "tests/test_work_command.py",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL WORK COMMAND TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME WORK COMMAND TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
