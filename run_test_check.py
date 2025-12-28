#!/usr/bin/env python
"""Quick test runner to check BeadsClient tests."""

import sys
import pytest

if __name__ == "__main__":
    # Run the BeadsClient tests
    exit_code = pytest.main([
        "tests/test_beads_client.py",
        "-v",
        "--tb=short"
    ])

    sys.exit(exit_code)
