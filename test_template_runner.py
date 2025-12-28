#!/usr/bin/env python
"""Run template tests."""

import sys
import pytest

if __name__ == "__main__":
    exit_code = pytest.main([
        "tests/templates/test_beads_spec_template.py",
        "-v",
        "--tb=short"
    ])
    sys.exit(exit_code)
