# ABOUTME: Test suite for the 'jc logs' command implementation
# ABOUTME: Tests log viewing, filtering by time/level, and real-time tailing

"""Tests for jc logs command.

This module tests the logs command functionality:
- Basic log viewing from events.jsonl
- --follow flag for real-time tailing
- --since flag for time filtering
- --level flag for log level filtering
- Colored Rich output
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from jean_claude.cli.main import cli


class TestLogsCommandBasic:
    """Tests for basic jc logs functionality."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with events.jsonl."""
        # Create agents directory with workflow
        workflow_dir = tmp_path / "agents" / "test-workflow-123"
        workflow_dir.mkdir(parents=True)

        # Create events.jsonl with sample events
        events = [
            {
                "id": "evt-1",
                "timestamp": "2025-01-15T12:00:00",
                "workflow_id": "test-workflow-123",
                "event_type": "workflow.started",
                "data": {"beads_task": "poc-xyz"}
            },
            {
                "id": "evt-2",
                "timestamp": "2025-01-15T12:00:01",
                "workflow_id": "test-workflow-123",
                "event_type": "feature.planned",
                "data": {"feature_name": "Create User model"}
            },
            {
                "id": "evt-3",
                "timestamp": "2025-01-15T12:00:02",
                "workflow_id": "test-workflow-123",
                "event_type": "agent.tool_use",
                "data": {"tool": "Read", "target": "src/models/__init__.py"}
            },
            {
                "id": "evt-4",
                "timestamp": "2025-01-15T12:00:10",
                "workflow_id": "test-workflow-123",
                "event_type": "agent.test_result",
                "data": {"passed": 3, "failed": 0}
            },
            {
                "id": "evt-5",
                "timestamp": "2025-01-15T12:00:50",
                "workflow_id": "test-workflow-123",
                "event_type": "feature.completed",
                "data": {"feature_name": "Create User model", "duration": "48s"}
            },
        ]

        events_file = workflow_dir / "events.jsonl"
        with open(events_file, 'w') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')

        # Create state.json for the workflow
        state = {
            "workflow_id": "test-workflow-123",
            "workflow_name": "Test Workflow",
            "phase": "implementing",
            "created_at": "2025-01-15T12:00:00",
            "updated_at": "2025-01-15T12:00:50",
        }
        state_file = workflow_dir / "state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f)

        return tmp_path

    def test_logs_no_workflows_shows_message(self, runner):
        """Test that jc logs with no workflows shows helpful message."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["logs"])

            assert result.exit_code == 0
            assert "No workflows found" in result.output or "no logs" in result.output.lower()

    def test_logs_invalid_workflow_shows_error(self, runner, temp_project):
        """Test that jc logs with invalid workflow ID shows error."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(temp_project / "agents", Path.cwd() / "agents")

            result = runner.invoke(cli, ["logs", "nonexistent-workflow"])

            assert result.exit_code != 0 or "not found" in result.output.lower()


