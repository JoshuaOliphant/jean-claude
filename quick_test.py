#!/usr/bin/env python
"""Quick test of generate_spec_from_beads function."""

import sys
sys.path.insert(0, '/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/src')

from jean_claude.core.beads import BeadsTask, generate_spec_from_beads

# Test 1: Basic functionality
print("Creating test task...")
task = BeadsTask(
    id="test-1",
    title="Test Task",
    description="This is a test description",
    acceptance_criteria=["Criterion 1", "Criterion 2", "Criterion 3"],
    status="not_started"
)

print("\nGenerating spec...")
spec = generate_spec_from_beads(task)

print("\n" + "="*60)
print("GENERATED SPEC:")
print("="*60)
print(spec)
print("="*60)

# Verify key components
print("\nVerifying spec contents...")
checks = [
    ("Title", "# Test Task" in spec),
    ("Description header", "## Description" in spec),
    ("Description content", "This is a test description" in spec),
    ("AC header", "## Acceptance Criteria" in spec),
    ("AC 1", "- Criterion 1" in spec),
    ("AC 2", "- Criterion 2" in spec),
    ("AC 3", "- Criterion 3" in spec),
    ("Ends with newline", spec.endswith("\n")),
]

all_passed = True
for check_name, result in checks:
    status = "✅" if result else "❌"
    print(f"{status} {check_name}: {result}")
    if not result:
        all_passed = False

print()
if all_passed:
    print("✅ ALL CHECKS PASSED!")
else:
    print("❌ SOME CHECKS FAILED!")
    sys.exit(1)

# Test 2: Without acceptance criteria
print("\n" + "="*60)
print("Test 2: Without acceptance criteria")
print("="*60)
task2 = BeadsTask(
    id="test-2",
    title="No Criteria",
    description="Task without criteria",
    status="done"
)

spec2 = generate_spec_from_beads(task2)
print(spec2)

if "## Acceptance Criteria" in spec2:
    print("⚠️  Note: Acceptance Criteria section present even with no criteria")
else:
    print("✅ No Acceptance Criteria section when list is empty")

# Test 3: None task
print("\n" + "="*60)
print("Test 3: None task should raise ValueError")
print("="*60)
try:
    generate_spec_from_beads(None)
    print("❌ FAILED - should have raised ValueError")
    sys.exit(1)
except ValueError as e:
    print(f"✅ PASSED - got expected ValueError: {e}")

print("\n" + "="*60)
print("✅ ALL QUICK TESTS PASSED!")
print("="*60)
