#!/usr/bin/env python
"""Run tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run the new backward compatibility tests
    exit_code = pytest.main([
        "tests/test_state.py::TestBackwardCompatibilityComprehensive",
        "-v",
        "--tb=short"
    ])
    sys.exit(exit_code)
