#!/usr/bin/env python
"""Run beads model tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run beads model tests
    exit_code = pytest.main([
        "tests/core/test_beads_model.py",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL BEADS MODEL TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME BEADS MODEL TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
