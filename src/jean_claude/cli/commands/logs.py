# ABOUTME: Implementation of the 'jc logs' command for viewing workflow event logs
# ABOUTME: Supports filtering by time, level, and real-time tailing with --follow

"""View and tail workflow logs."""

import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator

import click
from rich.console import Console
from rich.text import Text

from jean_claude.core.state import WorkflowState

console = Console()


# Event type to log level mapping
EVENT_LEVELS = {
    # Workflow events - INFO level
    "workflow.started": "INFO",
    "workflow.phase_changed": "INFO",
    "workflow.completed": "INFO",
    # Feature events - INFO level
    "feature.planned": "INFO",
    "feature.started": "INFO",
    "feature.completed": "INFO",
    "feature.failed": "ERROR",
    # Agent events - DEBUG/ERROR level
    "agent.tool_use": "DEBUG",
    "agent.test_result": "INFO",
    "agent.error": "ERROR",
}

# Level to color mapping
LEVEL_COLORS = {
    "DEBUG": "dim",
    "INFO": "cyan",
    "WARN": "yellow",
    "ERROR": "red",
}

# Level hierarchy for filtering
LEVEL_HIERARCHY = ["DEBUG", "INFO", "WARN", "ERROR"]


def parse_duration(duration_str: str) -> timedelta:
    """Parse a duration string like '5m' or '1h' into timedelta.

    Args:
        duration_str: Duration string (e.g., '5m', '1h', '30s', '2d')

    Returns:
        timedelta representing the duration

    Raises:
        ValueError: If the format is invalid
    """
    match = re.match(r'^(\d+)([smhd])$', duration_str.lower())
    if not match:
        raise ValueError(f"Invalid duration format: {duration_str}. Use format like '5m', '1h', '30s', '2d'")

    value = int(match.group(1))
    unit = match.group(2)

    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    else:
        raise ValueError(f"Unknown time unit: {unit}")


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

    # Find the most recently modified events.jsonl
    most_recent = None
    most_recent_time = None

    for workflow_dir in workflow_dirs:
        events_file = workflow_dir / "events.jsonl"
        if events_file.exists():
            mtime = events_file.stat().st_mtime
            if most_recent_time is None or mtime > most_recent_time:
                most_recent = workflow_dir.name
                most_recent_time = mtime

    return most_recent


