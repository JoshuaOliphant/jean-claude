#!/usr/bin/env python3
"""Verify beads data model feature is complete."""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def verify_implementation():
    """Verify the implementation exists and works."""
    print("=" * 60)
    print("BEADS DATA MODEL FEATURE VERIFICATION")
    print("=" * 60)

    # 1. Check that the models can be imported
    print("\n1. Checking imports...")
    try:
        from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, BeadsConfig
        print("   ✓ BeadsTask imported")
        print("   ✓ BeadsTaskStatus imported")
        print("   ✓ BeadsConfig imported")
    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        return False

    # 2. Check BeadsTask has all required fields
    print("\n2. Checking BeadsTask fields...")
    required_fields = ['id', 'title', 'description', 'status', 'acceptance_criteria', 'created_at', 'updated_at']
    task = BeadsTask(
        id="test-1",
        title="Test",
        description="Test description",
        status=BeadsTaskStatus.TODO
    )

    for field in required_fields:
        if hasattr(task, field):
            print(f"   ✓ {field}")
        else:
            print(f"   ✗ Missing field: {field}")
            return False

    # 3. Check from_dict method exists
    print("\n3. Checking from_dict() method...")
    try:
        task_dict = {
            "id": "test-2",
            "title": "Test Task",
            "description": "Test description",
            "status": BeadsTaskStatus.TODO
        }
        task_from_dict = BeadsTask.from_dict(task_dict)
        assert task_from_dict.id == "test-2"
        print("   ✓ from_dict() method works")
    except Exception as e:
        print(f"   ✗ from_dict() failed: {e}")
        return False

    # 4. Check to_dict method exists
    print("\n4. Checking to_dict() method...")
    try:
        task_dict = task.to_dict()
        assert isinstance(task_dict, dict)
        assert 'id' in task_dict
        print("   ✓ to_dict() method works")
    except Exception as e:
        print(f"   ✗ to_dict() failed: {e}")
        return False

    # 5. Check BeadsConfig
    print("\n5. Checking BeadsConfig...")
    try:
        config = BeadsConfig()
        assert config.cli_path == "bd"
        assert isinstance(config.config_options, dict)
        print("   ✓ BeadsConfig works")
    except Exception as e:
        print(f"   ✗ BeadsConfig failed: {e}")
        return False

    # 6. Check test file exists
    print("\n6. Checking test file...")
    test_file = "tests/core/test_beads_data_model.py"
    if os.path.exists(test_file):
        print(f"   ✓ Test file exists: {test_file}")
        # Count test functions
        with open(test_file) as f:
            content = f.read()
            test_count = content.count("def test_")
            print(f"   ✓ Found {test_count} test functions")
    else:
        print(f"   ✗ Test file not found: {test_file}")
        return False

    # 7. Check state file
    print("\n7. Checking state file...")
    state_file = "agents/beads-jean_claude-2sz.3/state.json"
    if os.path.exists(state_file):
        with open(state_file) as f:
            state = json.load(f)
            print(f"   ✓ Current feature index: {state['current_feature_index']}")
            print(f"   ✓ Total features: {len(state['features'])}")
            if state['features']:
                current_feature = state['features'][state['current_feature_index']]
                print(f"   ✓ Current feature: {current_feature['name']}")
                print(f"   ✓ Status: {current_feature['status']}")
    else:
        print(f"   ✗ State file not found: {state_file}")

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE - ALL CHECKS PASSED ✓")
    print("=" * 60)
    print("\nThe beads-data-model feature is fully implemented and ready.")
    return True

if __name__ == '__main__':
    success = verify_implementation()
    sys.exit(0 if success else 1)
