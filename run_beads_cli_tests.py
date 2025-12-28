#!/usr/bin/env python
"""Run beads-cli-integration tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run beads client tests
    exit_code = pytest.main([
        "tests/core/test_beads_client.py",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL BEADS CLIENT TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME BEADS CLIENT TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
