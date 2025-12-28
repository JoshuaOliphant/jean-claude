#!/usr/bin/env python
"""Run validation tests."""

import sys
import subprocess

# Run the validation tests
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "tests/test_task_validator.py",
    "tests/test_validation_result.py",
    "tests/test_description_validation.py",
    "tests/test_acceptance_criteria_validation.py",
    "tests/test_test_mention_validation.py",
    "tests/test_priority_type_validation.py",
    "-v", "--tb=short"
], capture_output=False)

sys.exit(result.returncode)
