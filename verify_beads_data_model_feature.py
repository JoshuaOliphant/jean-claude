#!/usr/bin/env python3
"""Verification script for beads-data-model feature."""

import sys
import subprocess
from pathlib import Path

def main():
    """Verify the beads-data-model feature is complete."""

    print("=" * 60)
    print("VERIFYING BEADS-DATA-MODEL FEATURE")
    print("=" * 60)
    print()

    # 1. Check that the model file exists
    print("1. Checking if BeadsTask model exists...")
    model_file = Path("src/jean_claude/core/beads.py")
    if not model_file.exists():
        print(f"❌ Model file not found: {model_file}")
        return False
    print(f"✅ Model file exists: {model_file}")
    print()

    # 2. Check that the test file exists
    print("2. Checking if test file exists...")
    test_file = Path("tests/core/test_beads_model.py")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    print(f"✅ Test file exists: {test_file}")
    print()

    # 3. Try to import the model
    print("3. Testing import of BeadsTask and BeadsTaskStatus...")
    try:
        from jean_claude.core.beads import BeadsTask, BeadsTaskStatus
        print("✅ Successfully imported BeadsTask and BeadsTaskStatus")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False
    print()

    # 4. Verify the model has required fields
    print("4. Verifying BeadsTask has required fields...")
    required_fields = ['id', 'title', 'description', 'acceptance_criteria', 'status', 'created_at', 'updated_at']
    model_fields = BeadsTask.model_fields.keys()
    missing_fields = [f for f in required_fields if f not in model_fields]
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
        return False
    print(f"✅ All required fields present: {required_fields}")
    print()

    # 5. Verify BeadsTaskStatus enum has correct values
    print("5. Verifying BeadsTaskStatus enum...")
    required_statuses = ['TODO', 'IN_PROGRESS', 'CLOSED']
    enum_members = [e.name for e in BeadsTaskStatus]
    missing_statuses = [s for s in required_statuses if s not in enum_members]
    if missing_statuses:
        print(f"❌ Missing statuses: {missing_statuses}")
        return False
    print(f"✅ All required statuses present: {required_statuses}")
    print()

    # 6. Run the tests
    print("6. Running tests for beads-data-model...")
    result = subprocess.run(
        ["python", "-m", "pytest", str(test_file), "-v"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ Tests failed!")
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        return False

    print("✅ All tests passed!")
    print()
    print(result.stdout)
    print()

    print("=" * 60)
    print("✅ BEADS-DATA-MODEL FEATURE VERIFICATION COMPLETE")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
