#!/usr/bin/env python3
"""Run tests for beads-status-updater feature."""

import subprocess
import sys

def main():
    """Run the beads status updater tests."""
    print("="*60)
    print("Running beads-status-updater tests...")
    print("="*60)

    result = subprocess.run(
        ["python", "-m", "pytest", "tests/core/test_beads_status_updater.py", "-v"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        print("\n❌ FAILED: test_beads_status_updater.py")
        print("="*60)
        return False
    else:
        print("\n✅ PASSED: test_beads_status_updater.py")
        print("="*60)
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
