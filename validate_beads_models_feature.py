#!/usr/bin/env python3
"""Quick validation script to verify BeadsTask dataclass implementation."""

import sys
from datetime import datetime
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, BeadsConfig

def test_beads_task_creation():
    """Test that BeadsTask can be created with all required fields."""
    try:
        task = BeadsTask(
            id="test-1",
            title="Test Task",
            description="A test task description",
            status=BeadsTaskStatus.TODO
        )

        assert task.id == "test-1"
        assert task.title == "Test Task"
        assert task.description == "A test task description"
        assert task.status == BeadsTaskStatus.TODO
        assert task.acceptance_criteria == []
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

        print("✓ BeadsTask creation with required fields works")
        return True
    except Exception as e:
        print(f"✗ BeadsTask creation failed: {e}")
        return False

def test_beads_task_with_acceptance_criteria():
    """Test BeadsTask with acceptance criteria."""
    try:
        criteria = ["Criterion 1", "Criterion 2"]
        task = BeadsTask(
            id="test-2",
            title="Task with AC",
            description="Task description",
            status=BeadsTaskStatus.IN_PROGRESS,
            acceptance_criteria=criteria
        )

        assert task.acceptance_criteria == criteria
        print("✓ BeadsTask with acceptance criteria works")
        return True
    except Exception as e:
        print(f"✗ BeadsTask with acceptance criteria failed: {e}")
        return False

def test_beads_task_from_json():
    """Test BeadsTask.from_json classmethod."""
    try:
        json_str = '{"id": "json-1", "title": "JSON Task", "description": "From JSON", "status": "todo"}'
        task = BeadsTask.from_json(json_str)

        assert task.id == "json-1"
        assert task.title == "JSON Task"
        assert task.description == "From JSON"
        assert task.status == BeadsTaskStatus.TODO

        print("✓ BeadsTask.from_json works")
        return True
    except Exception as e:
        print(f"✗ BeadsTask.from_json failed: {e}")
        return False

def test_beads_task_with_timestamps():
    """Test BeadsTask with custom timestamps."""
    try:
        created = datetime(2025, 1, 1, 12, 0, 0)
        updated = datetime(2025, 1, 2, 14, 30, 0)

        task = BeadsTask(
            id="test-3",
            title="Timestamp Task",
            description="Task with timestamps",
            status=BeadsTaskStatus.CLOSED,
            created_at=created,
            updated_at=updated
        )

        assert task.created_at == created
        assert task.updated_at == updated

        print("✓ BeadsTask with custom timestamps works")
        return True
    except Exception as e:
        print(f"✗ BeadsTask with timestamps failed: {e}")
        return False

def test_beads_config():
    """Test BeadsConfig creation."""
    try:
        config = BeadsConfig()
        assert config.cli_path == "bd"
        assert config.config_options == {}

        config2 = BeadsConfig(cli_path="/usr/bin/bd", config_options={"timeout": 30})
        assert config2.cli_path == "/usr/bin/bd"
        assert config2.config_options["timeout"] == 30

        print("✓ BeadsConfig works")
        return True
    except Exception as e:
        print(f"✗ BeadsConfig failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("Validating BeadsTask dataclass implementation...\n")

    tests = [
        test_beads_task_creation,
        test_beads_task_with_acceptance_criteria,
        test_beads_task_from_json,
        test_beads_task_with_timestamps,
        test_beads_config,
    ]

    results = [test() for test in tests]

    print(f"\n{sum(results)}/{len(results)} tests passed")

    if all(results):
        print("\n✓ All validation tests passed!")
        return 0
    else:
        print("\n✗ Some validation tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
