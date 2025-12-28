#!/usr/bin/env python
"""Run beads CLI wrapper tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run beads CLI wrapper tests
    exit_code = pytest.main([
        "tests/core/test_beads_cli_wrapper.py",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL BEADS CLI WRAPPER TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME BEADS CLI WRAPPER TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
