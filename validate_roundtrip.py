#!/usr/bin/env python
"""Validate roundtrip functionality manually."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from jean_claude.core.state import WorkflowState


def test_basic_roundtrip():
    """Test basic save/load roundtrip."""
    with TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create state with Beads fields
        original_state = WorkflowState(
            workflow_id="roundtrip-test",
            workflow_name="Roundtrip Test",
            workflow_type="feature",
            beads_task_id="jean_claude-2sz.2",
            beads_task_title="Test Roundtrip",
            phase="implementing",
        )

        # Save
        original_state.save(project_root)
        print("✓ State saved successfully")

        # Load
        loaded_state = WorkflowState.load("roundtrip-test", project_root)
        print("✓ State loaded successfully")

        # Verify
        assert loaded_state.beads_task_id == "jean_claude-2sz.2", f"Expected jean_claude-2sz.2, got {loaded_state.beads_task_id}"
        assert loaded_state.beads_task_title == "Test Roundtrip", f"Expected Test Roundtrip, got {loaded_state.beads_task_title}"
        assert loaded_state.phase == "implementing", f"Expected implementing, got {loaded_state.phase}"
        print("✓ All Beads fields verified")

        # Check JSON structure
        state_file = project_root / "agents" / "roundtrip-test" / "state.json"
        with open(state_file) as f:
            json_data = json.load(f)

        assert "beads_task_id" in json_data
        assert "beads_task_title" in json_data
        assert "phase" in json_data
        print("✓ JSON structure verified")

        print("\n✅ All roundtrip tests passed!")


if __name__ == "__main__":
    test_basic_roundtrip()