def read_events(events_file: Path) -> Iterator[dict]:
    """Read events from a JSONL file.

    Args:
        events_file: Path to events.jsonl file

    Yields:
        Event dictionaries, skipping malformed lines
    """
    if not events_file.exists():
        return

    with open(events_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue


def get_event_level(event_type: str) -> str:
    """Get the log level for an event type.

    Args:
        event_type: The event type string (e.g., 'workflow.started')

    Returns:
        Log level string (DEBUG, INFO, WARN, ERROR)
    """
    return EVENT_LEVELS.get(event_type, "INFO")


def get_event_category(event_type: str) -> str:
    """Get the category (prefix) from an event type.

    Args:
        event_type: The event type string (e.g., 'workflow.started')

    Returns:
        Category string (e.g., 'workflow')
    """
    if "." in event_type:
        return event_type.split(".")[0]
    return event_type


def format_event_data(data: dict) -> str:
    """Format event data as key=value pairs.

    Args:
        data: Event data dictionary

    Returns:
        Formatted string like 'key1=value1 key2=value2'
    """
    parts = []
    for key, value in data.items():
        if isinstance(value, str):
            parts.append(f"{key}={value}")
        else:
            parts.append(f"{key}={json.dumps(value)}")
    return " ".join(parts)


def format_log_line(event: dict, use_color: bool = True) -> str | Text:
    """Format an event as a log line.

    Args:
        event: Event dictionary
        use_color: Whether to use Rich colored output

    Returns:
        Formatted log line string or Rich Text
    """
    timestamp = event.get("timestamp", "")
    event_type = event.get("event_type", "unknown")
    data = event.get("data", {})

    # Parse timestamp to show just time
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        time_str = dt.strftime("%H:%M:%S")
    except (ValueError, AttributeError):
        time_str = timestamp[:8] if len(timestamp) >= 8 else timestamp

    level = get_event_level(event_type)
    data_str = format_event_data(data)

    if use_color:
        text = Text()
        text.append(time_str, style="dim")
        text.append(" [", style="dim")
        text.append(level, style=LEVEL_COLORS.get(level, "white"))
        text.append("]  ", style="dim")
        text.append(event_type, style="bold")
        if data_str:
            text.append(" " + data_str, style="dim")
        return text
    else:
        return f"{time_str} [{level}]  {event_type} {data_str}"


def filter_events(
    events: Iterator[dict],
    since: timedelta | None = None,
    level: str | None = None,
    category: str | None = None,
) -> Iterator[dict]:
    """Filter events by time, level, or category.

    Args:
        events: Iterator of event dictionaries
        since: Only include events from the last N time
        level: Minimum log level to include
        category: Only include events from this category (e.g., 'workflow', 'agent')

    Yields:
        Filtered event dictionaries
    """
    now = datetime.now()
    min_level_idx = LEVEL_HIERARCHY.index(level.upper()) if level and level.upper() in LEVEL_HIERARCHY else 0

    for event in events:
        # Filter by time
        if since is not None:
            try:
                timestamp = event.get("timestamp", "")
                event_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                if now - event_time > since:
                    continue
            except (ValueError, AttributeError):
                continue

        event_type = event.get("event_type", "")

        # Filter by level
        if level:
            event_level = get_event_level(event_type)
            # Special case: 'error' level means only error events
            if level.lower() == "error":
                if event_level != "ERROR":
                    continue
            else:
                event_level_idx = LEVEL_HIERARCHY.index(event_level)
                if event_level_idx < min_level_idx:
                    continue

        # Filter by category
        if category:
            event_category = get_event_category(event_type)
            if event_category.lower() != category.lower():
                continue

        yield event


@click.command()
@click.argument("workflow_id", required=False)
@click.option(
    "--follow", "-f",
    is_flag=True,
    help="Follow logs in real-time (like tail -f)",
)
@click.option(
    "--since",
    type=str,
    help="Show logs from the last N time (e.g., '5m', '1h', '30s')",
)
@click.option(
    "--level",
    type=str,
    help="Filter by log level (debug, info, warn, error) or category (workflow, feature, agent)",
)
@click.option(
    "-n", "--limit",
    type=int,
    default=None,
    help="Limit number of log lines to show",
)
@click.option(
    "--json", "json_output",
    is_flag=True,
    help="Output in JSON format for scripting",
)
def logs(
    workflow_id: str | None,
    follow: bool,
    since: str | None,
    level: str | None,
    limit: int | None,
    json_output: bool,
) -> None:
    """View workflow event logs.

    Shows events from the workflow's events.jsonl file with colored output.

    \b
    Examples:
      jc logs                      # Show logs from most recent workflow
      jc logs my-workflow-123      # Show logs from specific workflow
      jc logs --follow             # Tail logs in real-time
      jc logs --since 5m           # Show logs from last 5 minutes
      jc logs --level info         # Filter to INFO level and above
      jc logs --level error        # Show only error events
      jc logs --level workflow     # Show only workflow.* events
      jc logs -n 20                # Show last 20 log lines
      jc logs --json               # Output as JSON array
    """
    project_root = Path.cwd()

    # Determine which workflow to show
    if workflow_id is None:
        workflow_id = find_most_recent_workflow(project_root)
        if workflow_id is None:
            console.print("[yellow]No workflows found with logs[/yellow]")
            console.print("[dim]Run 'jc work <task-id>' to start a workflow[/dim]")
            return

    # Check workflow exists
    events_file = project_root / "agents" / workflow_id / "events.jsonl"
    if not events_file.exists():
        console.print(f"[red]Error:[/red] Workflow '{workflow_id}' not found or has no logs")
        console.print("[dim]Run 'jc status --all' to see available workflows[/dim]")
        raise click.Abort()

    # Parse since duration
    since_delta = None
    if since:
        try:
            since_delta = parse_duration(since)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise click.Abort()

    # Determine if level is a category or actual level
    category = None
    level_filter = level
    if level and level.lower() in ["workflow", "feature", "agent"]:
        category = level
        level_filter = None

    if follow:
        # Real-time tailing mode
        console.print(f"[dim]Tailing logs for workflow {workflow_id}... (Ctrl+C to stop)[/dim]")

        try:
            last_position = 0
            while True:
                if events_file.exists():
                    with open(events_file) as f:
                        f.seek(last_position)
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                event = json.loads(line)
                                # Apply filters
                                filtered = list(filter_events(
                                    [event],
                                    since=since_delta,
                                    level=level_filter,
                                    category=category,
                                ))
                                if filtered:
                                    if json_output:
                                        console.print_json(data=filtered[0])
                                    else:
                                        console.print(format_log_line(event))
                            except json.JSONDecodeError:
                                continue
                        last_position = f.tell()

                time.sleep(0.5)  # Poll every 500ms
        except KeyboardInterrupt:
            console.print("\n[dim]Stopped tailing logs[/dim]")
            return
    else:
        # Read all events
        events = list(read_events(events_file))

        # Apply filters
        filtered_events = list(filter_events(
            iter(events),
            since=since_delta,
            level=level_filter,
            category=category,
        ))

        # Apply limit (take last N events)
        if limit is not None and limit > 0:
            filtered_events = filtered_events[-limit:]

        if json_output:
            console.print_json(data=filtered_events)
        else:
            if not filtered_events:
                console.print("[dim]No matching log entries[/dim]")
                return

            for event in filtered_events:
                console.print(format_log_line(event))
