#!/usr/bin/env python
"""Run spec generation tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run spec generation tests
    exit_code = pytest.main([
        "tests/test_spec_generation.py",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL SPEC GENERATION TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME SPEC GENERATION TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
