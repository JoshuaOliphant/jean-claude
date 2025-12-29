#!/usr/bin/env python3
"""Quick linting check for modified orchestration files."""

import subprocess
import sys

FILES = [
    "src/jean_claude/orchestration/auto_continue.py",
    "src/jean_claude/orchestration/two_agent.py",
]

def main():
    print("Running ruff check on modified files...")
    print("=" * 60)

    all_passed = True

    for file_path in FILES:
        print(f"\nChecking: {file_path}")
        print("-" * 60)

        result = subprocess.run(
            ["uv", "run", "ruff", "check", file_path],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"✓ No linting errors found")
        else:
            all_passed = False
            print(f"✗ Linting errors found:")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"STDERR: {result.stderr}")

    print("\n" + "=" * 60)

    if all_passed:
        print("✓ All files passed linting checks!")
        return 0
    else:
        print("✗ Some files have linting errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
