# ABOUTME: Tests for workflow_utils module, specifically find_most_recent_workflow() function
# ABOUTME: Tests cover scenarios with state.json only, events.jsonl only, both files, and no workflows

"""Tests for jean_claude.core.workflow_utils module."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from jean_claude.core.workflow_utils import find_most_recent_workflow


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure with agents directory."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    return tmp_path


@pytest.fixture
def workflow_dir(temp_project, workflow_id="test-workflow-1"):
    """Create a workflow directory."""
    workflow_path = temp_project / "agents" / workflow_id
    workflow_path.mkdir(parents=True, exist_ok=True)
    return workflow_path


def create_state_file(workflow_dir: Path, updated_at: datetime = None):
    """Create a state.json file in the workflow directory."""
    if updated_at is None:
        updated_at = datetime.now()

    state_data = {
        "workflow_id": workflow_dir.name,
        "workflow_name": "Test Workflow",
        "workflow_type": "test",
        "phases": {},
        "inputs": {},
        "outputs": {},
        "created_at": updated_at.isoformat(),
        "updated_at": updated_at.isoformat(),
        "process_id": None,
    }

    state_file = workflow_dir / "state.json"
    state_file.write_text(json.dumps(state_data, indent=2))
    return state_file


def create_events_file(workflow_dir: Path):
    """Create an events.jsonl file in the workflow directory."""
    events_file = workflow_dir / "events.jsonl"
    event_data = {
        "event_type": "workflow.started",
        "timestamp": datetime.now().isoformat(),
        "workflow_id": workflow_dir.name,
    }
    events_file.write_text(json.dumps(event_data) + "\n")
    return events_file


def test_find_most_recent_workflow_with_state_file(temp_project):
    """Test find_most_recent_workflow when only state.json exists."""
    # Create a workflow with only state.json
    workflow1_dir = temp_project / "agents" / "workflow-1"
    workflow1_dir.mkdir(parents=True)
    create_state_file(workflow1_dir, datetime.now())

    result = find_most_recent_workflow(temp_project)

    assert result == "workflow-1"


def test_find_most_recent_workflow_with_events_file(temp_project):
    """Test find_most_recent_workflow when only events.jsonl exists."""
    # Create a workflow with only events.jsonl
    workflow1_dir = temp_project / "agents" / "workflow-1"
    workflow1_dir.mkdir(parents=True)
    create_events_file(workflow1_dir)

    result = find_most_recent_workflow(temp_project)

    assert result == "workflow-1"


def test_find_most_recent_workflow_with_both_files(temp_project):
    """Test find_most_recent_workflow when both state.json and events.jsonl exist.

    Should return the workflow with the most recent modification time between the two files.
    """
    import time

    # Create workflow-1 with state.json modified recently
    workflow1_dir = temp_project / "agents" / "workflow-1"
    workflow1_dir.mkdir(parents=True)
    state_file1 = create_state_file(workflow1_dir, datetime.now())

    # Wait a bit to ensure different mtimes
    time.sleep(0.1)

    # Create workflow-2 with events.jsonl modified even more recently
    workflow2_dir = temp_project / "agents" / "workflow-2"
    workflow2_dir.mkdir(parents=True)
    events_file2 = create_events_file(workflow2_dir)

    result = find_most_recent_workflow(temp_project)

    # workflow-2 should be most recent since its events.jsonl was created last
    assert result == "workflow-2"


def test_find_most_recent_workflow_prefers_events_over_state_same_workflow(temp_project):
    """Test that when a workflow has both files, the most recent mtime is used."""
    import time

    # Create a workflow with state.json
    workflow1_dir = temp_project / "agents" / "workflow-1"
    workflow1_dir.mkdir(parents=True)
    state_file = create_state_file(workflow1_dir, datetime.now() - timedelta(hours=1))

    # Wait and create events.jsonl with more recent mtime
    time.sleep(0.1)
    events_file = create_events_file(workflow1_dir)

    result = find_most_recent_workflow(temp_project)

    # Should still return workflow-1, but based on events.jsonl mtime
    assert result == "workflow-1"


def test_find_most_recent_workflow_no_workflows(temp_project):
    """Test find_most_recent_workflow when workflows directory is empty."""
    result = find_most_recent_workflow(temp_project)

    assert result is None


def test_find_most_recent_workflow_no_agents_directory(tmp_path):
    """Test find_most_recent_workflow when agents directory doesn't exist."""
    result = find_most_recent_workflow(tmp_path)

    assert result is None


def test_find_most_recent_workflow_multiple_workflows(temp_project):
    """Test find_most_recent_workflow correctly orders multiple workflows."""
    import time

    # Create workflow-1 (oldest)
    workflow1_dir = temp_project / "agents" / "workflow-1"
    workflow1_dir.mkdir(parents=True)
    create_state_file(workflow1_dir, datetime.now() - timedelta(hours=2))

    time.sleep(0.1)

    # Create workflow-2 (middle)
    workflow2_dir = temp_project / "agents" / "workflow-2"
    workflow2_dir.mkdir(parents=True)
    create_events_file(workflow2_dir)

    time.sleep(0.1)

    # Create workflow-3 (most recent)
    workflow3_dir = temp_project / "agents" / "workflow-3"
    workflow3_dir.mkdir(parents=True)
    create_state_file(workflow3_dir, datetime.now())

    result = find_most_recent_workflow(temp_project)

    # workflow-3 should be most recent
    assert result == "workflow-3"


def test_find_most_recent_workflow_handles_corrupted_state_file(temp_project):
    """Test that corrupted state.json files are skipped gracefully."""
    # Create workflow-1 with corrupted state.json
    workflow1_dir = temp_project / "agents" / "workflow-1"
    workflow1_dir.mkdir(parents=True)
    state_file1 = workflow1_dir / "state.json"
    state_file1.write_text("invalid json {{{")

    # Create workflow-2 with valid state.json
    workflow2_dir = temp_project / "agents" / "workflow-2"
    workflow2_dir.mkdir(parents=True)
    create_state_file(workflow2_dir, datetime.now())

    result = find_most_recent_workflow(temp_project)

    # Should return workflow-2, skipping the corrupted one
    assert result == "workflow-2"


def test_find_most_recent_workflow_with_only_workflow_dir(temp_project):
    """Test that workflow directories without state.json or events.jsonl are ignored."""
    # Create an empty workflow directory
    workflow1_dir = temp_project / "agents" / "workflow-1"
    workflow1_dir.mkdir(parents=True)

    # Create workflow-2 with state.json
    workflow2_dir = temp_project / "agents" / "workflow-2"
    workflow2_dir.mkdir(parents=True)
    create_state_file(workflow2_dir, datetime.now())

    result = find_most_recent_workflow(temp_project)

    # Should return workflow-2, ignoring the empty directory
    assert result == "workflow-2"
