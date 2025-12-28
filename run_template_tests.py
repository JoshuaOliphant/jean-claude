#!/usr/bin/env python3
"""Run template tests to verify beads_spec.md template."""

import subprocess
import sys

def main():
    """Run the template tests."""
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/templates/test_beads_spec_template.py", "-v"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    print(result.stderr)

    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
