#!/usr/bin/env python
"""Run spec generator tests."""

import sys
import pytest

if __name__ == "__main__":
    # Run spec generator tests
    print("Running spec generator tests...")
    exit_code = pytest.main([
        "tests/core/test_spec_generator.py",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL SPEC GENERATOR TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME SPEC GENERATOR TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
