#!/usr/bin/env python3
"""Verification script for Feature 11: post-tool-use-hook."""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"📋 {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, capture_output=True, text=True, shell=isinstance(cmd, str))
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode == 0

def main():
    """Run verification steps."""
    print("🔍 FEATURE 11 VERIFICATION: post-tool-use-hook")
    print("="*60)

    all_passed = True

    # Step 1: Test imports
    print("\n📦 Step 1: Verifying imports...")
    if not run_command(
        "python -c 'from jean_claude.orchestration.post_tool_use_hook import post_tool_use_hook; print(\"✅ Import successful\")'",
        "Testing post_tool_use_hook import"
    ):
        all_passed = False
        print("❌ Import test failed")
    else:
        print("✅ Import test passed")

    # Step 2: Run inline test
    print("\n🧪 Step 2: Running inline tests...")
    if not run_command(
        ["python", "test_post_tool_use_inline.py"],
        "Running inline verification tests"
    ):
        all_passed = False
        print("❌ Inline tests failed")
    else:
        print("✅ Inline tests passed")

    # Step 3: Run all mailbox-related tests
    print("\n🧪 Step 3: Running all mailbox-related tests...")
    mailbox_tests = [
        "tests/core/test_message_model.py",
        "tests/core/test_mailbox_paths.py",
        "tests/core/test_inbox_count.py",
        "tests/core/test_message_writer.py",
        "tests/core/test_message_reader.py",
        "tests/core/test_inbox_count_persistence.py",
        "tests/core/test_mailbox_api.py",
        "tests/orchestration/test_subagent_stop_hook.py",
        "tests/orchestration/test_user_prompt_submit_hook.py",
        "tests/orchestration/test_post_tool_use_hook.py",
    ]

    if not run_command(
        ["python", "-m", "pytest"] + mailbox_tests + ["-v"],
        "Running all mailbox feature tests"
    ):
        all_passed = False
        print("❌ Some mailbox tests failed")
    else:
        print("✅ All mailbox tests passed")

    # Step 4: Run just the new tests
    print("\n🧪 Step 4: Running new post-tool-use-hook tests...")
    if not run_command(
        ["python", "-m", "pytest", "tests/orchestration/test_post_tool_use_hook.py", "-v"],
        "Running post-tool-use-hook tests"
    ):
        all_passed = False
        print("❌ Post-tool-use-hook tests failed")
    else:
        print("✅ Post-tool-use-hook tests passed")

    # Summary
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)

    if all_passed:
        print("✅ ALL VERIFICATION STEPS PASSED!")
        print("\n🎉 Feature 11 (post-tool-use-hook) is ready for state update")
        return 0
    else:
        print("❌ SOME VERIFICATION STEPS FAILED")
        print("\n⚠️  Please review the failures above before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main())
