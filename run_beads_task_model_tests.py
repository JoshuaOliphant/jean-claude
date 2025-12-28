#!/usr/bin/env python
"""Run BeadsTask model tests to verify the feature is working."""

import sys
import pytest

if __name__ == "__main__":
    # Run the BeadsTask model tests
    exit_code = pytest.main([
        "tests/core/test_beads_task_model.py",
        "-v",
        "--tb=short"
    ])
    sys.exit(exit_code)
