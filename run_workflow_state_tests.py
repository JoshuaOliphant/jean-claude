#!/usr/bin/env python
"""Run WorkflowState setup tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run WorkflowState setup tests
    exit_code = pytest.main([
        "tests/test_work_command.py::TestWorkflowStateSetup",
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ ALL WORKFLOWSTATE SETUP TESTS PASSED!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ SOME WORKFLOWSTATE SETUP TESTS FAILED!")
        print("="*60)

    sys.exit(exit_code)