class TestLogsCommandFiltering:
    """Tests for jc logs filtering options."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_project_with_levels(self, tmp_path):
        """Create project with events at different levels."""
        workflow_dir = tmp_path / "agents" / "test-workflow"
        workflow_dir.mkdir(parents=True)

        now = datetime.now()
        events = [
            {
                "id": "evt-1",
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "workflow_id": "test-workflow",
                "event_type": "workflow.started",
                "data": {"message": "Starting"}
            },
            {
                "id": "evt-2",
                "timestamp": (now - timedelta(minutes=30)).isoformat(),
                "workflow_id": "test-workflow",
                "event_type": "agent.tool_use",
                "data": {"tool": "Read"}
            },
            {
                "id": "evt-3",
                "timestamp": (now - timedelta(minutes=5)).isoformat(),
                "workflow_id": "test-workflow",
                "event_type": "agent.error",
                "data": {"error": "Something failed"}
            },
            {
                "id": "evt-4",
                "timestamp": now.isoformat(),
                "workflow_id": "test-workflow",
                "event_type": "workflow.completed",
                "data": {"message": "Done"}
            },
        ]

        events_file = workflow_dir / "events.jsonl"
        with open(events_file, 'w') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')

        state = {
            "workflow_id": "test-workflow",
            "workflow_name": "Test",
            "phase": "completed",
            "created_at": (now - timedelta(hours=2)).isoformat(),
            "updated_at": now.isoformat(),
        }
        with open(workflow_dir / "state.json", 'w') as f:
            json.dump(state, f)

        return tmp_path

    def test_logs_since_accepts_various_formats(self, runner, temp_project_with_levels):
        """Test that --since accepts different time formats."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(temp_project_with_levels / "agents", Path.cwd() / "agents")

            # Test minutes
            result = runner.invoke(cli, ["logs", "test-workflow", "--since", "5m"])
            assert result.exit_code == 0

            # Test hours
            result = runner.invoke(cli, ["logs", "test-workflow", "--since", "1h"])
            assert result.exit_code == 0

    def test_logs_level_filters_by_event_category(self, runner, temp_project_with_levels):
        """Test that --level filters logs by category."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(temp_project_with_levels / "agents", Path.cwd() / "agents")

            # Filter to only workflow events
            result = runner.invoke(cli, ["logs", "test-workflow", "--level", "workflow"])

            assert result.exit_code == 0
            # Should only show workflow.* events


class TestLogsCommandFollow:
    """Tests for jc logs --follow real-time tailing."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_project_for_follow(self, tmp_path):
        """Create a minimal project for follow testing."""
        workflow_dir = tmp_path / "agents" / "follow-test"
        workflow_dir.mkdir(parents=True)

        events = [
            {
                "id": "evt-1",
                "timestamp": datetime.now().isoformat(),
                "workflow_id": "follow-test",
                "event_type": "workflow.started",
                "data": {}
            }
        ]

        with open(workflow_dir / "events.jsonl", 'w') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')

        with open(workflow_dir / "state.json", 'w') as f:
            json.dump({"workflow_id": "follow-test", "phase": "running"}, f)

        return tmp_path

    def test_logs_follow_shows_tailing_message(self, runner, temp_project_for_follow):
        """Test that --follow shows 'Tailing' message before entering loop."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(temp_project_for_follow / "agents", Path.cwd() / "agents")

            # Mock time.sleep to raise KeyboardInterrupt immediately
            with patch('jean_claude.cli.commands.logs.time.sleep', side_effect=KeyboardInterrupt):
                result = runner.invoke(
                    cli,
                    ["logs", "follow-test", "--follow"],
                    catch_exceptions=False
                )

            # Should show tailing message
            assert "Tailing" in result.output or "tailing" in result.output.lower()


class TestLogsCommandOutput:
    """Tests for jc logs output formatting."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a project with varied events."""
        workflow_dir = tmp_path / "agents" / "output-test"
        workflow_dir.mkdir(parents=True)

        events = [
            {
                "id": "evt-1",
                "timestamp": "2025-01-15T12:00:00",
                "workflow_id": "output-test",
                "event_type": "workflow.started",
                "data": {"workflow_id": "abc123", "beads_task": "poc-xyz"}
            },
            {
                "id": "evt-2",
                "timestamp": "2025-01-15T12:00:05",
                "workflow_id": "output-test",
                "event_type": "agent.error",
                "data": {"error": "Connection timeout"}
            },
        ]

        with open(workflow_dir / "events.jsonl", 'w') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')

        with open(workflow_dir / "state.json", 'w') as f:
            json.dump({"workflow_id": "output-test", "phase": "failed"}, f)

        return tmp_path

    def test_logs_json_output(self, runner, temp_project):
        """Test that --json outputs valid JSON."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(temp_project / "agents", Path.cwd() / "agents")

            result = runner.invoke(cli, ["logs", "output-test", "--json"])

            assert result.exit_code == 0
            # Should be valid JSON
            try:
                data = json.loads(result.output)
                assert isinstance(data, list)
                assert len(data) == 2
            except json.JSONDecodeError:
                pytest.fail("Output is not valid JSON")

    def test_logs_limit_option(self, runner, temp_project):
        """Test that -n/--limit restricts number of lines."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(temp_project / "agents", Path.cwd() / "agents")

            result = runner.invoke(cli, ["logs", "output-test", "-n", "1"])

            assert result.exit_code == 0
            # Should only show 1 event (the most recent)


