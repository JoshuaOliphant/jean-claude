#!/usr/bin/env python3
"""Verify that beads integration tests pass."""

import subprocess
import sys

def main():
    """Run beads integration tests and report results."""
    print("Running beads integration tests...")
    print("=" * 60)

    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/core/test_beads.py", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("✅ All beads integration tests PASSED!")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("❌ Some beads integration tests FAILED!")
            print("=" * 60)
            return 1

    except subprocess.TimeoutExpired:
        print("❌ Tests timed out!")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
