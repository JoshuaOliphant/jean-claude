#!/usr/bin/env python3
"""Manual test for generate_spec_from_beads function."""

from datetime import datetime
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, generate_spec_from_beads

# Create a test task
task = BeadsTask(
    id="jean_claude-2sz.3",
    title="Implement jc work Command",
    description="Create a new 'jc work' command that integrates with Beads task management.",
    acceptance_criteria=[
        "Command fetches task from Beads",
        "Command generates spec from task",
        "Command runs workflow"
    ],
    status=BeadsTaskStatus.IN_PROGRESS,
    created_at=datetime(2024, 12, 24, 10, 0, 0),
    updated_at=datetime(2024, 12, 24, 15, 0, 0)
)

# Generate spec
spec = generate_spec_from_beads(task)

# Print the spec
print("Generated Spec:")
print("=" * 80)
print(spec)
print("=" * 80)

# Verify key elements
print("\nVerification:")
print(f"✓ Contains title header: {'# Implement jc work Command' in spec}")
print(f"✓ Contains Description section: {'## Description' in spec}")
print(f"✓ Contains Acceptance Criteria section: {'## Acceptance Criteria' in spec}")
print(f"✓ Contains all criteria items: {all(f'- {c}' in spec for c in task.acceptance_criteria)}")
print(f"✓ Contains Task Metadata section: {'## Task Metadata' in spec}")
print(f"✓ Contains task ID: {task.id in spec}")
print(f"✓ Ends with newline: {spec.endswith(chr(10))}")

print("\n✅ All checks passed!")
