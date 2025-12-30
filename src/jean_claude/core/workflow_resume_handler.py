# ABOUTME: WorkflowResumeHandler for updating WorkflowState based on user decision and logging resume events
# ABOUTME: Handles workflow resumption when user provides decision on blockers requiring intervention

"""WorkflowResumeHandler for resuming workflows and logging resume events.

This module provides the WorkflowResumeHandler class that updates the WorkflowState
based on user decisions, sets the waiting_for_response flag to False, and logs resume
events to the events system when a workflow is resumed after user intervention.
"""

from pathlib import Path
from typing import Union

from jean_claude.core.state import WorkflowState
from jean_claude.core.events import EventLogger, EventType
from jean_claude.core.response_parser import UserDecision


class WorkflowResumeHandler:
    """Handles resuming workflows after user intervention and decision.

    The WorkflowResumeHandler is responsible for:
    1. Setting waiting_for_response=False in the WorkflowState
    2. Saving the updated state to disk
    3. Logging a resume event with user decision to the events system

    This component is used when user decisions are received that resolve
    blockers, allowing the workflow to continue with clear direction.

    Attributes:
        project_root: Path to the project root directory where workflow state is stored
    """

    def __init__(self, project_root: Union[str, Path]):
        """Initialize the WorkflowResumeHandler.

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

    def resume_workflow(self, workflow_state: WorkflowState, user_decision: UserDecision) -> None:
        """Resume a workflow by setting waiting_for_response=False and logging the event.

        This method:
        1. Validates inputs
        2. Sets workflow_state.waiting_for_response = False
        3. Saves the updated workflow state to disk
        4. Logs a resume event with user decision to the events system

        Args:
            workflow_state: The WorkflowState to resume
            user_decision: UserDecision containing the user's choice on how to proceed

        Raises:
            TypeError: If workflow_state is not a WorkflowState or user_decision is not a UserDecision
            PermissionError: If unable to save state or write events (propagated from underlying operations)

        Example:
            >>> handler = WorkflowResumeHandler(Path("/project"))
            >>> state = WorkflowState(workflow_id="test", ...)
            >>> decision = UserDecision(decision_type=DecisionType.FIX, ...)
            >>> handler.resume_workflow(state, decision)
        """
        # Validate workflow_state type
        if not isinstance(workflow_state, WorkflowState):
            raise TypeError(f"workflow_state must be a WorkflowState, got {type(workflow_state)}")

        # Validate user_decision type
        if not isinstance(user_decision, UserDecision):
            raise TypeError(f"user_decision must be a UserDecision, got {type(user_decision)}")

        # Set the waiting_for_response flag to False
        workflow_state.waiting_for_response = False

        # Save the updated state to disk
        workflow_state.save(self.project_root)

        # Log the resume event with user decision data
        event_logger = EventLogger(self.project_root)
        event_logger.emit(
            workflow_id=workflow_state.workflow_id,
            event_type=EventType.WORKFLOW_RESUMED,
            data={
                "user_decision": {
                    "decision_type": user_decision.decision_type.value,
                    "message": user_decision.message,
                    "context": user_decision.context
                },
                "waiting_for_response": False
            }
        )