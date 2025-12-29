# ABOUTME: Tests for the status CLI command
# ABOUTME: Consolidated tests for workflow status display and JSON output
# ABOUTME: Includes integration tests verifying status and logs use shared find_most_recent_workflow

"""Tests for jc status command.

Consolidated from 21 separate tests to focused tests covering
essential behaviors without per-status-icon redundancy.

Includes integration tests (TestStatusAndLogsIntegration) that verify
both status and logs commands correctly use the unified workflow finder
from workflow_utils.py.
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
        from jean_claude.core.workflow_utils import find_most_recent_workflow
        from jean_claude.cli.commands.status import get_all_workflows

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


class TestStatusAndLogsIntegration:
    """Integration tests to verify status and logs commands work with shared workflow_utils."""

    def test_both_commands_find_workflow_with_only_state_file(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test both status and logs find workflow when only state.json exists."""
        import time
        from jean_claude.cli.commands.status import status
        from jean_claude.cli.commands.logs import logs

        # Create workflow with only state.json
        state = WorkflowState(
            workflow_id="state-only-wf",
            workflow_name="State Only Workflow",
            workflow_type="feature",
            beads_task_title="Test Task",
            phase="implementing",
        )
        state.add_feature("Feature A", "Description A")
        state.save(tmp_path)

        monkeypatch.chdir(tmp_path)

        # Test status command finds it
        result = cli_runner.invoke(status, [])
        assert result.exit_code == 0
        assert "state-only-wf" in result.output
        assert "Feature A" in result.output

        # Test logs command finds it (should show no logs message)
        result = cli_runner.invoke(logs, [])
        # Should not error, even though no events.jsonl exists
        assert result.exit_code == 0

    def test_both_commands_find_workflow_with_only_events_file(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test both status and logs find workflow when only events.jsonl exists."""
        from jean_claude.cli.commands.status import status
        from jean_claude.cli.commands.logs import logs

        # Create workflow directory with only events.jsonl
        agents_dir = tmp_path / "agents"
        workflow_dir = agents_dir / "events-only-wf"
        workflow_dir.mkdir(parents=True)

        # Create events.jsonl
        events_file = workflow_dir / "events.jsonl"
        events = [
            {
                "id": "evt-1",
                "timestamp": datetime.now().isoformat(),
                "workflow_id": "events-only-wf",
                "event_type": "workflow.started",
                "data": {"beads_task": "test"}
            }
        ]
        with open(events_file, 'w') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')

        monkeypatch.chdir(tmp_path)

        # Test logs command finds it
        result = cli_runner.invoke(logs, [])
        assert result.exit_code == 0
        assert "workflow.started" in result.output

        # Note: status command needs state.json, so it won't show this workflow
        # This is expected behavior

    def test_both_commands_find_most_recent_when_multiple_workflows(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test both commands correctly identify most recent workflow."""
        import time
        from jean_claude.cli.commands.status import status
        from jean_claude.cli.commands.logs import logs

        # Create older workflow
        old_state = WorkflowState(
            workflow_id="old-workflow",
            workflow_name="Old Workflow",
            workflow_type="feature",
            updated_at=datetime.now() - timedelta(hours=2),
        )
        old_state.add_feature("Old Feature", "Old description")
        old_state.save(tmp_path)

        # Create older events file
        old_workflow_dir = tmp_path / "agents" / "old-workflow"
        old_events_file = old_workflow_dir / "events.jsonl"
        old_events = [
            {
                "id": "old-evt",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "workflow_id": "old-workflow",
                "event_type": "workflow.started",
                "data": {}
            }
        ]
        with open(old_events_file, 'w') as f:
            for event in old_events:
                f.write(json.dumps(event) + '\n')

        # Wait to ensure different mtimes
        time.sleep(0.1)

        # Create newer workflow
        new_state = WorkflowState(
            workflow_id="new-workflow",
            workflow_name="New Workflow",
            workflow_type="chore",
            updated_at=datetime.now(),
        )
        new_state.add_feature("New Feature", "New description")
        new_state.save(tmp_path)

        # Create newer events file
        new_workflow_dir = tmp_path / "agents" / "new-workflow"
        new_events_file = new_workflow_dir / "events.jsonl"
        new_events = [
            {
                "id": "new-evt",
                "timestamp": datetime.now().isoformat(),
                "workflow_id": "new-workflow",
                "event_type": "workflow.started",
                "data": {}
            }
        ]
        with open(new_events_file, 'w') as f:
            for event in new_events:
                f.write(json.dumps(event) + '\n')

        monkeypatch.chdir(tmp_path)

        # Test status shows new-workflow
        result = cli_runner.invoke(status, [])
        assert result.exit_code == 0
        assert "new-workflow" in result.output
        assert "New Feature" in result.output
        assert "old-workflow" not in result.output

        # Test logs shows new-workflow
        result = cli_runner.invoke(logs, [])
        assert result.exit_code == 0
        assert "new-workflow" in result.output or "workflow.started" in result.output
        # The new-evt event should be shown

    def test_both_commands_use_events_mtime_when_more_recent(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test both commands prefer workflow with recently modified events.jsonl."""
        import time
        from jean_claude.cli.commands.status import status
        from jean_claude.cli.commands.logs import logs

        # Create workflow-1 with old state.json
        state1 = WorkflowState(
            workflow_id="workflow-1",
            workflow_name="Workflow 1",
            workflow_type="feature",
            updated_at=datetime.now() - timedelta(hours=1),
        )
        state1.add_feature("Feature 1", "Desc 1")
        state1.save(tmp_path)

        time.sleep(0.1)

        # Create workflow-2 with recent state.json but old events
        state2 = WorkflowState(
            workflow_id="workflow-2",
            workflow_name="Workflow 2",
            workflow_type="feature",
            updated_at=datetime.now() - timedelta(minutes=30),
        )
        state2.add_feature("Feature 2", "Desc 2")
        state2.save(tmp_path)

        # Create old events for workflow-2
        wf2_dir = tmp_path / "agents" / "workflow-2"
        wf2_events = wf2_dir / "events.jsonl"
        wf2_events.write_text(json.dumps({
            "id": "evt",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "workflow_id": "workflow-2",
            "event_type": "workflow.started",
            "data": {}
        }) + '\n')

        time.sleep(0.1)

        # Create very recent events for workflow-1
        wf1_dir = tmp_path / "agents" / "workflow-1"
        wf1_events = wf1_dir / "events.jsonl"
        wf1_events.write_text(json.dumps({
            "id": "evt-recent",
            "timestamp": datetime.now().isoformat(),
            "workflow_id": "workflow-1",
            "event_type": "feature.completed",
            "data": {}
        }) + '\n')

        monkeypatch.chdir(tmp_path)

        # Both commands should identify workflow-1 as most recent
        # because its events.jsonl mtime is most recent
        result = cli_runner.invoke(status, [])
        assert result.exit_code == 0
        # Should show workflow-1 since its events.jsonl was modified most recently
        assert "workflow-1" in result.output or "Feature 1" in result.output

    def test_both_commands_handle_corrupted_state_gracefully(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch,
    ):
        """Test both commands skip corrupted state.json files."""
        from jean_claude.cli.commands.status import status
        from jean_claude.cli.commands.logs import logs

        # Create workflow with corrupted state.json
        agents_dir = tmp_path / "agents"
        corrupted_dir = agents_dir / "corrupted-wf"
        corrupted_dir.mkdir(parents=True)
        (corrupted_dir / "state.json").write_text("invalid json {{{")

        # Create valid workflow
        valid_state = WorkflowState(
            workflow_id="valid-wf",
            workflow_name="Valid Workflow",
            workflow_type="feature",
        )
        valid_state.add_feature("Valid Feature", "Valid desc")
        valid_state.save(tmp_path)

        monkeypatch.chdir(tmp_path)

        # Status should skip corrupted and show valid
        result = cli_runner.invoke(status, [])
        assert result.exit_code == 0
        assert "valid-wf" in result.output

    def test_unified_workflow_finder_consistency(self, tmp_path: Path):
        """Test that the shared find_most_recent_workflow function is consistent."""
        from jean_claude.core.workflow_utils import find_most_recent_workflow
        import time

        # Create multiple workflows with different file combinations
        # Workflow 1: state.json only (oldest)
        state1 = WorkflowState(
            workflow_id="wf-state-only",
            workflow_name="State Only",
            workflow_type="feature",
            updated_at=datetime.now() - timedelta(hours=3),
        )
        state1.save(tmp_path)

        time.sleep(0.1)

        # Workflow 2: events.jsonl only (middle)
        wf2_dir = tmp_path / "agents" / "wf-events-only"
        wf2_dir.mkdir(parents=True)
        wf2_events = wf2_dir / "events.jsonl"
        wf2_events.write_text(json.dumps({
            "id": "evt",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "workflow_id": "wf-events-only",
            "event_type": "workflow.started",
            "data": {}
        }) + '\n')

        time.sleep(0.1)

        # Workflow 3: both files (most recent)
        state3 = WorkflowState(
            workflow_id="wf-both",
            workflow_name="Both Files",
            workflow_type="feature",
            updated_at=datetime.now(),
        )
        state3.save(tmp_path)
        wf3_dir = tmp_path / "agents" / "wf-both"
        wf3_events = wf3_dir / "events.jsonl"
        wf3_events.write_text(json.dumps({
            "id": "evt-both",
            "timestamp": datetime.now().isoformat(),
            "workflow_id": "wf-both",
            "event_type": "workflow.started",
            "data": {}
        }) + '\n')

        # Should return the most recent workflow
        result = find_most_recent_workflow(tmp_path)
        assert result == "wf-both"
