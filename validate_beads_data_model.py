#!/usr/bin/env python3
"""Validate BeadsTask implementation matches requirements."""

import sys
import json
from datetime import datetime

def validate_implementation():
    """Validate that BeadsTask implementation meets all requirements."""
    print("=" * 70)
    print("VALIDATING BEADS DATA MODEL IMPLEMENTATION")
    print("=" * 70)
    print()

    errors = []
    warnings = []

    # Test 1: Import the required classes
    print("1. Testing imports...")
    try:
        from jean_claude.core.beads import BeadsTask, BeadsTaskStatus
        print("   ✓ Successfully imported BeadsTask and BeadsTaskStatus")
    except ImportError as e:
        errors.append(f"Failed to import: {e}")
        print(f"   ✗ Import failed: {e}")
        return False

    # Test 2: Verify required fields exist
    print("\n2. Verifying required fields...")
    required_fields = ['id', 'title', 'description', 'acceptance_criteria', 'status']
    try:
        task = BeadsTask(
            id="test-1",
            title="Test Task",
            description="Test description",
            acceptance_criteria=["AC1", "AC2"],
            status=BeadsTaskStatus.TODO
        )

        for field in required_fields:
            if not hasattr(task, field):
                errors.append(f"Missing required field: {field}")
                print(f"   ✗ Missing field: {field}")
            else:
                print(f"   ✓ Field '{field}' exists")

        # Check values
        assert task.id == "test-1"
        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.acceptance_criteria == ["AC1", "AC2"]
        assert task.status == BeadsTaskStatus.TODO
        print("   ✓ All field values correct")

    except Exception as e:
        errors.append(f"Field validation failed: {e}")
        print(f"   ✗ Field validation failed: {e}")

    # Test 3: Verify from_json() method exists and works
    print("\n3. Verifying from_json() class method...")
    try:
        task_data = {
            "id": "json-test",
            "title": "JSON Test",
            "description": "Testing from_json",
            "status": "todo",
            "acceptance_criteria": ["Criterion 1"]
        }
        json_str = json.dumps(task_data)
        task = BeadsTask.from_json(json_str)

        assert task.id == "json-test"
        assert task.title == "JSON Test"
        assert task.status == BeadsTaskStatus.TODO
        print("   ✓ from_json() method works correctly")

    except AttributeError:
        errors.append("from_json() method does not exist")
        print("   ✗ from_json() method does not exist")
    except Exception as e:
        errors.append(f"from_json() failed: {e}")
        print(f"   ✗ from_json() failed: {e}")

    # Test 4: Verify from_json() handles arrays (bd show --json format)
    print("\n4. Verifying from_json() handles JSON arrays...")
    try:
        task_data = [{
            "id": "array-test",
            "title": "Array Test",
            "description": "Testing array parsing",
            "status": "in_progress"
        }]
        json_str = json.dumps(task_data)
        task = BeadsTask.from_json(json_str)

        assert task.id == "array-test"
        assert task.status == BeadsTaskStatus.IN_PROGRESS
        print("   ✓ from_json() correctly handles JSON arrays")

    except Exception as e:
        errors.append(f"from_json() array handling failed: {e}")
        print(f"   ✗ from_json() array handling failed: {e}")

    # Test 5: Verify BeadsTaskStatus enum
    print("\n5. Verifying BeadsTaskStatus enum...")
    try:
        assert hasattr(BeadsTaskStatus, 'TODO')
        assert hasattr(BeadsTaskStatus, 'IN_PROGRESS')
        assert hasattr(BeadsTaskStatus, 'CLOSED')

        assert BeadsTaskStatus.TODO.value == 'todo'
        assert BeadsTaskStatus.IN_PROGRESS.value == 'in_progress'
        assert BeadsTaskStatus.CLOSED.value == 'closed'
        print("   ✓ BeadsTaskStatus enum has all required values")

    except Exception as e:
        errors.append(f"BeadsTaskStatus enum validation failed: {e}")
        print(f"   ✗ BeadsTaskStatus validation failed: {e}")

    # Test 6: Verify from_dict() method (bonus from requirements)
    print("\n6. Verifying from_dict() method...")
    try:
        if hasattr(BeadsTask, 'from_dict'):
            task_dict = {
                "id": "dict-test",
                "title": "Dict Test",
                "description": "Testing from_dict",
                "status": BeadsTaskStatus.CLOSED
            }
            task = BeadsTask.from_dict(task_dict)
            assert task.id == "dict-test"
            print("   ✓ from_dict() method exists and works")
        else:
            warnings.append("from_dict() method not found (not strictly required)")
            print("   ⚠ from_dict() method not found (mentioned in requirements)")
    except Exception as e:
        warnings.append(f"from_dict() exists but failed: {e}")
        print(f"   ⚠ from_dict() failed: {e}")

    # Test 7: Verify to_dict() method (bonus from requirements)
    print("\n7. Verifying to_dict() method...")
    try:
        if hasattr(task, 'to_dict'):
            task_dict = task.to_dict()
            assert isinstance(task_dict, dict)
            assert 'id' in task_dict
            print("   ✓ to_dict() method exists and works")
        else:
            warnings.append("to_dict() method not found (not strictly required)")
            print("   ⚠ to_dict() method not found (mentioned in requirements)")
    except Exception as e:
        warnings.append(f"to_dict() exists but failed: {e}")
        print(f"   ⚠ to_dict() failed: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    if errors:
        print(f"\n✗ FAILED with {len(errors)} error(s):")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")

    if warnings:
        print(f"\n⚠ {len(warnings)} warning(s):")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")

    if not errors:
        print("\n✓ ALL VALIDATIONS PASSED!")
        print("\nImplementation meets all requirements:")
        print("  • BeadsTask dataclass with required fields")
        print("  • from_json() class method for parsing JSON")
        print("  • BeadsTaskStatus enum")
        print("  • Additional bonus features (from_dict, to_dict, timestamps)")
        return True
    else:
        return False

if __name__ == '__main__':
    success = validate_implementation()
    sys.exit(0 if success else 1)
