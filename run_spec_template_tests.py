#!/usr/bin/env python
"""Run spec template tests."""

import sys
import pytest

if __name__ == "__main__":
    exit_code = pytest.main([
        "tests/test_spec_template.py",
        "-v",
        "--tb=short"
    ])
    print(f"\nTest run completed with exit code: {exit_code}")
    sys.exit(exit_code)
