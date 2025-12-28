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

    def test_feature_creation(self):
        """Test creating a feature with default values."""
        feature = Feature(name="test-feature", description="Test description")

        assert feature.name == "test-feature"
        assert feature.description == "Test description"
        assert feature.status == "not_started"
        assert feature.test_file is None
        assert feature.tests_passing is False
        assert feature.started_at is None
        assert feature.completed_at is None

    def test_feature_with_test_file(self):
        """Test creating a feature with test file."""
        feature = Feature(
            name="auth-feature",
            description="Add authentication",
            test_file="tests/test_auth.py",
            tests_passing=True,
        )

        assert feature.test_file == "tests/test_auth.py"
        assert feature.tests_passing is True

    def test_feature_status_literals(self):
        """Test that feature status is constrained to valid literals."""
        from pydantic import ValidationError

        feature = Feature(name="test", description="desc", status="in_progress")
        assert feature.status == "in_progress"

        # Pydantic will validate this at runtime
        with pytest.raises(ValidationError):
            Feature(name="test", description="desc", status="invalid_status")


class TestWorkflowState:
    """Tests for the WorkflowState model."""

    def test_workflow_state_creation(self):
        """Test creating a workflow state with defaults."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test Workflow",
            workflow_type="chore",
        )

        assert state.workflow_id == "test-123"
        assert state.workflow_name == "Test Workflow"
        assert state.workflow_type == "chore"
        assert state.features == []
        assert state.current_feature_index == 0
        assert state.iteration_count == 0
        assert state.max_iterations == 50
        assert state.session_ids == []
        assert state.total_cost_usd == 0.0
        assert state.total_duration_ms == 0
        assert isinstance(state.created_at, datetime)
        assert isinstance(state.updated_at, datetime)

    def test_add_feature(self):
        """Test adding features to workflow state."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="feature",
        )

        feature1 = state.add_feature("feature-1", "First feature")
        feature2 = state.add_feature("feature-2", "Second feature", test_file="tests/test2.py")

        assert len(state.features) == 2
        assert state.features[0] == feature1
        assert state.features[1] == feature2
        assert feature1.name == "feature-1"
        assert feature2.test_file == "tests/test2.py"

    def test_current_feature_property(self):
        """Test current_feature property."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="feature",
        )

        # No features yet
        assert state.current_feature is None

        # Add features
        feature1 = state.add_feature("f1", "First")
        feature2 = state.add_feature("f2", "Second")

        # Should return first feature
        assert state.current_feature == feature1

        # Advance index
        state.current_feature_index = 1
        assert state.current_feature == feature2

        # Out of bounds
        state.current_feature_index = 2
        assert state.current_feature is None

    def test_get_next_feature(self):
        """Test getting next feature."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="feature",
        )

        f1 = state.add_feature("f1", "First")
        f2 = state.add_feature("f2", "Second")

        assert state.get_next_feature() == f1
        state.current_feature_index = 1
        assert state.get_next_feature() == f2
        state.current_feature_index = 2
        assert state.get_next_feature() is None

    def test_start_feature(self):
        """Test starting a feature."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="feature",
        )

        feature = state.add_feature("f1", "First")
        assert feature.status == "not_started"
        assert feature.started_at is None

        started = state.start_feature()

        assert started == feature
        assert feature.status == "in_progress"
        assert isinstance(feature.started_at, datetime)

    def test_mark_feature_complete(self):
        """Test marking feature as complete."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="feature",
        )

        f1 = state.add_feature("f1", "First")
        f2 = state.add_feature("f2", "Second")

        state.start_feature()
        assert state.current_feature_index == 0

        state.mark_feature_complete()

        assert f1.status == "completed"
        assert isinstance(f1.completed_at, datetime)
        assert state.current_feature_index == 1
        assert state.current_feature == f2

    def test_mark_feature_failed(self):
        """Test marking feature as failed."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="feature",
        )

        feature = state.add_feature("f1", "First")
        state.start_feature()

        state.mark_feature_failed()

        assert feature.status == "failed"
        assert isinstance(feature.completed_at, datetime)

    def test_progress_percentage(self):
        """Test progress percentage calculation."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="feature",
        )

        # No features
        assert state.progress_percentage == 0.0

        # Add 4 features
        for i in range(4):
            state.add_feature(f"f{i}", f"Feature {i}")

        # 0% complete
        assert state.progress_percentage == 0.0

        # Complete 1 of 4 = 25%
        state.features[0].status = "completed"
        assert state.progress_percentage == 25.0

        # Complete 2 of 4 = 50%
        state.features[1].status = "completed"
        assert state.progress_percentage == 50.0

        # Complete all = 100%
        state.features[2].status = "completed"
        state.features[3].status = "completed"
        assert state.progress_percentage == 100.0

    def test_is_complete(self):
        """Test is_complete method."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="feature",
        )

        # No features = not complete
        assert state.is_complete() is False

        # Add features
        f1 = state.add_feature("f1", "First")
        f2 = state.add_feature("f2", "Second")

        # Not all complete
        assert state.is_complete() is False

        # One complete, one not
        f1.status = "completed"
        assert state.is_complete() is False

        # Both complete
        f2.status = "completed"
        assert state.is_complete() is True

    def test_is_failed(self):
        """Test is_failed method."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="feature",
        )

        f1 = state.add_feature("f1", "First")
        state.add_feature("f2", "Second")

        assert state.is_failed() is False

        f1.status = "failed"
        assert state.is_failed() is True

    def test_get_summary(self):
        """Test get_summary method."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="feature",
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
        assert summary["workflow_type"] == "feature"
        assert summary["total_features"] == 3
        assert summary["completed_features"] == 1
        assert summary["failed_features"] == 1
        assert summary["in_progress_features"] == 1
        assert summary["progress_percentage"] == pytest.approx(33.33, rel=0.01)
        assert summary["is_complete"] is False
        assert summary["is_failed"] is True
        assert summary["iteration_count"] == 5
        assert summary["total_cost_usd"] == 1.25
        assert summary["total_duration_ms"] == 5000


class TestWorkflowStatePersistence:
    """Tests for state save/load functionality."""

    def test_save_and_load(self):
        """Test saving and loading workflow state."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create state
            state = WorkflowState(
                workflow_id="test-123",
                workflow_name="Test Workflow",
                workflow_type="feature",
            )
            state.add_feature("f1", "First feature", test_file="tests/test1.py")
            state.add_feature("f2", "Second feature")
            state.start_feature()
            state.iteration_count = 3
            state.session_ids = ["session-1", "session-2"]
            state.total_cost_usd = 2.50

            # Save
            state.save(project_root)

            # Verify file exists
            state_file = project_root / "agents" / "test-123" / "state.json"
            assert state_file.exists()

            # Load
            loaded_state = WorkflowState.load("test-123", project_root)

            # Verify all fields
            assert loaded_state.workflow_id == state.workflow_id
            assert loaded_state.workflow_name == state.workflow_name
            assert loaded_state.workflow_type == state.workflow_type
            assert len(loaded_state.features) == 2
            assert loaded_state.features[0].name == "f1"
            assert loaded_state.features[0].test_file == "tests/test1.py"
            assert loaded_state.features[0].status == "in_progress"
            assert loaded_state.features[1].name == "f2"
            assert loaded_state.current_feature_index == 0
            assert loaded_state.iteration_count == 3
            assert loaded_state.session_ids == ["session-1", "session-2"]
            assert loaded_state.total_cost_usd == 2.50

    def test_json_serialization(self):
        """Test that state serializes correctly to JSON."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            state = WorkflowState(
                workflow_id="test-123",
                workflow_name="Test",
                workflow_type="chore",
            )
            feature = state.add_feature("f1", "Test feature")
            feature.status = "in_progress"
            feature.started_at = datetime(2024, 1, 1, 12, 0, 0)

            state.save(project_root)

            # Read raw JSON
            state_file = project_root / "agents" / "test-123" / "state.json"
            with open(state_file) as f:
                data = json.load(f)

            # Verify JSON structure
            assert data["workflow_id"] == "test-123"
            assert data["workflow_type"] == "chore"
            assert len(data["features"]) == 1
            assert data["features"][0]["name"] == "f1"
            assert data["features"][0]["status"] == "in_progress"
            assert "started_at" in data["features"][0]

    def test_load_nonexistent_workflow(self):
        """Test loading a workflow that doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            with pytest.raises(FileNotFoundError, match="No state found for workflow"):
                WorkflowState.load("nonexistent-123", project_root)

    def test_backward_compatibility(self):
        """Test that new fields don't break existing state files."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create old-style state (without new feature fields)
            old_state_data = {
                "workflow_id": "old-123",
                "workflow_name": "Old Workflow",
                "workflow_type": "chore",
                "phases": {},
                "inputs": {},
                "outputs": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "process_id": None,
            }

            # Write old state
            state_dir = project_root / "agents" / "old-123"
            state_dir.mkdir(parents=True, exist_ok=True)
            state_file = state_dir / "state.json"
            with open(state_file, "w") as f:
                json.dump(old_state_data, f)

            # Should load successfully with defaults for new fields
            loaded_state = WorkflowState.load("old-123", project_root)

            assert loaded_state.workflow_id == "old-123"
            assert loaded_state.features == []
            assert loaded_state.current_feature_index == 0
            assert loaded_state.iteration_count == 0
            assert loaded_state.session_ids == []
            assert loaded_state.total_cost_usd == 0.0


class TestWorkflowPhase:
    """Tests for WorkflowPhase (backward compatibility)."""

    def test_update_phase(self):
        """Test that update_phase still works with new state."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test",
            workflow_type="feature",
        )

        # Update phase
        state.update_phase("planning", "running")

        assert "planning" in state.phases
        assert state.phases["planning"].status == "running"
        assert isinstance(state.phases["planning"].started_at, datetime)

        # Complete phase
        state.update_phase("planning", "completed")
        assert state.phases["planning"].status == "completed"
        assert isinstance(state.phases["planning"].completed_at, datetime)


