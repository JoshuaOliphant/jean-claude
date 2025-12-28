#!/usr/bin/env python
"""Run all state tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run all state tests
    exit_code = pytest.main([
        "tests/test_state.py",
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
