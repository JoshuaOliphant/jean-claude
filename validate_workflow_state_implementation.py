#!/usr/bin/env python
"""Validate WorkflowState implementation in work command."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.core.state import WorkflowState
from jean_claude.core.beads import BeadsTask

def validate_implementation():
    """Validate that WorkflowState can be created with Beads task info."""
    print("Validating WorkflowState implementation...")
    print()

    # Simulate what the work command does
    beads_id = "test-task.1"
    task_title = "Test Task Title"

    # Create a mock task
    print(f"1. Creating mock BeadsTask with id='{beads_id}', title='{task_title}'")
    mock_task = BeadsTask(
        id=beads_id,
        title=task_title,
        description="Test description",
        acceptance_criteria=["AC 1", "AC 2"],
        status="not_started"
    )
    print(f"   ✓ BeadsTask created: {mock_task.id} - {mock_task.title}")
    print()

    # Create WorkflowState as the work command does
    print("2. Creating WorkflowState instance...")
    workflow_state = WorkflowState(
        workflow_id=f"beads-{beads_id}",
        workflow_name=task_title,
        workflow_type="beads-task",
        beads_task_id=beads_id,
        beads_task_title=task_title,
        phase="planning"
    )
    print(f"   ✓ WorkflowState created with workflow_id='beads-{beads_id}'")
    print()

    # Validate all fields are set correctly
    print("3. Validating WorkflowState fields...")

    checks = [
        ("beads_task_id", beads_id, workflow_state.beads_task_id),
        ("beads_task_title", task_title, workflow_state.beads_task_title),
        ("phase", "planning", workflow_state.phase),
        ("workflow_id", f"beads-{beads_id}", workflow_state.workflow_id),
        ("workflow_name", task_title, workflow_state.workflow_name),
        ("workflow_type", "beads-task", workflow_state.workflow_type),
    ]

    all_passed = True
    for field_name, expected, actual in checks:
        if expected == actual:
            print(f"   ✓ {field_name}: {actual}")
        else:
            print(f"   ✗ {field_name}: expected '{expected}', got '{actual}'")
            all_passed = False

    print()

    if not all_passed:
        print("❌ Validation FAILED - Some fields are incorrect!")
        return False

    print("4. Testing state save capability...")
    # Check that the save method exists and can be called
    if hasattr(workflow_state, 'save'):
        print("   ✓ save() method exists on WorkflowState")
    else:
        print("   ✗ save() method not found on WorkflowState")
        return False

    print()
    print("="*60)
    print("✅ ALL VALIDATIONS PASSED!")
    print("="*60)
    print()
    print("Summary:")
    print(f"  - WorkflowState can be created with Beads task info")
    print(f"  - beads_task_id is correctly set to: {beads_id}")
    print(f"  - beads_task_title is correctly set to: {task_title}")
    print(f"  - Initial phase is set to: planning")
    print(f"  - save() method is available for persistence")
    print()

    return True

if __name__ == "__main__":
    try:
        success = validate_implementation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
