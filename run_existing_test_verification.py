#!/usr/bin/env python3
"""Quick verification that existing tests pass."""

import subprocess
import sys

def main():
    """Run existing tests for completed features."""
    print("Running existing tests for completed features...")

    test_files = [
        "tests/core/test_beads_data_model.py",
        "tests/core/test_beads_cli_wrapper.py",
    ]

    for test_file in test_files:
        print(f"\n{'='*60}")
        print(f"Running: {test_file}")
        print('='*60)

        result = subprocess.run(
            ["python", "-m", "pytest", test_file, "-v"],
            capture_output=True,
            text=True
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:
            print(f"\n❌ FAILED: {test_file}")
            return False
        else:
            print(f"\n✅ PASSED: {test_file}")

    print("\n" + "="*60)
    print("✅ All existing tests passed!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
