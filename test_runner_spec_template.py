#!/usr/bin/env python
"""Run beads spec template tests."""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Import pytest and run tests
import pytest

if __name__ == "__main__":
    os.chdir(project_root)
    exit_code = pytest.main([
        "tests/templates/test_beads_spec_template.py",
        "-v",
        "--tb=short",
        "-p", "no:xdist"  # Disable parallel execution for approval
    ])
    sys.exit(exit_code)
