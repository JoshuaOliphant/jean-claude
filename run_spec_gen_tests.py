#!/usr/bin/env python
"""Run spec generator tests programmatically."""

import sys
import pytest

if __name__ == "__main__":
    # Run spec generator tests
    exit_code = pytest.main([
        "tests/core/test_spec_generator.py",
        "-v",
        "--tb=short"
    ])

    print(f"\n{'='*80}")
    print(f"Test exit code: {exit_code}")
    print(f"{'='*80}\n")

    sys.exit(exit_code)
