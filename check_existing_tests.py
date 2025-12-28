#!/usr/bin/env python
"""Check that existing tests pass before proceeding with new feature."""

import sys
import pytest

if __name__ == "__main__":
    # Run existing beads tests
    print("Running existing Beads tests...")
    exit_code = pytest.main([
        "tests/core/test_beads.py",
        "tests/templates/test_beads_spec.py",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL EXISTING TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME EXISTING TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
