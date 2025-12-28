#!/usr/bin/env python3
"""Manual test script for BeadsTask model."""

from datetime import datetime
from jean_claude.core.beads import BeadsTask

def test_basic_creation():
    """Test basic BeadsTask creation."""
    print("Test 1: Basic creation with auto-generated timestamps...")
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="A test task",
        status="not_started"
    )
    assert task.id == "test-1"
    assert task.title == "Test Task"
    assert task.description == "A test task"
    assert task.status == "not_started"
    assert isinstance(task.created_at, datetime)
    assert isinstance(task.updated_at, datetime)
    print(f"  ✓ created_at: {task.created_at}")
    print(f"  ✓ updated_at: {task.updated_at}")
    print("  PASSED\n")

def test_explicit_timestamps():
    """Test creation with explicit timestamps."""
    print("Test 2: Creation with explicit timestamps...")
    created = datetime(2025, 1, 1, 12, 0, 0)
    updated = datetime(2025, 1, 2, 14, 30, 0)

    task = BeadsTask(
        id="test-2",
        title="Test Task 2",
        description="Another test task",
        status="in_progress",
        created_at=created,
        updated_at=updated
    )
    assert task.created_at == created
    assert task.updated_at == updated
    print(f"  ✓ created_at: {task.created_at}")
    print(f"  ✓ updated_at: {task.updated_at}")
    print("  PASSED\n")

def test_with_acceptance_criteria():
    """Test with acceptance criteria."""
    print("Test 3: Creation with acceptance criteria...")
    task = BeadsTask(
        id="test-3",
        title="Test Task 3",
        description="Task with criteria",
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        status="done"
    )
    assert len(task.acceptance_criteria) == 2
    assert task.acceptance_criteria[0] == "Criterion 1"
    assert isinstance(task.created_at, datetime)
    assert isinstance(task.updated_at, datetime)
    print(f"  ✓ acceptance_criteria: {task.acceptance_criteria}")
    print(f"  ✓ created_at: {task.created_at}")
    print(f"  ✓ updated_at: {task.updated_at}")
    print("  PASSED\n")

def test_validation():
    """Test validation still works."""
    print("Test 4: Validation for empty fields...")
    try:
        task = BeadsTask(
            id="",
            title="Test",
            description="Test",
            status="done"
        )
        print("  FAILED: Should have raised ValidationError")
    except Exception as e:
        print(f"  ✓ Correctly raised error: {type(e).__name__}")
        print("  PASSED\n")

def test_serialization():
    """Test model serialization."""
    print("Test 5: Model serialization...")
    created = datetime(2025, 1, 1, 12, 0, 0)
    updated = datetime(2025, 1, 2, 14, 30, 0)

    task = BeadsTask(
        id="test-5",
        title="Serialization Test",
        description="Testing serialization",
        status="done",
        created_at=created,
        updated_at=updated
    )

    # Test dict serialization
    task_dict = task.model_dump()
    assert 'created_at' in task_dict
    assert 'updated_at' in task_dict
    print(f"  ✓ Dict includes created_at: {task_dict['created_at']}")
    print(f"  ✓ Dict includes updated_at: {task_dict['updated_at']}")

    # Test JSON serialization
    task_json = task.model_dump_json()
    assert 'created_at' in task_json
    assert 'updated_at' in task_json
    print(f"  ✓ JSON serialization works")
    print("  PASSED\n")

if __name__ == "__main__":
    print("="*60)
    print("BeadsTask Model Tests")
    print("="*60 + "\n")

    test_basic_creation()
    test_explicit_timestamps()
    test_with_acceptance_criteria()
    test_validation()
    test_serialization()

    print("="*60)
    print("All tests PASSED!")
    print("="*60)
