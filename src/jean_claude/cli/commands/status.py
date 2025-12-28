# ABOUTME: Implementation of the 'jc status' command for workflow monitoring
# ABOUTME: Shows progress, features, timing, and cost metrics for workflows

"""Check the status of workflows."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.table import Table
from rich.text import Text

from jean_claude.core.state import WorkflowState
from jean_claude.core.events import EventLogger

console = Console()


def find_most_recent_workflow(project_root: Path) -> str | None:
    """Find the most recently updated workflow.

    Args:
        project_root: Root directory of the project

    Returns:
        Workflow ID of the most recent workflow, or None if no workflows exist
    """
    agents_dir = project_root / "agents"
    if not agents_dir.exists():
        return None

    workflow_dirs = [d for d in agents_dir.iterdir() if d.is_dir()]
    if not workflow_dirs:
        return None

    # Find the most recently updated state file
    most_recent = None
    most_recent_time = None

    for workflow_dir in workflow_dirs:
        state_file = workflow_dir / "state.json"
        if state_file.exists():
            try:
                state = WorkflowState.load_from_file(state_file)
                if most_recent_time is None or state.updated_at > most_recent_time:
                    most_recent = state.workflow_id
                    most_recent_time = state.updated_at
            except Exception:
                continue

    return most_recent


def get_all_workflows(project_root: Path) -> list[WorkflowState]:
    """Get all workflows sorted by most recent first.

    Args:
        project_root: Root directory of the project

    Returns:
        List of WorkflowState objects sorted by updated_at descending
    """
    agents_dir = project_root / "agents"
    if not agents_dir.exists():
        return []

    workflows = []
    for workflow_dir in agents_dir.iterdir():
        if not workflow_dir.is_dir():
            continue

        state_file = workflow_dir / "state.json"
        if state_file.exists():
            try:
                state = WorkflowState.load_from_file(state_file)
                workflows.append(state)
            except Exception:
                continue

    # Sort by updated_at descending (most recent first)
    workflows.sort(key=lambda w: w.updated_at, reverse=True)
    return workflows


def get_feature_durations(project_root: Path, workflow_id: str) -> dict[str, int]:
    """Calculate duration in milliseconds for each feature from events.

    Args:
        project_root: Root directory of the project
        workflow_id: ID of the workflow

    Returns:
        Dict mapping feature names to duration in milliseconds
    """
    durations = {}
    events_file = project_root / "agents" / workflow_id / "events.jsonl"

    if not events_file.exists():
        return durations

    # Track start times for each feature
    feature_starts: dict[str, datetime] = {}

    try:
        with open(events_file) as f:
            for line in f:
                event = json.loads(line)
                event_type = event.get("event_type")
                data = event.get("data", {})

                if event_type == "feature.started":
                    feature_name = data.get("feature_name")
                    if feature_name:
                        feature_starts[feature_name] = datetime.fromisoformat(event["timestamp"])

                elif event_type == "feature.completed":
                    feature_name = data.get("feature_name")
                    if feature_name and feature_name in feature_starts:
                        end_time = datetime.fromisoformat(event["timestamp"])
                        duration_ms = int((end_time - feature_starts[feature_name]).total_seconds() * 1000)
                        durations[feature_name] = duration_ms
    except Exception:
        pass

    return durations


def format_duration(ms: int) -> str:
    """Format duration in milliseconds to human readable string.

    Args:
        ms: Duration in milliseconds

    Returns:
        Formatted string like "2m 14s" or "45s"
    """
    seconds = ms // 1000
    minutes = seconds // 60
    remaining_seconds = seconds % 60

    if minutes > 0:
        return f"{minutes}m {remaining_seconds:02d}s"
    return f"{remaining_seconds}s"


def get_status_icon(status: str) -> str:
    """Get status icon for a feature.

    Args:
        status: Feature status (completed, in_progress, not_started, failed)

    Returns:
        Unicode icon representing the status
    """
    icons = {
        "completed": "✓",
        "in_progress": "→",
        "not_started": "○",
        "failed": "✗",
    }
    return icons.get(status, "○")


def display_workflow_status(state: WorkflowState, project_root: Path, verbose: bool = False) -> None:
    """Display workflow status in human-readable format.

    Args:
        state: WorkflowState to display
        project_root: Root directory of the project
        verbose: Whether to show detailed feature information
    """
    # Header
    console.print(f"\n[bold]Workflow:[/bold] {state.workflow_id}")

    if state.beads_task_title:
        priority = state.inputs.get("priority", "")
        task_type = state.workflow_type
        console.print(f"[bold]Task:[/bold] {state.beads_task_title} [{priority}, {task_type}]")

    console.print(f"[bold]Phase:[/bold] {state.phase}")

    # Progress bar
    if state.features:
        completed = sum(1 for f in state.features if f.status == "completed")
        total = len(state.features)
        percentage = int(state.progress_percentage)

        # Create progress bar
        bar_width = 20
        filled = int(bar_width * percentage / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        console.print(f"[bold]Progress:[/bold] {bar} {completed}/{total} features ({percentage}%)\n")

        # Features list
        console.print("[bold]Features:[/bold]")

        durations = get_feature_durations(project_root, state.workflow_id)

        for feature in state.features:
            icon = get_status_icon(feature.status)
            name = feature.name

            # Format status text
            if feature.status == "in_progress":
                duration = durations.get(feature.name, 0)
                if duration > 0:
                    status_text = f"{format_duration(duration)} (in progress)"
                else:
                    status_text = "(in progress)"
                line = f"  {icon} {name:<40} {status_text}"
                console.print(f"[yellow]{line}[/yellow]")

            elif feature.status == "completed":
                duration = durations.get(feature.name, 0)
                if duration > 0:
                    status_text = format_duration(duration)
                else:
                    status_text = ""
                line = f"  {icon} {name:<40} {status_text}"
                console.print(f"[green]{line}[/green]")

            elif feature.status == "failed":
                line = f"  {icon} {name:<40} failed"
                console.print(f"[red]{line}[/red]")

            else:  # not_started
                line = f"  {icon} {name:<40} pending"
                console.print(f"[dim]{line}[/dim]")

            # Show description in verbose mode
            if verbose and feature.description:
                console.print(f"      [dim]{feature.description}[/dim]")

        console.print()

    # Duration and cost
    if state.total_duration_ms > 0:
        total_duration = format_duration(state.total_duration_ms)
        cost = f"${state.total_cost_usd:.2f}"
        console.print(f"[bold]Duration:[/bold] {total_duration} | [bold]Cost:[/bold] {cost}")
    else:
        console.print("[dim]No timing data available yet[/dim]")

    console.print()


def display_all_workflows(workflows: list[WorkflowState]) -> None:
    """Display summary of all workflows.

    Args:
        workflows: List of WorkflowState objects to display
    """
    if not workflows:
        console.print("[yellow]No workflows found[/yellow]")
        return

    table = Table(title="All Workflows")
    table.add_column("Workflow ID", style="cyan")
    table.add_column("Task", style="white")
    table.add_column("Phase", style="yellow")
    table.add_column("Progress", style="green")
    table.add_column("Status", style="magenta")

    for state in workflows:
        task_title = state.beads_task_title or state.workflow_name
        phase = state.phase

        if state.features:
            completed = sum(1 for f in state.features if f.status == "completed")
            total = len(state.features)
            progress = f"{completed}/{total} ({int(state.progress_percentage)}%)"
        else:
            progress = "N/A"

        # Determine overall status
        if state.is_complete():
            status = "✓ Complete"
            status_style = "green"
        elif state.is_failed():
            status = "✗ Failed"
            status_style = "red"
        else:
            status = "→ In Progress"
            status_style = "yellow"

        table.add_row(
            state.workflow_id,
            task_title[:50],  # Truncate long titles
            phase,
            progress,
            f"[{status_style}]{status}[/{status_style}]"
        )

    console.print(table)


def get_json_output(state: WorkflowState, project_root: Path) -> dict[str, Any]:
    """Generate JSON output for a workflow.

    Args:
        state: WorkflowState to convert to JSON
        project_root: Root directory of the project

    Returns:
        Dict suitable for JSON serialization
    """
    durations = get_feature_durations(project_root, state.workflow_id)

    features_json = []
    for feature in state.features:
        feature_dict = {
            "name": feature.name,
            "description": feature.description,
            "status": feature.status,
            "duration_ms": durations.get(feature.name, 0),
            "test_file": feature.test_file,
            "tests_passing": feature.tests_passing,
        }
        features_json.append(feature_dict)

    return {
        "workflow_id": state.workflow_id,
        "workflow_name": state.workflow_name,
        "workflow_type": state.workflow_type,
        "phase": state.phase,
        "beads_task_id": state.beads_task_id,
        "beads_task_title": state.beads_task_title,
        "features": features_json,
        "completed": sum(1 for f in state.features if f.status == "completed"),
        "total": len(state.features),
        "progress_percentage": state.progress_percentage,
        "duration_ms": state.total_duration_ms,
        "cost_usd": state.total_cost_usd,
        "is_complete": state.is_complete(),
        "is_failed": state.is_failed(),
    }


@click.command()
@click.argument("workflow_id", required=False)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output in JSON format for scripting",
)
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    help="List all workflows with summary",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed feature information",
)
def status(workflow_id: str | None, json_output: bool, show_all: bool, verbose: bool) -> None:
    """Check the status of workflows.

    Shows progress, features, timing, and cost metrics for workflows.

    \b
    Examples:
      jc status                    # Show most recent workflow
      jc status my-workflow-123    # Show specific workflow
      jc status --json             # JSON output for scripting
      jc status --all              # List all workflows
      jc status --verbose          # Show detailed feature info
    """
    project_root = Path.cwd()

    # Show all workflows
    if show_all:
        workflows = get_all_workflows(project_root)
        if json_output:
            output = [get_json_output(w, project_root) for w in workflows]
            console.print_json(data=output)
        else:
            display_all_workflows(workflows)
        return

    # Determine which workflow to show
    if workflow_id is None:
        workflow_id = find_most_recent_workflow(project_root)
        if workflow_id is None:
            console.print("[yellow]No workflows found[/yellow]")
            console.print("[dim]Run 'jc work <task-id>' to start a workflow[/dim]")
            return

    # Load the workflow state
    try:
        state = WorkflowState.load(workflow_id, project_root)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Workflow '{workflow_id}' not found")
        console.print("[dim]Run 'jc status --all' to see available workflows[/dim]")
        raise click.Abort()

    # Display or output JSON
    if json_output:
        output = get_json_output(state, project_root)
        console.print_json(data=output)
    else:
        display_workflow_status(state, project_root, verbose=verbose)
