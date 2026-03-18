# ABOUTME: Test suite for workflow state management with feature-based progress tracking
# ABOUTME: Covers state persistence, feature tracking, and backward compatibility

"""Tests for workflow state management."""

import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from jean_claude.core.state import Feature, WorkflowState


class TestFeature:
    """Tests for the Feature model."""

    def test_feature_creation_defaults_and_validation(self):
        """Test feature creation with defaults, custom fields, and status validation."""
        from pydantic import ValidationError

        # Defaults
        feature = Feature(name="test-feature", description="Test description")
        assert feature.name == "test-feature"
        assert feature.description == "Test description"
        assert feature.status == "not_started"
        assert feature.test_file is None
        assert feature.tests_passing is False
        assert feature.started_at is None
        assert feature.completed_at is None

        # Custom fields
        feature2 = Feature(name="auth", description="Add auth",
                           test_file="tests/test_auth.py", tests_passing=True)
        assert feature2.test_file == "tests/test_auth.py"
        assert feature2.tests_passing is True

        # Valid status
        feature3 = Feature(name="test", description="desc", status="in_progress")
        assert feature3.status == "in_progress"

        # Invalid status
        with pytest.raises(ValidationError):
            Feature(name="test", description="desc", status="invalid_status")


class TestWorkflowState:
    """Tests for the WorkflowState model."""

    def test_workflow_state_creation_and_defaults(self):
        """Test creating a workflow state with defaults."""
        state = WorkflowState(workflow_id="test-123", workflow_name="Test", workflow_type="chore")
        assert state.workflow_id == "test-123"
        assert state.features == []
        assert state.current_feature_index == 0
        assert state.iteration_count == 0
        assert state.max_iterations == 50
        assert state.session_ids == []
        assert state.total_cost_usd == 0.0
        assert state.total_duration_ms == 0
        assert state.phase == "planning"
        assert isinstance(state.created_at, datetime)

    def test_feature_lifecycle(self):
        """Test add, start, complete, fail features and navigation."""
        state = WorkflowState(workflow_id="test-123", workflow_name="Test", workflow_type="feature")

        # No features
        assert state.current_feature is None
        assert state.get_next_feature() is None

        # Add features
        f1 = state.add_feature("f1", "First")
        f2 = state.add_feature("f2", "Second", test_file="tests/test2.py")
        assert len(state.features) == 2
        assert f2.test_file == "tests/test2.py"
        assert state.current_feature == f1
        assert state.get_next_feature() == f1

        # Start feature
        started = state.start_feature()
        assert started == f1
        assert f1.status == "in_progress"
        assert isinstance(f1.started_at, datetime)

        # Complete feature
        state.mark_feature_complete()
        assert f1.status == "completed"
        assert isinstance(f1.completed_at, datetime)
        assert state.current_feature_index == 1
        assert state.current_feature == f2

        # Start and fail
        state.start_feature()
        state.mark_feature_failed()
        assert f2.status == "failed"
        assert isinstance(f2.completed_at, datetime)

        # Out of bounds
        state.current_feature_index = 2
        assert state.current_feature is None
        assert state.get_next_feature() is None

    def test_progress_and_completion(self):
        """Test progress percentage, is_complete, and is_failed."""
        state = WorkflowState(workflow_id="test-123", workflow_name="Test", workflow_type="feature")

        assert state.progress_percentage == 0.0
        assert state.is_complete() is False

        for i in range(4):
            state.add_feature(f"f{i}", f"Feature {i}")

        assert state.progress_percentage == 0.0
        assert state.is_complete() is False
        assert state.is_failed() is False

        state.features[0].status = "completed"
        assert state.progress_percentage == 25.0

        state.features[1].status = "failed"
        assert state.is_failed() is True
        assert state.is_complete() is False

        for f in state.features:
            f.status = "completed"
        assert state.progress_percentage == 100.0
        assert state.is_complete() is True

    def test_get_summary_with_beads_fields(self):
        """Test get_summary includes all fields including Beads-specific."""
        state = WorkflowState(
            workflow_id="test-123", workflow_name="Test", workflow_type="feature",
            beads_task_id="jean_claude-2sz.2",
            beads_task_title="Link WorkflowState to Beads Tasks",
            phase="verifying",
        )
        state.add_feature("f1", "First")
        state.add_feature("f2", "Second")
        state.add_feature("f3", "Third")
        state.features[0].status = "completed"
        state.features[1].status = "in_progress"
        state.features[2].status = "failed"
        state.iteration_count = 5
        state.total_cost_usd = 1.25
        state.total_duration_ms = 5000

        summary = state.get_summary()
        assert summary["workflow_id"] == "test-123"
        assert summary["total_features"] == 3
        assert summary["completed_features"] == 1
        assert summary["failed_features"] == 1
        assert summary["in_progress_features"] == 1
        assert summary["progress_percentage"] == pytest.approx(33.33, rel=0.01)
        assert summary["is_complete"] is False
        assert summary["is_failed"] is True
        assert summary["iteration_count"] == 5
        assert summary["total_cost_usd"] == 1.25
        assert summary["beads_task_id"] == "jean_claude-2sz.2"
        assert summary["beads_task_title"] == "Link WorkflowState to Beads Tasks"
        assert summary["phase"] == "verifying"

    def test_update_phase(self):
        """Test that update_phase works for starting and completing phases."""
        state = WorkflowState(workflow_id="test-123", workflow_name="Test", workflow_type="feature")
        state.update_phase("planning", "running")
        assert state.phases["planning"].status == "running"
        assert isinstance(state.phases["planning"].started_at, datetime)

        state.update_phase("planning", "completed")
        assert state.phases["planning"].status == "completed"
        assert isinstance(state.phases["planning"].completed_at, datetime)

    def test_phase_validation(self):
        """Test valid phase literals and invalid phase rejection."""
        from pydantic import ValidationError

        for phase in ["planning", "implementing", "verifying", "complete"]:
            s = WorkflowState(workflow_id="t", workflow_name="T", workflow_type="feature", phase=phase)
            assert s.phase == phase

        with pytest.raises(ValidationError):
            WorkflowState(workflow_id="t", workflow_name="T", workflow_type="feature", phase="invalid")


