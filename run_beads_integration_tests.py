#!/usr/bin/env python
"""Run beads integration tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run beads integration tests
    exit_code = pytest.main([
        "tests/test_beads_integration.py",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL BEADS INTEGRATION TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME BEADS INTEGRATION TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
