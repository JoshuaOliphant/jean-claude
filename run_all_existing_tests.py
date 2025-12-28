#!/usr/bin/env python
"""Run all existing tests to verify nothing is broken."""

import sys
import pytest

if __name__ == "__main__":
    # Run all tests in the tests directory
    exit_code = pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])
    sys.exit(exit_code)
