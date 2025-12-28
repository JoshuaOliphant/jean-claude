# ABOUTME: Beads integration module for jean_claude
# ABOUTME: Provides models and functions to interact with Beads task management system

"""Beads integration for jean_claude.

This module provides integration with the Beads task management system,
allowing jean_claude to fetch task details, update task status, and
generate specifications from Beads tasks.
"""

import json
import subprocess
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, Field, field_validator


class BeadsTaskStatus(str, Enum):
    """Enum representing the possible statuses of a Beads task.

    These values match what the Beads CLI actually returns in JSON output.
    """

    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    CLOSED = 'closed'


class BeadsTaskPriority(str, Enum):
    """Enum representing the possible priorities of a Beads task."""

    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class BeadsTaskType(str, Enum):
    """Enum representing the possible types of a Beads task."""

    BUG = 'bug'
    FEATURE = 'feature'
    CHORE = 'chore'
    DOCS = 'docs'


class BeadsTask(BaseModel):
    """Model representing a Beads task.

    Attributes:
        id: Unique identifier for the task
        title: Task title
        description: Detailed description of the task
        acceptance_criteria: List of acceptance criteria that must be met
        status: Current status of the task
        priority: Priority level of the task (low/medium/high/critical)
        task_type: Type of task (bug/feature/chore/docs)
        created_at: Timestamp when the task was created
        updated_at: Timestamp when the task was last updated
    """

    model_config = {"extra": "ignore"}  # Ignore extra fields from Beads

    id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed task description")
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description="List of acceptance criteria"
    )
    status: BeadsTaskStatus = Field(..., description="Current task status")
    priority: Optional[BeadsTaskPriority] = Field(
        default=None,
        description="Priority level of the task"
    )
    task_type: Optional[BeadsTaskType] = Field(
        default=None,
        description="Type of task",
        validation_alias=AliasChoices("task_type", "issue_type")
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the task was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the task was last updated"
    )

    @field_validator('id', 'title', 'description')
    @classmethod
    def validate_required_strings(cls, v: str, info) -> str:
        """Validate that required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v

    @field_validator('acceptance_criteria', mode='before')
    @classmethod
    def parse_acceptance_criteria(cls, v) -> List[str]:
        """Parse acceptance_criteria from string or list."""
        if isinstance(v, str):
            # Parse markdown checklist format
            lines = v.strip().split('\n')
            return [line.lstrip('- [ ] ').lstrip('- [x] ').strip()
                    for line in lines if line.strip()]
        return v if v else []

    @field_validator('status', mode='before')
    @classmethod
    def normalize_status(cls, v) -> BeadsTaskStatus:
        """Normalize status values from Beads CLI to internal enum values.

        Maps external status values to internal enum:
        - 'open', 'not_started', 'todo' -> OPEN
        - 'in_progress' -> IN_PROGRESS
        - 'done', 'closed' -> CLOSED
        """
        if isinstance(v, BeadsTaskStatus):
            return v

        if isinstance(v, str):
            # Validate it's not empty
            if not v or not v.strip():
                raise ValueError("status cannot be empty")

            # Map Beads CLI status values to internal enum
            status_map = {
                'open': BeadsTaskStatus.OPEN,
                'not_started': BeadsTaskStatus.OPEN,
                'todo': BeadsTaskStatus.OPEN,
                'in_progress': BeadsTaskStatus.IN_PROGRESS,
                'done': BeadsTaskStatus.CLOSED,
                'closed': BeadsTaskStatus.CLOSED,
            }

            normalized = status_map.get(v.lower())
            if normalized:
                return normalized

            # If not in map, try to create enum from value
            try:
                return BeadsTaskStatus(v)
            except ValueError:
                raise ValueError(f"Invalid status value: {v}")

        return v

    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority(cls, v) -> Optional[BeadsTaskPriority]:
        """Validate and normalize priority values.

        Args:
            v: The priority value to validate

        Returns:
            BeadsTaskPriority enum value or None

        Raises:
            ValueError: If priority value is invalid
        """
        if v is None:
            return None

        if isinstance(v, BeadsTaskPriority):
            return v

        # Map integer priority (0-4) to word-based priority
        if isinstance(v, int):
            int_mapping = {
                0: 'critical',
                1: 'high',
                2: 'medium',
                3: 'low',
                4: 'low',
            }
            if v in int_mapping:
                return BeadsTaskPriority(int_mapping[v])
            raise ValueError(f"Invalid priority: {v}. Must be 0-4")

        if isinstance(v, str):
            # Map P0-P4 format to word-based priority
            priority_mapping = {
                'p0': 'critical',
                'p1': 'high',
                'p2': 'medium',
                'p3': 'low',
                'p4': 'low',
            }
            normalized = v.lower()
            if normalized in priority_mapping:
                normalized = priority_mapping[normalized]

            # Try to create enum from value
            try:
                return BeadsTaskPriority(normalized)
            except ValueError:
                raise ValueError(
                    f"Invalid priority: {v}. Must be one of: low, medium, high, critical (or P0-P4)"
                )

        return v

    @field_validator('task_type', mode='before')
    @classmethod
    def validate_task_type(cls, v) -> Optional[BeadsTaskType]:
        """Validate and normalize task_type values.

        Args:
            v: The task_type value to validate

        Returns:
            BeadsTaskType enum value or None

        Raises:
            ValueError: If task_type value is invalid
        """
        if v is None:
            return None

        if isinstance(v, BeadsTaskType):
            return v

        if isinstance(v, str):
            # Try to create enum from value
            try:
                return BeadsTaskType(v.lower())
            except ValueError:
                raise ValueError(
                    f"Invalid task_type: {v}. Must be one of: bug, feature, chore, docs"
                )

        return v

    @classmethod
    def from_json(cls, json_str: str) -> "BeadsTask":
        """Create a BeadsTask instance from a JSON string.

        This method parses the output from 'bd show --json' commands and creates
        a BeadsTask instance. It handles both single task objects and arrays of
        tasks (taking the first task if an array is provided).

        Args:
            json_str: JSON string containing task data

        Returns:
            BeadsTask instance created from the JSON data

        Raises:
            json.JSONDecodeError: If json_str is not valid JSON
            ValueError: If json_str is empty or results in empty data
            ValidationError: If required fields are missing or invalid
        """
        if not json_str or not json_str.strip():
            raise ValueError("json_str cannot be empty")

        # Parse the JSON string
        task_data = json.loads(json_str)

        # Handle array output (bd show --json returns an array)
        if isinstance(task_data, list):
            if not task_data:
                raise ValueError("JSON array is empty")
            task_data = task_data[0]

        # Create and return BeadsTask instance using Pydantic's model validation
        return cls(**task_data)

    @classmethod
    def from_dict(cls, data: dict) -> "BeadsTask":
        """Create a BeadsTask instance from a dictionary.

        This method creates a BeadsTask instance from a dictionary containing
        task data. It validates all required fields and handles optional fields
        with appropriate defaults.

        Args:
            data: Dictionary containing task data with keys: id, title, description,
                  status, and optionally acceptance_criteria, created_at, updated_at

        Returns:
            BeadsTask instance created from the dictionary data

        Raises:
            ValidationError: If required fields are missing or invalid
        """
        return cls(**data)

    def to_dict(self) -> dict:
        """Convert the BeadsTask instance to a dictionary.

        Returns a dictionary representation of the BeadsTask with all fields
        included. The returned dictionary can be used for JSON serialization
        or passed to from_dict() to recreate the task.

        Returns:
            Dictionary containing all task fields
        """
        return self.model_dump()


def fetch_beads_task(task_id: str) -> BeadsTask:
    """Fetch a Beads task by ID.

    Runs 'bd show --json <task_id>' subprocess to retrieve task details,
    parses the JSON output, and returns a BeadsTask model instance.

    Args:
        task_id: The ID of the task to fetch

    Returns:
        BeadsTask instance with the fetched task data

    Raises:
        ValueError: If task_id is empty or invalid
        subprocess.CalledProcessError: If the bd command fails
        json.JSONDecodeError: If the output is not valid JSON
        RuntimeError: If the subprocess fails with non-zero exit code
    """
    if not task_id or not task_id.strip():
        raise ValueError("task_id cannot be empty")

    try:
        # Run the bd show command with JSON output
        result = subprocess.run(
            ['bd', 'show', '--json', task_id],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse the JSON output
        task_data = json.loads(result.stdout)

        # Handle array output (bd show --json returns an array)
        if isinstance(task_data, list):
            if not task_data:
                raise RuntimeError(f"No task found with ID {task_id}")
            task_data = task_data[0]

        # Create and return BeadsTask instance
        return BeadsTask(**task_data)

    except subprocess.CalledProcessError as e:
        # Handle subprocess errors
        error_msg = f"Failed to fetch task {task_id}: {e.stderr}"
        raise RuntimeError(error_msg) from e
    except json.JSONDecodeError as e:
        # Handle JSON parsing errors
        error_msg = f"Invalid JSON response for task {task_id}: {e}"
        raise json.JSONDecodeError(e.msg, e.doc, e.pos) from None
    except Exception as e:
        # Handle other errors (e.g., validation errors from Pydantic)
        raise


def update_beads_status(task_id: str, status: str) -> None:
    """Update the status of a Beads task.

    Runs 'bd update --status <status> <task_id>' subprocess to update the task status.

    Args:
        task_id: The ID of the task to update
        status: The new status value. Must be one of: not_started, in_progress, done, blocked, cancelled

    Raises:
        ValueError: If task_id or status is empty, or if status is invalid
        RuntimeError: If the subprocess fails with non-zero exit code
    """
    # Validate task_id
    if not task_id or not task_id.strip():
        raise ValueError("task_id cannot be empty")

    # Validate status
    if not status or not status.strip():
        raise ValueError("status cannot be empty")

    # Define valid status values
    valid_statuses = ["not_started", "in_progress", "done", "blocked", "cancelled"]
    if status not in valid_statuses:
        raise ValueError(
            f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}"
        )

    try:
        # Run the bd update command
        subprocess.run(
            ['bd', 'update', '--status', status, task_id],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        # Handle subprocess errors
        error_msg = f"Failed to update status for task {task_id}: {e.stderr}"
        raise RuntimeError(error_msg) from e


def close_beads_task(task_id: str) -> None:
    """Close a Beads task to mark it as completed.

    Runs 'bd close <task_id>' subprocess to mark the task as completed.

    Args:
        task_id: The ID of the task to close

    Raises:
        ValueError: If task_id is empty
        RuntimeError: If the subprocess fails with non-zero exit code
    """
    # Validate task_id
    if not task_id or not task_id.strip():
        raise ValueError("task_id cannot be empty")

    try:
        # Run the bd close command
        subprocess.run(
            ['bd', 'close', task_id],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        # Handle subprocess errors
        error_msg = f"Failed to close task {task_id}: {e.stderr}"
        raise RuntimeError(error_msg) from e


def generate_spec_from_beads(task: BeadsTask) -> str:
    """Generate a markdown specification from a BeadsTask.

    Formats the BeadsTask as a markdown specification compatible with
    Jean Claude workflow input. The spec includes the task title,
    description, acceptance criteria, and task metadata using the
    beads_spec.md template.

    Args:
        task: The BeadsTask to convert to a specification

    Returns:
        A formatted markdown string containing the task specification

    Raises:
        ValueError: If task is None
        FileNotFoundError: If the template file cannot be found
    """
    if task is None:
        raise ValueError("task cannot be None")

    # Load the template file
    from pathlib import Path

    # Get the template path relative to this file
    template_path = Path(__file__).parent.parent / "templates" / "beads_spec.md"

    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found at {template_path}")

    # Read the template
    template_content = template_path.read_text(encoding="utf-8")

    # Format acceptance criteria as markdown list
    if task.acceptance_criteria:
        acceptance_criteria_text = "\n".join(
            f"- {criterion}" for criterion in task.acceptance_criteria
        )
    else:
        acceptance_criteria_text = ""

    # Format timestamps
    created_at_str = task.created_at.strftime("%Y-%m-%d %H:%M:%S")
    updated_at_str = task.updated_at.strftime("%Y-%m-%d %H:%M:%S")

    # Replace placeholders in template
    spec = template_content.replace("{{title}}", task.title)
    spec = spec.replace("{{description}}", task.description)
    spec = spec.replace("{{acceptance_criteria}}", acceptance_criteria_text)
    spec = spec.replace("{{task_id}}", task.id)
    spec = spec.replace("{{status}}", task.status.value)
    spec = spec.replace("{{created_at}}", created_at_str)
    spec = spec.replace("{{updated_at}}", updated_at_str)

    return spec
