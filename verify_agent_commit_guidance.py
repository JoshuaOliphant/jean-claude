#!/usr/bin/env python3
"""Verification script for agent commit guidance feature."""

import sys
import subprocess


def main():
    """Run tests for agent commit guidance."""
    print("=" * 60)
    print("Running Agent Commit Guidance Tests")
    print("=" * 60)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_agent_prompt_commit_guidance.py",
            "-v",
            "--tb=short",
        ],
        cwd=".",
    )

    if result.returncode == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
