#!/usr/bin/env python
"""Quick verification script for commit workflow integration."""

import sys
import ast

def verify_syntax(filepath):
    """Verify Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        ast.parse(code)
        print(f"✓ Syntax OK: {filepath}")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax Error in {filepath}: {e}")
        return False

def verify_imports():
    """Verify key imports work."""
    try:
        from jean_claude.orchestration.auto_continue import run_auto_continue
        from jean_claude.core.feature_commit_orchestrator import FeatureCommitOrchestrator
        print("✓ Imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import Error: {e}")
        return False

if __name__ == "__main__":
    all_ok = True

    # Check syntax
    files_to_check = [
        "src/jean_claude/orchestration/auto_continue.py",
        "tests/test_commit_workflow_integration.py",
    ]

    for filepath in files_to_check:
        if not verify_syntax(filepath):
            all_ok = False

    # Check imports
    if not verify_imports():
        all_ok = False

    if all_ok:
        print("\n✓ All verification checks passed!")
        sys.exit(0)
    else:
        print("\n✗ Some verification checks failed")
        sys.exit(1)
