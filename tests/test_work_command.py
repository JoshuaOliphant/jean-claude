# ABOUTME: Test suite for work CLI command
# ABOUTME: Tests work command structure, flags, workflow integration, and lifecycle

"""Tests for work CLI command.

This test file uses shared fixtures from conftest.py instead of defining
fixtures in each class. All tests use:
- mock_beads_task: Standard BeadsTask for testing
- work_command_mocks: Combined mocks for all work command dependencies
- isolated_cli_runner: CliRunner with isolated filesystem
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from jean_claude.cli.commands.work import work
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus
from jean_claude.core.state import WorkflowState


class TestWorkCommandFlags:
    """Tests for work command business logic."""

    @pytest.mark.parametrize("model", ["sonnet", "opus", "haiku"])
    def test_model_option_accepts_valid_models(self, model, work_command_mocks, isolated_cli_runner):
        """Test that --model option accepts all valid model choices."""
        result = isolated_cli_runner.invoke(work, ["test-task.1", "--model", model])
        # Should not show "Invalid value" error
        assert "Invalid value" not in result.output

    def test_dry_run_skips_workflow_execution(self, cli_runner, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that --dry-run mode does not call run_two_agent_workflow."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('jean_claude.cli.commands.work.anyio.run') as mock_anyio_run:
                        result = isolated_cli_runner.invoke(work, ["test-task.1", "--dry-run"])
                        mock_anyio_run.assert_not_called()


class TestWorkFetchAndSpec:
    """Tests for work command integration with fetch_beads_task and spec generation."""

    def test_work_fetches_task_and_generates_spec(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command fetches task and generates spec file."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task) as mock_fetch:
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test Spec") as mock_generate:
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    result = isolated_cli_runner.invoke(work, ["test-task.1"])

                    # Should call fetch_beads_task with the beads_id
                    mock_fetch.assert_called_once_with("test-task.1")
                    # Should call generate_spec_from_beads with the fetched task
                    mock_generate.assert_called_once_with(mock_beads_task)
                    # Should create spec file
                    spec_path = Path("specs/beads-test-task.1.md")
                    assert spec_path.exists()

    def test_work_handles_fetch_error_gracefully(self, cli_runner, isolated_cli_runner):
        """Test that work command handles fetch_beads_task errors gracefully."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', side_effect=RuntimeError("Failed to fetch")):
            result = isolated_cli_runner.invoke(work, ["nonexistent-task.1"])
            assert result.exit_code != 0 or "error" in result.output.lower() or "failed" in result.output.lower()