class TestPhaseField:
    """Tests for the phase field in WorkflowState."""

    def test_phase_default_value(self):
        """Test that phase defaults to 'planning'."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test Workflow",
            workflow_type="feature",
        )

        assert state.phase == "planning"

    def test_phase_valid_literals(self):
        """Test that all valid phase literals work."""
        valid_phases = ["planning", "implementing", "verifying", "complete"]

        for phase_value in valid_phases:
            state = WorkflowState(
                workflow_id="test-123",
                workflow_name="Test Workflow",
                workflow_type="feature",
                phase=phase_value,
            )
            assert state.phase == phase_value

    def test_phase_invalid_value_raises_error(self):
        """Test that invalid phase values raise ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            WorkflowState(
                workflow_id="test-123",
                workflow_name="Test Workflow",
                workflow_type="feature",
                phase="invalid_phase",
            )

    def test_phase_persistence(self):
        """Test that phase is saved and loaded correctly."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create state with phase set to 'implementing'
            state = WorkflowState(
                workflow_id="test-123",
                workflow_name="Test Workflow",
                workflow_type="feature",
                phase="implementing",
            )

            # Save
            state.save(project_root)

            # Load
            loaded_state = WorkflowState.load("test-123", project_root)

            # Verify phase is preserved
            assert loaded_state.phase == "implementing"

    def test_phase_backward_compatibility(self):
        """Test that old state files without phase load correctly with default."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create old-style state (without phase)
            old_state_data = {
                "workflow_id": "old-123",
                "workflow_name": "Old Workflow",
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
                "beads_task_id": None,
                "beads_task_title": None,
            }

            # Write old state
            state_dir = project_root / "agents" / "old-123"
            state_dir.mkdir(parents=True, exist_ok=True)
            state_file = state_dir / "state.json"
            with open(state_file, "w") as f:
                json.dump(old_state_data, f)

            # Should load successfully with phase defaulting to 'planning'
            loaded_state = WorkflowState.load("old-123", project_root)

            assert loaded_state.workflow_id == "old-123"
            assert loaded_state.phase == "planning"


