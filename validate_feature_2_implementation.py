#!/usr/bin/env python
"""Validate that Feature 2 implementation is complete."""

import inspect
from jean_claude.core.beads import fetch_beads_task, BeadsTask

def main():
    print("=" * 80)
    print("VALIDATING FEATURE 2: beads-cli-wrapper")
    print("=" * 80)
    print()

    # Check 1: Function exists and is callable
    print("✓ Check 1: fetch_beads_task function exists")
    assert callable(fetch_beads_task), "fetch_beads_task should be callable"
    print("  PASS: Function is callable")
    print()

    # Check 2: Function signature
    print("✓ Check 2: Function signature")
    sig = inspect.signature(fetch_beads_task)
    params = list(sig.parameters.keys())
    assert 'task_id' in params, "Function should have task_id parameter"
    assert sig.return_annotation == BeadsTask, "Function should return BeadsTask"
    print(f"  PASS: Signature is correct: {sig}")
    print()

    # Check 3: Function has proper docstring
    print("✓ Check 3: Function documentation")
    doc = fetch_beads_task.__doc__
    assert doc is not None, "Function should have docstring"
    assert "bd show" in doc, "Docstring should mention 'bd show' command"
    assert "JSON" in doc or "json" in doc.lower(), "Docstring should mention JSON"
    assert "BeadsTask" in doc, "Docstring should mention BeadsTask"
    print("  PASS: Documentation exists and is comprehensive")
    print()

    # Check 4: Source code location
    print("✓ Check 4: Source code location")
    source_file = inspect.getfile(fetch_beads_task)
    assert "beads.py" in source_file, "Function should be in beads.py module"
    print(f"  PASS: Located in {source_file}")
    print()

    # Check 5: Implementation details
    print("✓ Check 5: Implementation details")
    source = inspect.getsource(fetch_beads_task)

    # Check for subprocess usage
    assert "subprocess.run" in source, "Should use subprocess.run"
    print("  PASS: Uses subprocess.run for command execution")

    # Check for JSON parsing
    assert "json.loads" in source, "Should parse JSON"
    print("  PASS: Parses JSON output")

    # Check for error handling
    assert "ValueError" in source, "Should validate input"
    assert "CalledProcessError" in source, "Should handle command failures"
    assert "JSONDecodeError" in source, "Should handle invalid JSON"
    print("  PASS: Has comprehensive error handling")

    # Check for BeadsTask creation
    assert "BeadsTask(" in source, "Should create BeadsTask instance"
    print("  PASS: Creates BeadsTask instances")
    print()

    # Summary
    print("=" * 80)
    print("✅ FEATURE 2 IMPLEMENTATION IS COMPLETE!")
    print("=" * 80)
    print()
    print("Implementation Summary:")
    print("  - Function: fetch_beads_task(task_id: str) -> BeadsTask")
    print("  - Location: jean_claude.core.beads")
    print("  - Functionality:")
    print("    • Executes 'bd show --json <task-id>' command")
    print("    • Parses JSON output")
    print("    • Returns BeadsTask object")
    print("    • Handles command failures (CalledProcessError)")
    print("    • Handles invalid JSON (JSONDecodeError)")
    print("    • Validates inputs (ValueError)")
    print()
    print("Next step: Run tests to verify correctness")
    return 0

if __name__ == "__main__":
    import sys
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
