#!/usr/bin/env python
"""Run all validation tests including interactive prompt."""

import sys
import subprocess

# Run all validation tests
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "tests/test_task_validator.py",
    "tests/test_validation_result.py",
    "tests/test_description_validation.py",
    "tests/test_acceptance_criteria_validation.py",
    "tests/test_test_mention_validation.py",
    "tests/test_priority_type_validation.py",
    "tests/test_strict_mode.py",
    "tests/test_validation_output.py",
    "tests/test_interactive_prompt.py",
    "-v", "--tb=short"
], capture_output=False)

sys.exit(result.returncode)