class TestBackwardCompatibilityComprehensive:
    """Comprehensive tests for backward compatibility with all new Beads fields."""

    def test_load_old_state_without_any_beads_fields(self):
        """Test loading old state JSON that lacks beads_task_id, beads_task_title, and phase.

        This simulates loading a state file created before the Beads integration
        was implemented. All three new fields should default correctly.
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create old-style state without ANY Beads fields
            # This represents a state file from before the Beads integration
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


class TestGetSummaryIncludesBeadsFields:
    """Tests that get_summary() includes beads_task_id, beads_task_title, and phase fields."""

    def test_get_summary_includes_all_beads_fields(self):
        """Test that get_summary() includes all Beads fields together."""
        state = WorkflowState(
            workflow_id="test-123",
            workflow_name="Test Workflow",
            workflow_type="feature",
            beads_task_id="jean_claude-2sz.2",
            beads_task_title="Link WorkflowState to Beads Tasks",
            phase="verifying",
        )

        state.add_feature("f1", "First feature")
        state.add_feature("f2", "Second feature")
        state.features[0].status = "completed"
        state.iteration_count = 5
        state.total_cost_usd = 2.50

        summary = state.get_summary()

        # Verify all Beads fields are present
        assert "beads_task_id" in summary
        assert "beads_task_title" in summary
        assert "phase" in summary

        # Verify their values
        assert summary["beads_task_id"] == "jean_claude-2sz.2"
        assert summary["beads_task_title"] == "Link WorkflowState to Beads Tasks"
        assert summary["phase"] == "verifying"

        # Verify other fields still work
        assert summary["workflow_id"] == "test-123"
        assert summary["total_features"] == 2
        assert summary["completed_features"] == 1
        assert summary["iteration_count"] == 5
        assert summary["total_cost_usd"] == 2.50


class TestBeadsFieldsSaveLoadRoundtrip:
    """Tests for save/load roundtrip with Beads fields."""

    def test_save_load_roundtrip_with_all_beads_fields(self):
        """Test that beads_task_id, beads_task_title, and phase are preserved in save/load roundtrip.

        Create a state with all three Beads fields set to non-default values,
        save to disk, load from disk, and verify all values are preserved correctly.
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create state with all Beads fields set to non-default values
            original_state = WorkflowState(
                workflow_id="roundtrip-test-123",
                workflow_name="Roundtrip Test Workflow",
                workflow_type="feature",
                beads_task_id="jean_claude-2sz.2",
                beads_task_title="Link WorkflowState to Beads Tasks",
                phase="implementing",
            )

            # Add some features to make it more realistic
            original_state.add_feature("feature-1", "First feature", test_file="tests/test_f1.py")
            original_state.add_feature("feature-2", "Second feature")
            original_state.start_feature()
            original_state.iteration_count = 5
            original_state.total_cost_usd = 3.50

            # Save to disk
            original_state.save(project_root)

            # Load from disk
            loaded_state = WorkflowState.load("roundtrip-test-123", project_root)

            # Verify all Beads fields are preserved exactly
            assert loaded_state.beads_task_id == "jean_claude-2sz.2"
            assert loaded_state.beads_task_title == "Link WorkflowState to Beads Tasks"
            assert loaded_state.phase == "implementing"

            # Verify other fields are also preserved
            assert loaded_state.workflow_id == "roundtrip-test-123"
            assert loaded_state.workflow_name == "Roundtrip Test Workflow"
            assert loaded_state.workflow_type == "feature"
            assert len(loaded_state.features) == 2
            assert loaded_state.features[0].name == "feature-1"
            assert loaded_state.iteration_count == 5
            assert loaded_state.total_cost_usd == 3.50

