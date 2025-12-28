#!/usr/bin/env python
"""Quick verification script for feature 8: work-fetch-and-generate-spec"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Test 1: Import the functions
print("Test 1: Importing functions...")
try:
    from jean_claude.core.beads import BeadsTask, fetch_beads_task, generate_spec_from_beads
    from jean_claude.cli.commands.work import work
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Test generate_spec_from_beads
print("\nTest 2: Testing generate_spec_from_beads...")
try:
    test_task = BeadsTask(
        id="test-123",
        title="Test Task",
        description="This is a test task description",
        acceptance_criteria=["AC 1", "AC 2", "AC 3"],
        status="not_started"
    )
    spec = generate_spec_from_beads(test_task)

    assert "# Test Task" in spec
    assert "## Description" in spec
    assert "This is a test task description" in spec
    assert "## Acceptance Criteria" in spec
    assert "- AC 1" in spec
    assert "- AC 2" in spec
    assert "- AC 3" in spec
    print("✓ generate_spec_from_beads works correctly")
except Exception as e:
    print(f"✗ generate_spec_from_beads failed: {e}")
    sys.exit(1)

# Test 3: Test generate_spec_from_beads with no acceptance criteria
print("\nTest 3: Testing generate_spec_from_beads with no acceptance criteria...")
try:
    test_task = BeadsTask(
        id="test-456",
        title="Simple Task",
        description="Simple description",
        acceptance_criteria=[],
        status="not_started"
    )
    spec = generate_spec_from_beads(test_task)

    assert "# Simple Task" in spec
    assert "## Description" in spec
    assert "Simple description" in spec
    # Should not have acceptance criteria section
    assert "## Acceptance Criteria" not in spec
    print("✓ generate_spec_from_beads handles empty acceptance criteria")
except Exception as e:
    print(f"✗ Test failed: {e}")
    sys.exit(1)

# Test 4: Test that work command has the right signature
print("\nTest 4: Checking work command signature...")
try:
    import inspect
    sig = inspect.signature(work.callback if hasattr(work, 'callback') else work)
    params = list(sig.parameters.keys())

    assert 'beads_id' in params
    assert 'model' in params
    assert 'show_plan' in params
    assert 'dry_run' in params
    assert 'auto_confirm' in params
    print("✓ work command has correct parameters")
except Exception as e:
    print(f"✗ Signature check failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✓ All verification tests passed!")
print("="*50)
