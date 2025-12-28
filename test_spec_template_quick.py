#!/usr/bin/env python3
"""Quick test runner for spec template tests."""

import sys
from datetime import datetime
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, generate_spec_from_beads

def test_basic_template():
    """Test basic template functionality."""
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="Test description",
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        status=BeadsTaskStatus.TODO,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 2, 12, 0, 0)
    )

    spec = generate_spec_from_beads(task)

    # Check all required sections
    checks = [
        ("Title", "# Test Task" in spec),
        ("Description section", "## Description" in spec),
        ("Description content", "Test description" in spec),
        ("Requirements section", "## Requirements" in spec),
        ("Acceptance Criteria section", "## Acceptance Criteria" in spec),
        ("Criterion 1", "- Criterion 1" in spec),
        ("Criterion 2", "- Criterion 2" in spec),
        ("Separator", "---" in spec),
        ("Task Metadata section", "## Task Metadata" in spec),
        ("Task ID", "test-1" in spec),
        ("Status", "todo" in spec),
        ("Created timestamp", "2024-01-01" in spec),
        ("Updated timestamp", "2024-01-02" in spec),
    ]

    all_passed = True
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n✅ All checks passed!")
        return True
    else:
        print("\n❌ Some checks failed!")
        print("\nGenerated spec:")
        print("=" * 80)
        print(spec)
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = test_basic_template()
    sys.exit(0 if success else 1)
