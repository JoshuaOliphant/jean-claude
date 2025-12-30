# ABOUTME: WorkflowPauseHandler for setting waiting_for_response=True and logging pause events
# ABOUTME: Handles workflow pausing when blockers are detected that require user intervention

"""WorkflowPauseHandler for pausing workflows and logging pause events.

This module provides the WorkflowPauseHandler class that sets the waiting_for_response
flag in WorkflowState and logs pause events to the events system when a workflow
needs to be paused due to blockers requiring user intervention.
"""

from pathlib import Path
from typing import Union

from jean_claude.core.state import WorkflowState
from jean_claude.core.events import EventLogger, EventType


class WorkflowPauseHandler:
    """Handles pausing workflows when blockers require user intervention.

    The WorkflowPauseHandler is responsible for:
    1. Setting waiting_for_response=True in the WorkflowState
    2. Saving the updated state to disk
    3. Logging a pause event to the events system

    This component is used when blockers are detected that require user
    intervention, such as test failures, errors, or ambiguous requirements.

    Attributes:
        project_root: Path to the project root directory where workflow state is stored
    """

    def __init__(self, project_root: Union[str, Path]):
        """Initialize the WorkflowPauseHandler.

        Args:
            project_root: Path to the project root directory

        Raises:
            TypeError: If project_root is None
            ValueError: If project_root is an empty string
        """
        if project_root is None:
            raise TypeError("project_root cannot be None")

        if isinstance(project_root, str):
            if not project_root.strip():
                raise ValueError("project_root cannot be empty")
            project_root = Path(project_root)

        self.project_root = Path(project_root)

    def pause_workflow(self, workflow_state: WorkflowState, reason: str) -> None:
        """Pause a workflow by setting waiting_for_response=True and logging the event.

        This method:
        1. Validates inputs
        2. Sets workflow_state.waiting_for_response = True
        3. Saves the updated workflow state to disk
        4. Logs a pause event with the reason to the events system

        Args:
            workflow_state: The WorkflowState to pause
            reason: String explaining why the workflow is being paused

        Raises:
            TypeError: If workflow_state is not a WorkflowState or reason is not a string
            ValueError: If reason is empty or only whitespace
            PermissionError: If unable to save state or write events (propagated from underlying operations)

        Example:
            >>> handler = WorkflowPauseHandler(Path("/project"))
            >>> state = WorkflowState(workflow_id="test", ...)
            >>> handler.pause_workflow(state, "Test failures detected")
        """
        # Validate workflow_state type
        if not isinstance(workflow_state, WorkflowState):
            raise TypeError(f"workflow_state must be a WorkflowState, got {type(workflow_state)}")

        # Validate reason type and content
        if not isinstance(reason, str):
            raise TypeError(f"reason must be a string, got {type(reason)}")

        if not reason.strip():
            raise ValueError("reason cannot be empty or only whitespace")

        # Set the waiting_for_response flag
        workflow_state.waiting_for_response = True

        # Save the updated state to disk
        workflow_state.save(self.project_root)

        # Log the pause event
        event_logger = EventLogger(self.project_root)
        event_logger.emit(
            workflow_id=workflow_state.workflow_id,
            event_type=EventType.WORKFLOW_PAUSED,
            data={
                "reason": reason,
                "waiting_for_response": True
            }
        )