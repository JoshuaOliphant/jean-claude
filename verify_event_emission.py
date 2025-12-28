#!/usr/bin/env python
"""Verify event emission feature in work command."""

import sys
import pytest

if __name__ == "__main__":
    # Run only the event emission tests
    exit_code = pytest.main([
        "tests/test_work_command.py::TestWorkEventEmission",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL EVENT EMISSION TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME EVENT EMISSION TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
