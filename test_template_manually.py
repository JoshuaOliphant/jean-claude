#!/usr/bin/env python
"""Manual test of the beads_spec template."""

from datetime import datetime
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, generate_spec_from_beads

# Create a test task
task = BeadsTask(
    id="test-123",
    title="Test Task",
    description="This is a test task description",
    status=BeadsTaskStatus.TODO,
    acceptance_criteria=["Criterion 1", "Criterion 2", "Criterion 3"],
    created_at=datetime(2025, 1, 1, 12, 0, 0),
    updated_at=datetime(2025, 1, 2, 14, 30, 0)
)

# Generate spec
try:
    spec = generate_spec_from_beads(task)
    print("SUCCESS: Template generated successfully")
    print("\n" + "="*80)
    print("GENERATED SPEC:")
    print("="*80)
    print(spec)
    print("="*80)

    # Verify required sections
    assert "# Test Task" in spec, "Missing title"
    assert "## Description" in spec, "Missing Description section"
    assert "This is a test task description" in spec, "Missing description content"
    assert "## Requirements" in spec or "## Acceptance Criteria" in spec, "Missing AC/Requirements section"
    assert "Criterion 1" in spec, "Missing AC content"
    assert "test-123" in spec, "Missing task ID"

    print("\nAll assertions passed! ✓")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
