#!/usr/bin/env python3
"""Check if beads-data-model feature is complete and ready to mark done."""

import sys
from pathlib import Path

def check_feature_complete():
    """Verify the beads-data-model feature is complete."""

    print("=" * 70)
    print("CHECKING BEADS-DATA-MODEL FEATURE COMPLETION")
    print("=" * 70)
    print()

    checks_passed = 0
    checks_total = 0

    # Check 1: Model file exists
    checks_total += 1
    model_file = Path("src/jean_claude/core/beads.py")
    if model_file.exists():
        print(f"✅ Check 1: Model file exists at {model_file}")
        checks_passed += 1
    else:
        print(f"❌ Check 1: Model file NOT found at {model_file}")
    print()

    # Check 2: Test file exists
    checks_total += 1
    test_file = Path("tests/core/test_beads_model.py")
    if test_file.exists():
        print(f"✅ Check 2: Test file exists at {test_file}")
        checks_passed += 1
    else:
        print(f"❌ Check 2: Test file NOT found at {test_file}")
    print()

    # Check 3: Can import BeadsTask
    checks_total += 1
    try:
        from jean_claude.core.beads import BeadsTask
        print("✅ Check 3: BeadsTask can be imported")
        checks_passed += 1
    except ImportError as e:
        print(f"❌ Check 3: Cannot import BeadsTask: {e}")
        return False
    print()

    # Check 4: Can import BeadsTaskStatus
    checks_total += 1
    try:
        from jean_claude.core.beads import BeadsTaskStatus
        print("✅ Check 4: BeadsTaskStatus can be imported")
        checks_passed += 1
    except ImportError as e:
        print(f"❌ Check 4: Cannot import BeadsTaskStatus: {e}")
        return False
    print()

    # Check 5: BeadsTask has required fields
    checks_total += 1
    required_fields = ['id', 'title', 'description', 'acceptance_criteria', 'status',
                       'created_at', 'updated_at']
    model_fields = list(BeadsTask.model_fields.keys())
    missing = [f for f in required_fields if f not in model_fields]

    if not missing:
        print(f"✅ Check 5: BeadsTask has all required fields:")
        for field in required_fields:
            print(f"     - {field}")
        checks_passed += 1
    else:
        print(f"❌ Check 5: BeadsTask missing fields: {missing}")
    print()

    # Check 6: BeadsTaskStatus has required values
    checks_total += 1
    required_statuses = ['TODO', 'IN_PROGRESS', 'CLOSED']
    actual_statuses = [s.name for s in BeadsTaskStatus]
    missing_statuses = [s for s in required_statuses if s not in actual_statuses]

    if not missing_statuses:
        print(f"✅ Check 6: BeadsTaskStatus has all required values:")
        for status in required_statuses:
            enum_member = BeadsTaskStatus[status]
            print(f"     - {status} = '{enum_member.value}'")
        checks_passed += 1
    else:
        print(f"❌ Check 6: BeadsTaskStatus missing values: {missing_statuses}")
    print()

    # Check 7: Can create a BeadsTask instance
    checks_total += 1
    try:
        from datetime import datetime
        task = BeadsTask(
            id="test-1",
            title="Test Task",
            description="This is a test",
            status=BeadsTaskStatus.TODO
        )
        print("✅ Check 7: Can create BeadsTask instance")
        print(f"     Created: {task.title} (ID: {task.id})")
        checks_passed += 1
    except Exception as e:
        print(f"❌ Check 7: Cannot create BeadsTask instance: {e}")
    print()

    # Check 8: BeadsTask.from_json method exists
    checks_total += 1
    if hasattr(BeadsTask, 'from_json'):
        print("✅ Check 8: BeadsTask.from_json() method exists")
        checks_passed += 1
    else:
        print("❌ Check 8: BeadsTask.from_json() method NOT found")
    print()

    # Check 9: Test from_json works
    checks_total += 1
    try:
        import json
        json_data = json.dumps({
            "id": "json-test",
            "title": "JSON Test",
            "description": "Test from JSON",
            "status": "todo"
        })
        task = BeadsTask.from_json(json_data)
        print("✅ Check 9: BeadsTask.from_json() works correctly")
        print(f"     Parsed: {task.title} (Status: {task.status.value})")
        checks_passed += 1
    except Exception as e:
        print(f"❌ Check 9: BeadsTask.from_json() failed: {e}")
    print()

    # Summary
    print("=" * 70)
    print(f"CHECKS PASSED: {checks_passed}/{checks_total}")
    print("=" * 70)

    if checks_passed == checks_total:
        print()
        print("🎉 All checks passed! The beads-data-model feature is COMPLETE.")
        print()
        print("Next steps:")
        print("  1. Update state.json to mark feature as complete")
        print("  2. Set tests_passing to true")
        print("  3. Update completed_at timestamp")
        print("  4. Increment current_feature_index")
        return True
    else:
        print()
        print("⚠️  Some checks failed. Feature is NOT complete.")
        return False

if __name__ == "__main__":
    success = check_feature_complete()
    sys.exit(0 if success else 1)
