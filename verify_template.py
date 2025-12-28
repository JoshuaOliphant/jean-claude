#!/usr/bin/env python
"""Verify the template works correctly."""

from datetime import datetime
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, generate_spec_from_beads

def main():
    # Create a test task
    task = BeadsTask(
        id="test-123",
        title="Test Task",
        description="This is a test task description.",
        acceptance_criteria=["Criterion 1", "Criterion 2", "Criterion 3"],
        status=BeadsTaskStatus.TODO,
        created_at=datetime(2024, 12, 24, 10, 0, 0),
        updated_at=datetime(2024, 12, 24, 15, 30, 0)
    )

    print("=== Test Task ===")
    print(f"ID: {task.id}")
    print(f"Title: {task.title}")
    print(f"Status: {task.status}")
    print()

    # Generate spec
    print("=== Generating Spec ===")
    try:
        spec = generate_spec_from_beads(task)
        print("SUCCESS! Generated spec:")
        print("-" * 60)
        print(spec)
        print("-" * 60)
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
