# ABOUTME: Utility functions for working with workflows
# ABOUTME: Provides find_most_recent_workflow() and get_all_workflows() for workflow discovery and loading

"""Workflow utility functions.

This module provides utility functions for working with workflows, including
finding the most recently updated workflow and loading all workflows from
the agents directory with proper error handling.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from jean_claude.core.state import WorkflowState


def find_most_recent_workflow(project_root: Path) -> Optional[str]:
    """Find the most recently updated workflow.

    This function scans all workflow directories in the agents folder and
    determines which workflow was most recently updated by checking the
    modification times of both state.json and events.jsonl files.

    For each workflow directory, it checks:
    - state.json mtime (if it exists)
    - events.jsonl mtime (if it exists)

    The workflow with the most recent modification time across all these
    files is returned.

    Args:
        project_root: Root directory of the project

    Returns:
        Workflow ID of the most recent workflow, or None if no workflows exist
        or if the agents directory doesn't exist.

    Examples:
        >>> project_root = Path("/path/to/project")
        >>> workflow_id = find_most_recent_workflow(project_root)
        >>> if workflow_id:
        ...     print(f"Most recent workflow: {workflow_id}")
    """
    agents_dir = project_root / "agents"
    if not agents_dir.exists():
        return None

    workflow_dirs = [d for d in agents_dir.iterdir() if d.is_dir()]
    if not workflow_dirs:
        return None

    # Track the most recent workflow and its modification time
    most_recent_workflow = None
    most_recent_time = None

    for workflow_dir in workflow_dirs:
        # Check both state.json and events.jsonl for this workflow
        state_file = workflow_dir / "state.json"
        events_file = workflow_dir / "events.jsonl"

        # Get the most recent mtime for this workflow
        workflow_most_recent_time = None

        # Check state.json
        if state_file.exists():
            try:
                state = WorkflowState.load_from_file(state_file)
                # Use the updated_at timestamp from the state file
                if workflow_most_recent_time is None or state.updated_at > workflow_most_recent_time:
                    workflow_most_recent_time = state.updated_at
            except Exception:
                # If we can't load the state file, skip it
                pass

        # Check events.jsonl mtime
        if events_file.exists():
            try:
                mtime = events_file.stat().st_mtime
                # Convert to datetime for comparison
                mtime_dt = datetime.fromtimestamp(mtime)

                if workflow_most_recent_time is None or mtime_dt > workflow_most_recent_time:
                    workflow_most_recent_time = mtime_dt
            except Exception:
                # If we can't stat the file, skip it
                pass

        # Update the global most recent if this workflow is more recent
        if workflow_most_recent_time is not None:
            if most_recent_time is None or workflow_most_recent_time > most_recent_time:
                most_recent_workflow = workflow_dir.name
                most_recent_time = workflow_most_recent_time

    return most_recent_workflow


def get_all_workflows(project_root: Path) -> list[WorkflowState]:
    """Get all workflows from the agents directory.

    This function loads all workflows from the agents directory, handling
    missing directories and skipping corrupted files gracefully.

    Args:
        project_root: Root directory of the project

    Returns:
        List of WorkflowState objects sorted by updated_at descending
        (most recent first). Returns empty list if no workflows exist
        or if the agents directory doesn't exist.

    Examples:
        >>> project_root = Path("/path/to/project")
        >>> workflows = get_all_workflows(project_root)
        >>> for workflow in workflows:
        ...     print(f"{workflow.workflow_id}: {workflow.workflow_name}")
    """
    agents_dir = project_root / "agents"
    if not agents_dir.exists():
        return []

    workflows = []
    for workflow_dir in agents_dir.iterdir():
        if not workflow_dir.is_dir():
            continue

        state_file = workflow_dir / "state.json"
        if not state_file.exists():
            continue

        try:
            state = WorkflowState.load_from_file(state_file)
            workflows.append(state)
        except Exception:
            # Skip corrupted files and continue processing
            continue

    # Sort by updated_at descending (most recent first)
    workflows.sort(key=lambda w: w.updated_at, reverse=True)
    return workflows
