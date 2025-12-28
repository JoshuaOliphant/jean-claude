#!/usr/bin/env python3
"""Verify the beads-data-model feature implementation."""

import sys
from datetime import datetime

try:
    # Import the BeadsTask and BeadsTaskStatus from the module
    from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, BeadsConfig

    print("✓ Successfully imported BeadsTask, BeadsTaskStatus, and BeadsConfig")

    # Test 1: Create a BeadsTask with all required fields
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="A test task description",
        status=BeadsTaskStatus.TODO
    )

    print("✓ Created BeadsTask with required fields")

    # Verify fields
    assert task.id == "test-1", "ID should be 'test-1'"
    assert task.title == "Test Task", "Title should be 'Test Task'"
    assert task.description == "A test task description", "Description mismatch"
    assert task.status == BeadsTaskStatus.TODO, "Status should be TODO"
    assert task.acceptance_criteria == [], "Acceptance criteria should default to empty list"
    assert isinstance(task.created_at, datetime), "created_at should be datetime"
    assert isinstance(task.updated_at, datetime), "updated_at should be datetime"

    print("✓ All required fields verified")

    # Test 2: Create with acceptance criteria
    task2 = BeadsTask(
        id="test-2",
        title="Task with AC",
        description="Task with acceptance criteria",
        status=BeadsTaskStatus.IN_PROGRESS,
        acceptance_criteria=["Criterion 1", "Criterion 2"]
    )

    assert len(task2.acceptance_criteria) == 2, "Should have 2 acceptance criteria"
    print("✓ Acceptance criteria handling verified")

    # Test 3: Test validation (empty id should fail)
    try:
        invalid_task = BeadsTask(
            id="",
            title="Test",
            description="Test",
            status=BeadsTaskStatus.TODO
        )
        print("✗ Empty id validation failed - should have raised error")
        sys.exit(1)
    except Exception as e:
        print(f"✓ Empty id validation working: {e}")

    # Test 4: Test from_json and to_dict methods
    import json

    json_str = json.dumps({
        "id": "json-test",
        "title": "JSON Test",
        "description": "Testing JSON parsing",
        "status": "todo"
    })

    task_from_json = BeadsTask.from_json(json_str)
    assert task_from_json.id == "json-test", "from_json should parse id correctly"
    print("✓ from_json method working")

    task_dict = task.to_dict()
    assert isinstance(task_dict, dict), "to_dict should return a dict"
    assert task_dict["id"] == "test-1", "to_dict should include id"
    print("✓ to_dict method working")

    # Test 5: BeadsConfig model
    config = BeadsConfig()
    assert config.cli_path == "bd", "Default CLI path should be 'bd'"
    assert config.config_options == {}, "Default config options should be empty dict"
    print("✓ BeadsConfig model working")

    config2 = BeadsConfig(cli_path="/custom/bd", config_options={"timeout": 30})
    assert config2.cli_path == "/custom/bd", "Custom CLI path should be set"
    assert config2.config_options["timeout"] == 30, "Config options should be set"
    print("✓ BeadsConfig with custom values working")

    # Test config to_dict and from_dict
    config_dict = config2.to_dict()
    config_restored = BeadsConfig.from_dict(config_dict)
    assert config_restored.cli_path == config2.cli_path, "Config roundtrip should preserve cli_path"
    print("✓ BeadsConfig serialization working")

    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60)
    print("\nBeadsTask dataclass implementation is complete with:")
    print("  • Required fields: id, title, description, status")
    print("  • Optional fields: acceptance_criteria, created_at, updated_at")
    print("  • Type hints and validation")
    print("  • from_json() and to_dict() methods")
    print("  • BeadsConfig model for CLI configuration")
    sys.exit(0)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