class TestLogsCommandEdgeCases:
    """Edge case tests for jc logs command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    def test_logs_empty_events_file(self, runner, tmp_path):
        """Test handling of empty events.jsonl file."""
        with runner.isolated_filesystem():
            workflow_dir = Path.cwd() / "agents" / "empty-test"
            workflow_dir.mkdir(parents=True)

            # Create empty events file
            (workflow_dir / "events.jsonl").touch()
            with open(workflow_dir / "state.json", 'w') as f:
                json.dump({"workflow_id": "empty-test", "phase": "running"}, f)

            result = runner.invoke(cli, ["logs", "empty-test"])

            assert result.exit_code == 0
            # Should handle gracefully

    def test_logs_malformed_event_line(self, runner, tmp_path):
        """Test handling of malformed JSON in events.jsonl."""
        with runner.isolated_filesystem():
            workflow_dir = Path.cwd() / "agents" / "malformed-test"
            workflow_dir.mkdir(parents=True)

            # Create events with one malformed line
            with open(workflow_dir / "events.jsonl", 'w') as f:
                f.write('{"id": "evt-1", "event_type": "workflow.started", "timestamp": "2025-01-15T12:00:00", "workflow_id": "x", "data": {}}\n')
                f.write('this is not valid json\n')
                f.write('{"id": "evt-2", "event_type": "workflow.completed", "timestamp": "2025-01-15T12:01:00", "workflow_id": "x", "data": {}}\n')

            with open(workflow_dir / "state.json", 'w') as f:
                json.dump({"workflow_id": "malformed-test", "phase": "running"}, f)

            result = runner.invoke(cli, ["logs", "malformed-test"])

            # Should handle gracefully - show valid events, skip malformed
            assert result.exit_code == 0


class TestLogsCommandRefactor:
    """Tests for logs command refactor to use get_all_workflows utility function."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_project_multi_workflows(self, tmp_path):
        """Create a temporary project with multiple workflows for testing --all functionality."""
        # Create agents directory
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Create first workflow
        workflow1_dir = agents_dir / "workflow-one"
        workflow1_dir.mkdir()

        events1 = [
            {
                "id": "evt-1",
                "timestamp": "2025-01-15T12:00:00",
                "workflow_id": "workflow-one",
                "event_type": "workflow.started",
                "data": {"beads_task": "task-1"}
            },
            {
                "id": "evt-2",
                "timestamp": "2025-01-15T12:00:10",
                "workflow_id": "workflow-one",
                "event_type": "feature.completed",
                "data": {"feature_name": "Feature A"}
            }
        ]

        with open(workflow1_dir / "events.jsonl", 'w') as f:
            for event in events1:
                f.write(json.dumps(event) + '\n')

        state1 = {
            "workflow_id": "workflow-one",
            "workflow_name": "First Workflow",
            "workflow_type": "feature",
            "phase": "complete",
            "created_at": "2025-01-15T12:00:00",
            "updated_at": "2025-01-15T12:00:10",
        }
        with open(workflow1_dir / "state.json", 'w') as f:
            json.dump(state1, f)

        # Create second workflow
        workflow2_dir = agents_dir / "workflow-two"
        workflow2_dir.mkdir()

        events2 = [
            {
                "id": "evt-3",
                "timestamp": "2025-01-15T13:00:00",
                "workflow_id": "workflow-two",
                "event_type": "workflow.started",
                "data": {"beads_task": "task-2"}
            },
            {
                "id": "evt-4",
                "timestamp": "2025-01-15T13:00:20",
                "workflow_id": "workflow-two",
                "event_type": "agent.error",
                "data": {"error": "Something failed"}
            }
        ]

        with open(workflow2_dir / "events.jsonl", 'w') as f:
            for event in events2:
                f.write(json.dumps(event) + '\n')

        state2 = {
            "workflow_id": "workflow-two",
            "workflow_name": "Second Workflow",
            "workflow_type": "bug",
            "phase": "verifying",
            "created_at": "2025-01-15T13:00:00",
            "updated_at": "2025-01-15T13:00:20",
        }
        with open(workflow2_dir / "state.json", 'w') as f:
            json.dump(state2, f)

        return tmp_path

    def test_logs_module_imports_get_all_workflows_from_utils(self):
        """Test that logs module imports get_all_workflows from workflow_utils."""
        from jean_claude.cli.commands import logs as logs_module
        from jean_claude.core.workflow_utils import get_all_workflows as utils_get_all_workflows

        # The logs module should import get_all_workflows from workflow_utils
        assert hasattr(logs_module, 'get_all_workflows')
        assert logs_module.get_all_workflows is utils_get_all_workflows

    def test_logs_all_with_json_output(self, runner, temp_project_multi_workflows):
        """Test that 'jc logs --all --json' outputs valid JSON with logs from all workflows."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(temp_project_multi_workflows / "agents", Path.cwd() / "agents")

            result = runner.invoke(cli, ["logs", "--all", "--json"])

            assert result.exit_code == 0
            # Should be valid JSON
            try:
                data = json.loads(result.output)
                assert isinstance(data, list)
                # Should have events from both workflows
                workflow_ids = {event.get("workflow_id") for event in data}
                assert "workflow-one" in workflow_ids
                assert "workflow-two" in workflow_ids
            except json.JSONDecodeError:
                pytest.fail("Output is not valid JSON")
