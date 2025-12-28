#!/usr/bin/env python
"""Run roundtrip tests."""

import sys
import pytest

if __name__ == "__main__":
    # Run the new roundtrip tests
    exit_code = pytest.main([
        "tests/test_state.py::TestBeadsFieldsSaveLoadRoundtrip",
        "-v",
        "--tb=short"
    ])
    sys.exit(exit_code)
