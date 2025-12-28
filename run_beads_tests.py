#!/usr/bin/env python
"""Run beads tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run beads tests
    exit_code = pytest.main([
        "tests/test_beads.py",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL BEADS TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME BEADS TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