class TestWorkflowStateSetup:
    """Tests for WorkflowState initialization in work command."""

    def test_work_creates_and_saves_workflow_state(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command creates and saves WorkflowState with beads fields."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('jean_claude.cli.commands.work.WorkflowState') as mock_state_class:
                        mock_state_instance = Mock()
                        mock_state_class.return_value = mock_state_instance

                        result = isolated_cli_runner.invoke(work, ["test-task.1"])

                        # Should create WorkflowState with correct fields
                        mock_state_class.assert_called_once()
                        call_kwargs = mock_state_class.call_args.kwargs
                        assert call_kwargs.get("beads_task_id") == "test-task.1"
                        assert call_kwargs.get("beads_task_title") == "Test Task"
                        assert call_kwargs.get("phase") == "planning"
                        # Should call save()
                        mock_state_instance.save.assert_called()


class TestBeadsStatusLifecycle:
    """Tests for Beads status lifecycle management."""

    def test_work_updates_status_to_in_progress(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command updates Beads status to 'in_progress' on start."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test"):
                with patch('jean_claude.cli.commands.work.update_beads_status') as mock_update_status:
                    with patch('jean_claude.cli.commands.work.WorkflowState') as mock_state_class:
                        mock_state_class.return_value = Mock()
                        result = isolated_cli_runner.invoke(work, ["test-task.1"])
                        mock_update_status.assert_called_with("test-task.1", "in_progress")

    def test_work_closes_task_on_success(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command closes Beads task when workflow completes successfully."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('jean_claude.cli.commands.work.close_beads_task') as mock_close:
                        with patch('jean_claude.cli.commands.work.anyio.run') as mock_anyio:
                            # Mock successful workflow
                            mock_state = Mock()
                            mock_state.is_complete.return_value = True
                            mock_state.is_failed.return_value = False
                            mock_state.phase = "implementing"
                            mock_state.save = Mock()
                            mock_anyio.return_value = mock_state

                            result = isolated_cli_runner.invoke(work, ["test-task.1"])
                            mock_close.assert_called_once_with("test-task.1")

    def test_work_does_not_close_on_failure(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command does NOT close task on workflow failure."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', side_effect=RuntimeError("Failed")):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('jean_claude.cli.commands.work.close_beads_task') as mock_close:
                        result = isolated_cli_runner.invoke(work, ["test-task.1"])
                        mock_close.assert_not_called()

    def test_work_handles_status_update_failure_gracefully(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command continues if status update fails."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.update_beads_status', side_effect=RuntimeError("Status update failed")):
                with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test"):
                    with patch('jean_claude.cli.commands.work.WorkflowState') as mock_state_class:
                        mock_state_class.return_value = Mock()
                        result = isolated_cli_runner.invoke(work, ["test-task.1"])
                        # Should not crash - shows warning
                        assert "Test Task" in result.output or "test-task.1" in result.output


class TestWorkEventEmission:
    """Tests for event emission in work command."""

    def test_work_emits_workflow_events(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command emits workflow.started event with beads_task_id."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('jean_claude.cli.commands.work.anyio.run') as mock_anyio:
                        # Mock the workflow execution to prevent actual SDK calls
                        mock_state = Mock()
                        mock_state.is_complete.return_value = True
                        mock_anyio.return_value = mock_state

                        with patch('jean_claude.cli.commands.work.EventLogger') as mock_logger_class:
                            mock_logger = Mock()
                            mock_logger_class.return_value = mock_logger

                            result = isolated_cli_runner.invoke(work, ["test-task.1"])

                            # Should emit workflow.started event with beads_task_id
                            mock_logger.emit.assert_any_call(
                                workflow_id="beads-test-task.1",
                                event_type="workflow.started",
                                data={"beads_task_id": "test-task.1"}
                            )


class TestWorkflowIntegration:
    """Tests for work command integration with run_two_agent_workflow."""

    def test_work_calls_workflow_with_spec(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command calls run_two_agent_workflow with generated spec."""
        spec_content = "# Test Spec\n\nTest content"
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value=spec_content):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('jean_claude.cli.commands.work.anyio.run') as mock_anyio:
                        mock_state = Mock()
                        mock_state.is_complete.return_value = True
                        mock_anyio.return_value = mock_state

                        result = isolated_cli_runner.invoke(work, ["test-task.1"])

                        # Verify spec file was created
                        spec_path = Path("specs/beads-test-task.1.md")
                        assert spec_path.exists()
                        assert mock_anyio.called

    def test_work_model_flag_overrides_both_agents(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that --model flag sets both initializer and coder models."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('jean_claude.cli.commands.work.run_two_agent_workflow') as mock_workflow:
                        mock_state = Mock()
                        mock_state.is_complete.return_value = True

                        with patch('jean_claude.cli.commands.work.anyio.run', side_effect=lambda fn, *args: fn(*args)):
                            mock_workflow.return_value = mock_state
                            result = isolated_cli_runner.invoke(work, ["test-task.1", "--model", "opus"])

                            assert mock_workflow.called
                            call_args = mock_workflow.call_args.args
                            assert call_args[3] == "opus"  # initializer_model
                            assert call_args[4] == "opus"  # coder_model

    def test_work_handles_workflow_errors(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command handles run_two_agent_workflow errors gracefully."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('jean_claude.cli.commands.work.anyio.run', side_effect=RuntimeError("Workflow failed")):
                        result = isolated_cli_runner.invoke(work, ["test-task.1"])
                        assert result.exit_code != 0
                        assert "error" in result.output.lower() or "failed" in result.output.lower()

    def test_show_plan_without_approval_skips_workflow(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that --show-plan mode waits for user approval before executing workflow."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    with patch('jean_claude.cli.commands.work.anyio.run') as mock_anyio:
                        # User declines
                        result = isolated_cli_runner.invoke(work, ["test-task.1", "--show-plan"], input="n\n")
                        mock_anyio.assert_not_called()


class TestWorkPhaseTransitions:
    """Tests for WorkflowState phase transitions."""

    def test_work_saves_state_with_planning_phase(self, mock_beads_task, mock_task_validator, isolated_cli_runner):
        """Test that work command saves state with planning phase initially."""
        with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task):
            with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test"):
                with patch('jean_claude.cli.commands.work.update_beads_status'):
                    result = isolated_cli_runner.invoke(work, ["test-task.1"])

                    # Load the saved workflow state
                    state_path = Path("agents/beads-test-task.1/state.json")
                    assert state_path.exists()

                    with open(state_path) as f:
                        state_data = json.load(f)

                    assert "phase" in state_data
                    assert state_data["phase"] in ["planning", "implementing", "verifying", "complete"]


# NOTE: Dead exception handler detection removed
# The previous test gave false positives by only checking indentation levels,
# not whether exception handlers were part of the same try-except chain.
# Static analysis tools like Ruff properly detect unreachable exception handlers
# through AST traversal, making this manual test redundant.
