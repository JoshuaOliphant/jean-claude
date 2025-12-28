#!/usr/bin/env python
"""Run beads core module tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run beads core tests
    exit_code = pytest.main([
        "tests/core/test_beads.py",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL BEADS CORE MODULE TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME BEADS CORE MODULE TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
