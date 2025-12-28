# ABOUTME: Tests for the status CLI command
# ABOUTME: Consolidated tests for workflow status display and JSON output

"""Tests for jc status command.

Consolidated from 21 separate tests to focused tests covering
essential behaviors without per-status-icon redundancy.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner

from jean_claude.cli.commands.status import status
from jean_claude.core.state import WorkflowState


class TestStatusCommand:
    """Tests for the status command - consolidated from 16 tests to 8."""

    def test_status_no_workflows_and_specific_workflow(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test status with no workflows and with a specific workflow ID."""
        # No workflows
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(status, [])
        assert result.exit_code == 0
        assert "No workflows found" in result.output

        # Specific workflow
        state = WorkflowState(
            workflow_id="test-workflow-123",
            workflow_name="Test Workflow",
            workflow_type="feature",
            beads_task_title="Add feature X",
            phase="implementing",
        )
        state.add_feature("Feature A", "Description A")
        state.add_feature("Feature B", "Description B")
        state.save(tmp_path)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(status, ["test-workflow-123"])

        assert result.exit_code == 0
        assert "test-workflow-123" in result.output
        assert "Add feature X" in result.output
        assert "Feature A" in result.output

    def test_status_most_recent_workflow(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test status shows most recent workflow by default."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Older workflow
        old_state = WorkflowState(
            workflow_id="old-workflow",
            workflow_name="Old Workflow",
            workflow_type="feature",
            updated_at=datetime.now() - timedelta(hours=2),
        )
        old_state.save(tmp_path)

        # Newer workflow
        new_state = WorkflowState(
            workflow_id="new-workflow",
            workflow_name="New Workflow",
            workflow_type="chore",
            updated_at=datetime.now(),
        )
        new_state.save(tmp_path)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(status, [])

        assert result.exit_code == 0
        assert "new-workflow" in result.output
        assert "old-workflow" not in result.output

    def test_status_feature_progress_and_icons(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test status shows feature progress with correct icons."""
        state = WorkflowState(
            workflow_id="progress-test",
            workflow_name="Progress Test",
            workflow_type="feature",
        )
        state.add_feature("Completed Feature", "Done")
        state.add_feature("In Progress Feature", "Working")
        state.add_feature("Pending Feature", "Not started")
        state.add_feature("Failed Feature", "Error")

        state.features[0].status = "completed"
        state.features[1].status = "in_progress"
        state.features[2].status = "not_started"
        state.features[3].status = "failed"
        state.save(tmp_path)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(status, ["progress-test"])

        assert result.exit_code == 0
        assert "✓" in result.output  # completed
        assert "→" in result.output  # in_progress
        assert "○" in result.output  # not_started
        assert "✗" in result.output  # failed
        assert "1/4" in result.output  # 1 of 4 completed

    def test_status_json_output(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test status --json outputs valid JSON for single and multiple workflows."""
        # Single workflow
        state = WorkflowState(
            workflow_id="json-test",
            workflow_name="JSON Test",
            workflow_type="feature",
            beads_task_id="task-123",
            beads_task_title="Test Task",
            phase="implementing",
            total_cost_usd=0.42,
            total_duration_ms=123456,
        )
        state.add_feature("Feature A", "Description A")
        state.features[0].status = "completed"
        state.save(tmp_path)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(status, ["json-test", "--json"])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["workflow_id"] == "json-test"
        assert output["phase"] == "implementing"
        assert output["completed"] == 1
        assert output["progress_percentage"] == 100.0

        # Multiple workflows with --all --json
        state2 = WorkflowState(
            workflow_id="wf-2",
            workflow_name="Second",
            workflow_type="chore",
        )
        state2.save(tmp_path)

        result = cli_runner.invoke(status, ["--all", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert isinstance(output, list)
        assert len(output) == 2

    def test_status_all_flag(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test status --all shows all workflows."""
        workflows = [
            ("workflow-1", "Workflow One", "feature"),
            ("workflow-2", "Workflow Two", "chore"),
            ("workflow-3", "Workflow Three", "bug"),
        ]

        for wf_id, wf_name, wf_type in workflows:
            state = WorkflowState(
                workflow_id=wf_id,
                workflow_name=wf_name,
                workflow_type=wf_type,
            )
            state.save(tmp_path)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(status, ["--all"])

        assert result.exit_code == 0
        assert "workflow-1" in result.output
        assert "workflow-2" in result.output
        assert "workflow-3" in result.output

    def test_status_verbose_flag(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test status --verbose shows feature descriptions."""
        state = WorkflowState(
            workflow_id="verbose-test",
            workflow_name="Verbose Test",
            workflow_type="feature",
        )
        state.add_feature("Feature A", "Detailed description of feature A")
        state.save(tmp_path)

        monkeypatch.chdir(tmp_path)

        # Without verbose
        result = cli_runner.invoke(status, ["verbose-test"])
        assert "Detailed description" not in result.output

        # With verbose
        result = cli_runner.invoke(status, ["verbose-test", "--verbose"])
        assert result.exit_code == 0
        assert "Detailed description of feature A" in result.output

    def test_status_error_and_edge_cases(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test status error handling and edge cases."""
        # Nonexistent workflow
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(status, ["nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.output

        # No timing data
        state = WorkflowState(
            workflow_id="no-timing",
            workflow_name="No Timing",
            workflow_type="feature",
            total_duration_ms=0,
        )
        state.save(tmp_path)
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(status, ["no-timing"])
        assert result.exit_code == 0
        assert "No timing data" in result.output

    def test_status_handles_missing_and_malformed_events(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test status gracefully handles missing and malformed events."""
        # Missing events file
        state1 = WorkflowState(
            workflow_id="no-events",
            workflow_name="No Events",
            workflow_type="feature",
        )
        state1.add_feature("F1", "Feature 1")
        state1.features[0].status = "completed"
        state1.save(tmp_path)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(status, ["no-events"])
        assert result.exit_code == 0

        # Malformed events file
        state2 = WorkflowState(
            workflow_id="bad-events",
            workflow_name="Bad Events",
            workflow_type="feature",
        )
        state2.add_feature("F1", "Feature 1")
        state2.save(tmp_path)

        events_dir = tmp_path / "agents" / "bad-events"
        events_dir.mkdir(parents=True, exist_ok=True)
        events_file = events_dir / "events.jsonl"
        with open(events_file, 'w') as f:
            f.write("not valid json\n")
            f.write('{"malformed": true\n')

        result = cli_runner.invoke(status, ["bad-events"])
        assert result.exit_code == 0


class TestStatusHelperFunctions:
    """Tests for status helper functions - consolidated from 5 tests to 2."""

    def test_find_most_recent_and_get_all_workflows(self, tmp_path: Path):
        """Test finding most recent workflow and getting all workflows."""
        from jean_claude.cli.commands.status import find_most_recent_workflow, get_all_workflows

        # No agents dir
        assert find_most_recent_workflow(tmp_path) is None
        assert get_all_workflows(tmp_path) == []

        # Create agents dir but no workflows
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        assert find_most_recent_workflow(tmp_path) is None
        assert get_all_workflows(tmp_path) == []

        # Create workflows with different timestamps
        old_state = WorkflowState(
            workflow_id="old",
            workflow_name="Old",
            workflow_type="feature",
            updated_at=datetime.now() - timedelta(hours=1),
        )
        old_state.save(tmp_path)

        new_state = WorkflowState(
            workflow_id="new",
            workflow_name="New",
            workflow_type="feature",
            updated_at=datetime.now(),
        )
        new_state.save(tmp_path)

        # Most recent
        assert find_most_recent_workflow(tmp_path) == "new"

        # All workflows sorted by most recent
        all_wf = get_all_workflows(tmp_path)
        assert len(all_wf) == 2
        assert all_wf[0].workflow_id == "new"
        assert all_wf[1].workflow_id == "old"

    def test_format_duration_and_status_icon(self):
        """Test duration formatting and status icon mapping."""
        from jean_claude.cli.commands.status import format_duration, get_status_icon

        # Duration formatting
        assert format_duration(30000) == "30s"
        assert format_duration(60000) == "1m 00s"
        assert format_duration(90000) == "1m 30s"
        assert format_duration(134000) == "2m 14s"
        assert format_duration(3600000) == "60m 00s"

        # Status icons
        assert get_status_icon("completed") == "✓"
        assert get_status_icon("in_progress") == "→"
        assert get_status_icon("not_started") == "○"
        assert get_status_icon("failed") == "✗"
        assert get_status_icon("unknown") == "○"  # default

    def test_get_feature_durations(self, tmp_path: Path):
        """Test extracting feature durations from events."""
        from jean_claude.cli.commands.status import get_feature_durations

        # No events file
        assert get_feature_durations(tmp_path, "no-events") == {}

        # Create events file
        events_dir = tmp_path / "agents" / "test-workflow"
        events_dir.mkdir(parents=True)
        events_file = events_dir / "events.jsonl"

        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=45)

        events = [
            {
                "id": "1",
                "timestamp": start_time.isoformat(),
                "workflow_id": "test-workflow",
                "event_type": "feature.started",
                "data": {"feature_name": "Test Feature"}
            },
            {
                "id": "2",
                "timestamp": end_time.isoformat(),
                "workflow_id": "test-workflow",
                "event_type": "feature.completed",
                "data": {"feature_name": "Test Feature"}
            },
        ]

        with open(events_file, 'w') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')

        result = get_feature_durations(tmp_path, "test-workflow")
        assert "Test Feature" in result
        assert result["Test Feature"] == 45000  # 45 seconds in ms
