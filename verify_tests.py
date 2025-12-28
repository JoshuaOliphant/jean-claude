#!/usr/bin/env python
"""Quick verification script for backward compatibility tests."""

import json
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.core.state import WorkflowState


def test_load_old_state_without_any_beads_fields():
    """Test loading old state JSON that lacks beads_task_id, beads_task_title, and phase."""
    with TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create old-style state without ANY Beads fields
        old_state_data = {
            "workflow_id": "legacy-workflow-123",
            "workflow_name": "Legacy Workflow",
            "workflow_type": "feature",
            "phases": {},
            "inputs": {},
            "outputs": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "process_id": None,
            "features": [
                {
                    "name": "legacy-feature-1",
                    "description": "A feature from before Beads integration",
                    "status": "completed",
                    "test_file": "tests/test_legacy.py",
                    "tests_passing": True,
                    "started_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat(),
                }
            ],
            "current_feature_index": 1,
            "iteration_count": 5,
            "max_iterations": 50,
            "session_ids": ["session-abc-123"],
            "total_cost_usd": 2.75,
            "total_duration_ms": 120000,
            "last_verification_at": datetime.now().isoformat(),
            "last_verification_passed": True,
            "verification_count": 3,
            # NOTE: Missing beads_task_id, beads_task_title, and phase
        }

        # Write old state to disk
        state_dir = project_root / "agents" / "legacy-workflow-123"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "state.json"
        with open(state_file, "w") as f:
            json.dump(old_state_data, f)

        # Load the state - should succeed with default values
        loaded_state = WorkflowState.load("legacy-workflow-123", project_root)

        # Verify all existing fields are preserved
        assert loaded_state.workflow_id == "legacy-workflow-123"
        assert loaded_state.workflow_name == "Legacy Workflow"
        assert loaded_state.workflow_type == "feature"
        assert loaded_state.current_feature_index == 1
        assert loaded_state.iteration_count == 5
        assert loaded_state.total_cost_usd == 2.75
        assert len(loaded_state.features) == 1
        assert loaded_state.features[0].name == "legacy-feature-1"
        assert loaded_state.features[0].status == "completed"

        # Verify all NEW Beads fields have correct defaults
        assert loaded_state.beads_task_id is None
        assert loaded_state.beads_task_title is None
        assert loaded_state.phase == "planning"

        print("✓ test_load_old_state_without_any_beads_fields PASSED")


def test_load_old_state_with_partial_beads_fields():
    """Test loading state with only some Beads fields present."""
    with TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create state with only beads_task_id, missing beads_task_title and phase
        partial_state_data = {
            "workflow_id": "partial-123",
            "workflow_name": "Partial Beads Integration",
            "workflow_type": "feature",
            "phases": {},
            "inputs": {},
            "outputs": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "process_id": None,
            "features": [],
            "current_feature_index": 0,
            "iteration_count": 0,
            "max_iterations": 50,
            "session_ids": [],
            "total_cost_usd": 0.0,
            "total_duration_ms": 0,
            "last_verification_at": None,
            "last_verification_passed": True,
            "verification_count": 0,
            "beads_task_id": "jean_claude-xyz.456",
            # NOTE: Missing beads_task_title and phase
        }

        # Write state to disk
        state_dir = project_root / "agents" / "partial-123"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "state.json"
        with open(state_file, "w") as f:
            json.dump(partial_state_data, f)

        # Load the state
        loaded_state = WorkflowState.load("partial-123", project_root)

        # Verify the present field is loaded
        assert loaded_state.beads_task_id == "jean_claude-xyz.456"

        # Verify missing fields get defaults
        assert loaded_state.beads_task_title is None
        assert loaded_state.phase == "planning"

        print("✓ test_load_old_state_with_partial_beads_fields PASSED")


def test_load_and_save_preserves_defaults():
    """Test that loading old state and re-saving preserves default values."""
    with TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create old-style state without Beads fields
        old_state_data = {
            "workflow_id": "resave-test-123",
            "workflow_name": "Resave Test",
            "workflow_type": "chore",
            "phases": {},
            "inputs": {},
            "outputs": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "process_id": None,
            "features": [],
            "current_feature_index": 0,
            "iteration_count": 0,
            "max_iterations": 50,
            "session_ids": [],
            "total_cost_usd": 0.0,
            "total_duration_ms": 0,
            "last_verification_at": None,
            "last_verification_passed": True,
            "verification_count": 0,
        }

        # Write old state
        state_dir = project_root / "agents" / "resave-test-123"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "state.json"
        with open(state_file, "w") as f:
            json.dump(old_state_data, f)

        # Load old state
        loaded_state = WorkflowState.load("resave-test-123", project_root)

        # Verify defaults are applied
        assert loaded_state.beads_task_id is None
        assert loaded_state.beads_task_title is None
        assert loaded_state.phase == "planning"

        # Re-save the state
        loaded_state.save(project_root)

        # Load again and verify defaults are still correct
        reloaded_state = WorkflowState.load("resave-test-123", project_root)
        assert reloaded_state.beads_task_id is None
        assert reloaded_state.beads_task_title is None
        assert reloaded_state.phase == "planning"

        # Verify the saved JSON contains the default values
        with open(state_file) as f:
            saved_data = json.load(f)

        assert saved_data["beads_task_id"] is None
        assert saved_data["beads_task_title"] is None
        assert saved_data["phase"] == "planning"

        print("✓ test_load_and_save_preserves_defaults PASSED")


if __name__ == "__main__":
    try:
        test_load_old_state_without_any_beads_fields()
        test_load_old_state_with_partial_beads_fields()
        test_load_and_save_preserves_defaults()
        print("\n✅ All backward compatibility tests PASSED!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