class TestWorkflowStatePersistence:
    """Tests for state save/load functionality."""

    def test_save_load_roundtrip_with_all_fields(self):
        """Test save/load roundtrip including Beads fields."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            state = WorkflowState(
                workflow_id="test-123", workflow_name="Test Workflow", workflow_type="feature",
                beads_task_id="jean_claude-2sz.2",
                beads_task_title="Link WorkflowState to Beads Tasks",
                phase="implementing",
            )
            state.add_feature("f1", "First feature", test_file="tests/test1.py")
            state.add_feature("f2", "Second feature")
            state.start_feature()
            state.iteration_count = 3
            state.session_ids = ["session-1", "session-2"]
            state.total_cost_usd = 2.50

            state.save(project_root)

            state_file = project_root / "agents" / "test-123" / "state.json"
            assert state_file.exists()

            loaded = WorkflowState.load("test-123", project_root)
            assert loaded.workflow_id == state.workflow_id
            assert loaded.workflow_name == state.workflow_name
            assert len(loaded.features) == 2
            assert loaded.features[0].name == "f1"
            assert loaded.features[0].test_file == "tests/test1.py"
            assert loaded.features[0].status == "in_progress"
            assert loaded.iteration_count == 3
            assert loaded.session_ids == ["session-1", "session-2"]
            assert loaded.total_cost_usd == 2.50
            assert loaded.beads_task_id == "jean_claude-2sz.2"
            assert loaded.beads_task_title == "Link WorkflowState to Beads Tasks"
            assert loaded.phase == "implementing"

    def test_json_serialization_structure(self):
        """Test that raw JSON has correct structure."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            state = WorkflowState(workflow_id="test-123", workflow_name="Test", workflow_type="chore")
            feature = state.add_feature("f1", "Test feature")
            feature.status = "in_progress"
            feature.started_at = datetime(2024, 1, 1, 12, 0, 0)
            state.save(project_root)

            state_file = project_root / "agents" / "test-123" / "state.json"
            with open(state_file) as f:
                data = json.load(f)
            assert data["workflow_id"] == "test-123"
            assert len(data["features"]) == 1
            assert data["features"][0]["status"] == "in_progress"

    def test_load_nonexistent_workflow(self):
        """Test loading a workflow that doesn't exist raises FileNotFoundError."""
        with TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError, match="No state found for workflow"):
                WorkflowState.load("nonexistent-123", Path(tmpdir))

    def test_backward_compatibility_old_state_files(self):
        """Test that old state files (missing beads/phase fields) load with defaults."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Old state without beads_task_id, beads_task_title, or phase
            old_state_data = {
                "workflow_id": "legacy-123", "workflow_name": "Legacy",
                "workflow_type": "feature", "phases": {}, "inputs": {},
                "outputs": {}, "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(), "process_id": None,
                "features": [{
                    "name": "legacy-f1", "description": "Legacy feature",
                    "status": "completed", "test_file": "tests/test_legacy.py",
                    "tests_passing": True,
                    "started_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat(),
                }],
                "current_feature_index": 1, "iteration_count": 5,
                "max_iterations": 50, "session_ids": ["session-abc"],
                "total_cost_usd": 2.75, "total_duration_ms": 120000,
                "last_verification_at": datetime.now().isoformat(),
                "last_verification_passed": True, "verification_count": 3,
            }

            state_dir = project_root / "agents" / "legacy-123"
            state_dir.mkdir(parents=True, exist_ok=True)
            with open(state_dir / "state.json", "w") as f:
                json.dump(old_state_data, f)

            loaded = WorkflowState.load("legacy-123", project_root)
            assert loaded.workflow_id == "legacy-123"
            assert loaded.features[0].name == "legacy-f1"
            assert loaded.features[0].status == "completed"
            assert loaded.beads_task_id is None
            assert loaded.beads_task_title is None
            assert loaded.phase == "planning"
            assert loaded.iteration_count == 5
            assert loaded.total_cost_usd == 2.75
