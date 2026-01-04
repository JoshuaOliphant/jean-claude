# ABOUTME: Comprehensive edge case tests for workflow_utils.get_all_workflows function
# ABOUTME: Tests edge cases: empty directory, non-directories in agents folder, corrupted JSON files, missing state.json files

"""Comprehensive edge case tests for jean_claude.core.workflow_utils.get_all_workflows."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from jean_claude.core.workflow_utils import get_all_workflows
from jean_claude.core.state import WorkflowState


class TestGetAllWorkflowsEdgeCases:
    """Comprehensive edge case tests for get_all_workflows function."""

    def test_empty_agents_directory(self):
        """Test get_all_workflows with completely empty agents directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            agents_dir = project_root / "agents"
            agents_dir.mkdir()

            result = get_all_workflows(project_root)

            assert result == []

    def test_missing_agents_directory(self):
        """Test get_all_workflows when agents directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            # Don't create agents directory

            result = get_all_workflows(project_root)

            assert result == []

    def test_non_directories_in_agents_folder(self):
        """Test get_all_workflows skips files and symlinks in agents folder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            agents_dir = project_root / "agents"
            agents_dir.mkdir()

            # Create various non-directory items
            (agents_dir / "regular_file.txt").write_text("not a workflow")
            (agents_dir / "state.json").write_text("misleading name")
            (agents_dir / "another_file.log").write_text("another file")

            # Create empty subdirectory (should be skipped due to no state.json)
            empty_dir = agents_dir / "empty_dir"
            empty_dir.mkdir()

            # Create one valid workflow
            valid_dir = agents_dir / "valid-workflow"
            valid_dir.mkdir()

            now = datetime.now()
            state_data = {
                "workflow_id": "valid-workflow",
                "workflow_name": "Valid Workflow",
                "workflow_type": "beads-task",
                "phases": {},
                "inputs": {},
                "outputs": {},
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "process_id": None,
                "beads_task_id": "test-123",
                "beads_task_title": "Test Task",
                "phase": "implementing",
                "features": [],
                "current_feature_index": 0,
                "iteration_count": 1,
                "max_iterations": 21,
                "session_ids": [],
                "total_cost_usd": 0.0,
                "total_duration_ms": 0,
                "last_verification_at": now.isoformat(),
                "last_verification_passed": True,
                "verification_count": 0,
                "waiting_for_response": False
            }

            state_file = valid_dir / "state.json"
            with open(state_file, 'w') as f:
                json.dump(state_data, f)

            result = get_all_workflows(project_root)

            # Should only return the valid workflow, ignoring files and empty dirs
            assert len(result) == 1
            assert result[0].workflow_id == "valid-workflow"

    def test_corrupted_json_files_multiple_scenarios(self):
        """Test get_all_workflows handles various corrupted JSON scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            agents_dir = project_root / "agents"
            agents_dir.mkdir()

            # Scenario 1: Completely invalid JSON
            corrupted1_dir = agents_dir / "corrupted-1"
            corrupted1_dir.mkdir()
            (corrupted1_dir / "state.json").write_text("invalid json {{{")

            # Scenario 2: Valid JSON but missing required fields
            corrupted2_dir = agents_dir / "corrupted-2"
            corrupted2_dir.mkdir()
            (corrupted2_dir / "state.json").write_text('{"incomplete": "data"}')

            # Scenario 3: Empty file
            corrupted3_dir = agents_dir / "corrupted-3"
            corrupted3_dir.mkdir()
            (corrupted3_dir / "state.json").write_text("")

            # Scenario 4: Null/None content
            corrupted4_dir = agents_dir / "corrupted-4"
            corrupted4_dir.mkdir()
            (corrupted4_dir / "state.json").write_text("null")

            # Create one valid workflow
            valid_dir = agents_dir / "valid-workflow"
            valid_dir.mkdir()

            now = datetime.now()
            state_data = {
                "workflow_id": "valid-workflow",
                "workflow_name": "Valid Workflow",
                "workflow_type": "beads-task",
                "phases": {},
                "inputs": {},
                "outputs": {},
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "process_id": None,
                "beads_task_id": "test-123",
                "beads_task_title": "Test Task",
                "phase": "implementing",
                "features": [],
                "current_feature_index": 0,
                "iteration_count": 1,
                "max_iterations": 21,
                "session_ids": [],
                "total_cost_usd": 0.0,
                "total_duration_ms": 0,
                "last_verification_at": now.isoformat(),
                "last_verification_passed": True,
                "verification_count": 0,
                "waiting_for_response": False
            }

            valid_state_file = valid_dir / "state.json"
            with open(valid_state_file, 'w') as f:
                json.dump(state_data, f)

            result = get_all_workflows(project_root)

            # Should only return the valid workflow, gracefully skipping all corrupted ones
            assert len(result) == 1
            assert result[0].workflow_id == "valid-workflow"

    def test_missing_state_json_files(self):
        """Test get_all_workflows skips directories without state.json files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            agents_dir = project_root / "agents"
            agents_dir.mkdir()

            # Directory with no files
            empty_dir = agents_dir / "empty-workflow"
            empty_dir.mkdir()

            # Directory with other files but no state.json
            other_files_dir = agents_dir / "other-files"
            other_files_dir.mkdir()
            (other_files_dir / "events.jsonl").write_text('{"event": "test"}')
            (other_files_dir / "other.txt").write_text("some content")
            (other_files_dir / "config.yaml").write_text("config: value")

            # Directory with state.json.bak (wrong extension)
            backup_dir = agents_dir / "backup-state"
            backup_dir.mkdir()
            (backup_dir / "state.json.bak").write_text('{"workflow_id": "backup"}')

            # Valid workflow for comparison
            valid_dir = agents_dir / "valid-workflow"
            valid_dir.mkdir()

            now = datetime.now()
            state_data = {
                "workflow_id": "valid-workflow",
                "workflow_name": "Valid Workflow",
                "workflow_type": "beads-task",
                "phases": {},
                "inputs": {},
                "outputs": {},
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "process_id": None,
                "beads_task_id": "test-123",
                "beads_task_title": "Test Task",
                "phase": "implementing",
                "features": [],
                "current_feature_index": 0,
                "iteration_count": 1,
                "max_iterations": 21,
                "session_ids": [],
                "total_cost_usd": 0.0,
                "total_duration_ms": 0,
                "last_verification_at": now.isoformat(),
                "last_verification_passed": True,
                "verification_count": 0,
                "waiting_for_response": False
            }

            state_file = valid_dir / "state.json"
            with open(state_file, 'w') as f:
                json.dump(state_data, f)

            result = get_all_workflows(project_root)

            # Should only return the workflow with valid state.json
            assert len(result) == 1
            assert result[0].workflow_id == "valid-workflow"

    def test_permission_errors_handling(self):
        """Test get_all_workflows gracefully handles file permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            agents_dir = project_root / "agents"
            agents_dir.mkdir()

            # Create a valid workflow first
            valid_dir = agents_dir / "valid-workflow"
            valid_dir.mkdir()

            now = datetime.now()
            state_data = {
                "workflow_id": "valid-workflow",
                "workflow_name": "Valid Workflow",
                "workflow_type": "beads-task",
                "phases": {},
                "inputs": {},
                "outputs": {},
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "process_id": None,
                "beads_task_id": "test-123",
                "beads_task_title": "Test Task",
                "phase": "implementing",
                "features": [],
                "current_feature_index": 0,
                "iteration_count": 1,
                "max_iterations": 21,
                "session_ids": [],
                "total_cost_usd": 0.0,
                "total_duration_ms": 0,
                "last_verification_at": now.isoformat(),
                "last_verification_passed": True,
                "verification_count": 0,
                "waiting_for_response": False
            }

            state_file = valid_dir / "state.json"
            with open(state_file, 'w') as f:
                json.dump(state_data, f)

            # Mock a scenario where WorkflowState.load_from_file raises an exception
            # This simulates permission errors or other I/O issues
            original_load = WorkflowState.load_from_file

            def mock_load_with_error(file_path):
                if "error-prone" in str(file_path):
                    raise PermissionError("Permission denied")
                return original_load(file_path)

            # Create directory that will cause permission error
            error_dir = agents_dir / "error-prone-workflow"
            error_dir.mkdir()
            (error_dir / "state.json").write_text('{"workflow_id": "error-prone"}')

            with patch.object(WorkflowState, 'load_from_file', side_effect=mock_load_with_error):
                result = get_all_workflows(project_root)

            # Should handle the error gracefully and return the valid workflow
            assert len(result) == 1
            assert result[0].workflow_id == "valid-workflow"

    def test_mixed_valid_and_invalid_workflows(self):
        """Test get_all_workflows correctly filters and sorts mixed scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            agents_dir = project_root / "agents"
            agents_dir.mkdir()

            base_time = datetime.now()

            # Mix of different scenarios
            scenarios = [
                ("valid-newest", base_time, True),           # Valid, newest
                ("corrupted", None, False),                   # Corrupted JSON
                ("no-state", None, None),                     # No state.json file
                ("valid-oldest", base_time.replace(year=base_time.year-1), True),  # Valid, oldest
                ("valid-middle", base_time - timedelta(days=30), True),  # Valid, middle (30 days ago)
            ]

            for workflow_id, updated_at, scenario_type in scenarios:
                workflow_dir = agents_dir / workflow_id
                workflow_dir.mkdir()

                if scenario_type is True:  # Valid workflow
                    state_data = {
                        "workflow_id": workflow_id,
                        "workflow_name": f"Workflow {workflow_id}",
                        "workflow_type": "beads-task",
                        "phases": {},
                        "inputs": {},
                        "outputs": {},
                        "created_at": updated_at.isoformat(),
                        "updated_at": updated_at.isoformat(),
                        "process_id": None,
                        "beads_task_id": f"test-{workflow_id}",
                        "beads_task_title": f"Test {workflow_id}",
                        "phase": "implementing",
                        "features": [],
                        "current_feature_index": 0,
                        "iteration_count": 1,
                        "max_iterations": 21,
                        "session_ids": [],
                        "total_cost_usd": 0.0,
                        "total_duration_ms": 0,
                        "last_verification_at": updated_at.isoformat(),
                        "last_verification_passed": True,
                        "verification_count": 0,
                        "waiting_for_response": False
                    }

                    state_file = workflow_dir / "state.json"
                    with open(state_file, 'w') as f:
                        json.dump(state_data, f)

                elif scenario_type is False:  # Corrupted
                    (workflow_dir / "state.json").write_text("invalid json")

                # scenario_type is None means no state.json (already handled by not creating it)

            result = get_all_workflows(project_root)

            # Should only return valid workflows, sorted by updated_at descending
            assert len(result) == 3
            assert result[0].workflow_id == "valid-newest"
            assert result[1].workflow_id == "valid-middle"
            assert result[2].workflow_id == "valid-oldest"

    def test_edge_case_workflow_names(self):
        """Test get_all_workflows handles edge case workflow directory names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            agents_dir = project_root / "agents"
            agents_dir.mkdir()

            now = datetime.now()

            # Edge case directory names
            edge_case_names = [
                "workflow.with.dots",
                "workflow-with-special-chars-123",
                "workflow_with_underscores",
                "WorkflowWithCamelCase",
                "workflow with spaces",  # This might not be valid on all filesystems
                "workflow@with#symbols",
                "123-numeric-start",
                "a",  # Single character
                "very-long-workflow-name-that-might-cause-issues-in-some-systems-but-should-be-handled-gracefully"
            ]

            valid_workflows = []
            for i, name in enumerate(edge_case_names):
                try:
                    workflow_dir = agents_dir / name
                    workflow_dir.mkdir()

                    state_data = {
                        "workflow_id": name,
                        "workflow_name": f"Workflow {name}",
                        "workflow_type": "beads-task",
                        "phases": {},
                        "inputs": {},
                        "outputs": {},
                        "created_at": (now.replace(minute=i)).isoformat(),
                        "updated_at": (now.replace(minute=i)).isoformat(),
                        "process_id": None,
                        "beads_task_id": f"test-{i}",
                        "beads_task_title": f"Test {i}",
                        "phase": "implementing",
                        "features": [],
                        "current_feature_index": 0,
                        "iteration_count": 1,
                        "max_iterations": 21,
                        "session_ids": [],
                        "total_cost_usd": 0.0,
                        "total_duration_ms": 0,
                        "last_verification_at": (now.replace(minute=i)).isoformat(),
                        "last_verification_passed": True,
                        "verification_count": 0,
                        "waiting_for_response": False
                    }

                    state_file = workflow_dir / "state.json"
                    with open(state_file, 'w') as f:
                        json.dump(state_data, f)

                    valid_workflows.append(name)
                except OSError:
                    # Some edge case names might not be valid on this filesystem
                    pass

            result = get_all_workflows(project_root)

            # Should return all workflows that were successfully created
            assert len(result) == len(valid_workflows)

            # Verify all expected workflows are present
            result_ids = {w.workflow_id for w in result}
            expected_ids = set(valid_workflows)
            assert result_ids == expected_ids

    def test_large_number_of_workflows(self):
        """Test get_all_workflows performance and correctness with many workflows."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            agents_dir = project_root / "agents"
            agents_dir.mkdir()

            num_workflows = 50  # Reasonable number for testing
            base_time = datetime.now()

            for i in range(num_workflows):
                workflow_id = f"workflow-{i:03d}"
                workflow_dir = agents_dir / workflow_id
                workflow_dir.mkdir()

                # Vary the timestamps to test sorting
                updated_at = base_time.replace(second=i % 60, microsecond=i * 1000)

                state_data = {
                    "workflow_id": workflow_id,
                    "workflow_name": f"Workflow {i}",
                    "workflow_type": "beads-task",
                    "phases": {},
                    "inputs": {},
                    "outputs": {},
                    "created_at": updated_at.isoformat(),
                    "updated_at": updated_at.isoformat(),
                    "process_id": None,
                    "beads_task_id": f"test-{i}",
                    "beads_task_title": f"Test {i}",
                    "phase": "implementing",
                    "features": [],
                    "current_feature_index": 0,
                    "iteration_count": 1,
                    "max_iterations": 21,
                    "session_ids": [],
                    "total_cost_usd": 0.0,
                    "total_duration_ms": 0,
                    "last_verification_at": updated_at.isoformat(),
                    "last_verification_passed": True,
                    "verification_count": 0,
                    "waiting_for_response": False
                }

                state_file = workflow_dir / "state.json"
                with open(state_file, 'w') as f:
                    json.dump(state_data, f)

            result = get_all_workflows(project_root)

            # Should return all workflows
            assert len(result) == num_workflows

            # Should be sorted by updated_at descending
            for i in range(len(result) - 1):
                assert result[i].updated_at >= result[i + 1].updated_at

            # First should be the one with highest index (latest timestamp)
            assert result[0].workflow_id == f"workflow-{(num_workflows - 1):03d}"