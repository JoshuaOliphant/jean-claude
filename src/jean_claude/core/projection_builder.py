# ABOUTME: Base ProjectionBuilder class for building projections from event streams
# ABOUTME: Provides abstract methods for handling different event types and state management

"""Base ProjectionBuilder class for event-sourced projections.

This module provides the base ProjectionBuilder class which defines the interface
for building projections from event streams. Projections are read-optimized views
of workflow state derived from the immutable event log.

The ProjectionBuilder follows the Command Query Responsibility Segregation (CQRS)
pattern where events are the source of truth and projections provide optimized
views for different use cases (dashboard, API, reports, etc.).

Key Features:
- Abstract base class with required methods for event handling
- Type-safe event application with validation
- Immutable state transformations
- Support for all event types defined in ARCHITECTURE.md
- Error handling for unknown event types
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from .event_models import Event


class ProjectionBuilder(ABC):
    """Base class for building projections from event streams.

    This abstract base class defines the interface that all projection builders
    must implement. Each projection builder handles specific event types and
    transforms them into a projection-specific state representation.

    The apply_event() method serves as the main entry point for event processing,
    dispatching to the appropriate event-specific handler method based on the
    event type.

    Event Types Supported (from ARCHITECTURE.md):
    - workflow.started: Workflow begins execution
    - workflow.completed: Workflow completes successfully
    - workflow.failed: Workflow fails with error
    - worktree.created: Git worktree created for workflow
    - worktree.active: Worktree heartbeat signal (monitoring)
    - worktree.merged: Worktree branch merged back to main
    - worktree.deleted: Worktree cleaned up and deleted
    - feature.planned: Feature planned for implementation
    - feature.started: Feature implementation begins
    - feature.completed: Feature implementation completes
    - feature.failed: Feature implementation fails
    - phase.changed: Workflow phase transition
    - tests.started: Test execution begins
    - tests.passed: Tests complete successfully
    - tests.failed: Test execution fails
    - commit.created: Git commit successfully created
    - commit.failed: Git commit attempt fails

    Example:
        class DashboardProjectionBuilder(ProjectionBuilder):
            def get_initial_state(self):
                return {'workflows': {}, 'active_count': 0}

            def apply_workflow_started(self, state, event):
                new_state = state.copy()
                new_state['workflows'][event.workflow_id] = {
                    'status': 'active',
                    'started_at': event.timestamp
                }
                new_state['active_count'] += 1
                return new_state

            # ... implement other abstract methods ...

        builder = DashboardProjectionBuilder()
        state = builder.get_initial_state()

        event = Event(workflow_id="w1", event_type="workflow.started", event_data={})
        new_state = builder.apply_event(state, event)
    """

    def apply_event(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply an event to the current state and return the new state.

        This is the main entry point for event processing. It validates the inputs,
        dispatches to the appropriate event-specific handler method, and returns
        the transformed state.

        The method ensures immutability by requiring that event handler methods
        return a new state rather than modifying the input state.

        Args:
            state: Current projection state as a dictionary. Must not be None.
            event: Event to apply. Must be a valid Event instance.

        Returns:
            Dict[str, Any]: New state after applying the event. The original state
                           is not modified (immutable transformation).

        Raises:
            TypeError: If state is not a dict or event is not an Event instance.
            ValueError: If the event type is not supported by this projection builder.

        Example:
            >>> builder = SomeProjectionBuilder()
            >>> initial_state = {'count': 0}
            >>> event = Event(workflow_id="w1", event_type="workflow.started", event_data={})
            >>> new_state = builder.apply_event(initial_state, event)
            >>> # original initial_state is unchanged
        """
        # Validate input parameters
        if not isinstance(state, dict):
            raise TypeError("State parameter must be a dict")

        if not isinstance(event, Event):
            raise TypeError("Event parameter must be an Event instance")

        # Dispatch to event-specific handler method based on event type
        event_type = event.event_type

        # Map event types to handler methods
        event_handlers = {
            'workflow.started': self.apply_workflow_started,
            'workflow.completed': self.apply_workflow_completed,
            'workflow.failed': self.apply_workflow_failed,
            'worktree.created': self.apply_worktree_created,
            'worktree.active': self.apply_worktree_active,
            'worktree.merged': self.apply_worktree_merged,
            'worktree.deleted': self.apply_worktree_deleted,
            'feature.planned': self.apply_feature_planned,
            'feature.started': self.apply_feature_started,
            'feature.completed': self.apply_feature_completed,
            'feature.failed': self.apply_feature_failed,
            'phase.changed': self.apply_phase_changed,
            'tests.started': self.apply_tests_started,
            'tests.passed': self.apply_tests_passed,
            'tests.failed': self.apply_tests_failed,
            'commit.created': self.apply_commit_created,
            'commit.failed': self.apply_commit_failed,
        }

        # Get the appropriate handler for this event type
        handler = event_handlers.get(event_type)

        if handler is None:
            raise ValueError(f"Unknown event type: {event_type}")

        # Call the handler with state and event
        return handler(state, event)

    @abstractmethod
    def get_initial_state(self) -> Dict[str, Any]:
        """Return the initial state for this projection.

        This method defines the starting state when no events have been processed
        yet. The structure of the initial state depends on the specific projection
        being built.

        Returns:
            Dict[str, Any]: Initial state dictionary for this projection.

        Example:
            def get_initial_state(self):
                return {
                    'workflow_id': None,
                    'phase': 'unknown',
                    'features': [],
                    'status': 'inactive'
                }
        """
        pass

    @abstractmethod
    def apply_workflow_started(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorkflowStarted event to the state.

        Called when a workflow begins execution. Typically updates the state to
        reflect that the workflow is now active and captures metadata from the
        event data.

        Args:
            state: Current projection state.
            event: WorkflowStarted event with data like description, beads_task_id.

        Returns:
            Dict[str, Any]: New state with workflow started information.

        Expected event.event_data fields:
        - description: Workflow description (optional)
        - beads_task_id: Associated Beads task ID (optional)
        """
        pass

    @abstractmethod
    def apply_workflow_completed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorkflowCompleted event to the state.

        Called when a workflow completes successfully. Updates the state to
        reflect completion status and captures final metrics.

        Args:
            state: Current projection state.
            event: WorkflowCompleted event with data like duration_ms, total_cost.

        Returns:
            Dict[str, Any]: New state with workflow completion information.

        Expected event.event_data fields:
        - duration_ms: Total workflow execution time in milliseconds (optional)
        - total_cost: Total cost of workflow execution (optional)
        """
        pass

    @abstractmethod
    def apply_workflow_failed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorkflowFailed event to the state.

        Called when a workflow fails with an error. Updates the state to
        reflect failure status and captures error information.

        Args:
            state: Current projection state.
            event: WorkflowFailed event with error details and failure context.

        Returns:
            Dict[str, Any]: New state with workflow failure information.

        Expected event.event_data fields:
        - error: Error message or description (optional)
        - phase: Phase where failure occurred (optional)
        """
        pass

    @abstractmethod
    def apply_worktree_created(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorktreeCreated event to the state.

        Called when a git worktree is created for workflow isolation. Updates
        the state with worktree information and branch details.

        Args:
            state: Current projection state.
            event: WorktreeCreated event with worktree path and branch info.

        Returns:
            Dict[str, Any]: New state with worktree information.

        Expected event.event_data fields:
        - path: Filesystem path to the worktree
        - branch: Git branch name for the worktree
        - base_commit: Base commit SHA for the worktree (optional)
        """
        pass

    @abstractmethod
    def apply_feature_planned(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply FeaturePlanned event to the state.

        Called when a feature is planned for implementation. Typically adds
        the feature to a features list or updates feature-related state.

        Args:
            state: Current projection state.
            event: FeaturePlanned event with feature details.

        Returns:
            Dict[str, Any]: New state with planned feature information.

        Expected event.event_data fields:
        - name: Feature name (required)
        - description: Feature description (required)
        - test_file: Associated test file path (optional)
        """
        pass

    @abstractmethod
    def apply_feature_started(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply FeatureStarted event to the state.

        Called when feature implementation begins. Updates the status of the
        specified feature to indicate it's in progress.

        Args:
            state: Current projection state.
            event: FeatureStarted event with feature identifier.

        Returns:
            Dict[str, Any]: New state with updated feature status.

        Expected event.event_data fields:
        - name: Feature name (required)
        """
        pass

    @abstractmethod
    def apply_feature_completed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply FeatureCompleted event to the state.

        Called when feature implementation completes successfully. Updates the
        feature status and captures completion metrics.

        Args:
            state: Current projection state.
            event: FeatureCompleted event with completion details.

        Returns:
            Dict[str, Any]: New state with completed feature information.

        Expected event.event_data fields:
        - name: Feature name (required)
        - tests_passing: Whether tests are passing (optional)
        - duration_ms: Implementation duration in milliseconds (optional)
        """
        pass

    @abstractmethod
    def apply_feature_failed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply FeatureFailed event to the state.

        Called when feature implementation fails. Updates the feature status
        and captures error information.

        Args:
            state: Current projection state.
            event: FeatureFailed event with failure details.

        Returns:
            Dict[str, Any]: New state with failed feature information.

        Expected event.event_data fields:
        - name: Feature name (required)
        - error: Error message or description (optional)
        """
        pass

    @abstractmethod
    def apply_phase_changed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply PhaseChanged event to the state.

        Called when the workflow transitions between phases (e.g., planning
        to implementing). Updates the current phase and optionally tracks
        phase history.

        Args:
            state: Current projection state.
            event: PhaseChanged event with phase transition details.

        Returns:
            Dict[str, Any]: New state with updated phase information.

        Expected event.event_data fields:
        - from_phase: Previous phase (optional)
        - to_phase: New current phase (required)
        """
        pass

    @abstractmethod
    def apply_worktree_active(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorktreeActive event to the state.

        Called when a worktree sends a heartbeat signal indicating it's still
        active. Used for monitoring worktree health and activity.

        Args:
            state: Current projection state.
            event: WorktreeActive event with heartbeat information.

        Returns:
            Dict[str, Any]: New state with updated activity timestamp.

        Expected event.event_data fields:
        - path: Filesystem path to the active worktree
        """
        pass

    @abstractmethod
    def apply_worktree_merged(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorktreeMerged event to the state.

        Called when a worktree branch is successfully merged back to main.
        Updates the state with merge information and final commit details.

        Args:
            state: Current projection state.
            event: WorktreeMerged event with merge commit and conflict details.

        Returns:
            Dict[str, Any]: New state with merge information.

        Expected event.event_data fields:
        - commit_sha: SHA of the merge commit
        - conflicts: List of files that had conflicts (empty if clean merge)
        """
        pass

    @abstractmethod
    def apply_worktree_deleted(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorktreeDeleted event to the state.

        Called when a worktree is cleaned up and deleted. Records the deletion
        and the reason for cleanup.

        Args:
            state: Current projection state.
            event: WorktreeDeleted event with deletion details.

        Returns:
            Dict[str, Any]: New state with deletion information.

        Expected event.event_data fields:
        - reason: Reason for deletion ("merged", "failed", "manual")
        """
        pass

    @abstractmethod
    def apply_tests_started(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply TestsStarted event to the state.

        Called when test execution begins for a feature or test file.
        Records the start of test execution for tracking purposes.

        Args:
            state: Current projection state.
            event: TestsStarted event with test execution details.

        Returns:
            Dict[str, Any]: New state with test execution tracking.

        Expected event.event_data fields:
        - test_file: Path to the test file being executed
        - feature: Associated feature name (optional)
        """
        pass

    @abstractmethod
    def apply_tests_passed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply TestsPassed event to the state.

        Called when tests complete successfully. Records test success metrics
        and timing information.

        Args:
            state: Current projection state.
            event: TestsPassed event with test results.

        Returns:
            Dict[str, Any]: New state with successful test results.

        Expected event.event_data fields:
        - test_file: Path to the test file that passed
        - feature: Associated feature name (optional)
        - count: Number of tests that passed (optional)
        - duration_ms: Test execution time in milliseconds (optional)
        """
        pass

    @abstractmethod
    def apply_tests_failed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply TestsFailed event to the state.

        Called when tests fail during execution. Records test failure details
        and specific failure information for debugging.

        Args:
            state: Current projection state.
            event: TestsFailed event with failure details.

        Returns:
            Dict[str, Any]: New state with test failure information.

        Expected event.event_data fields:
        - test_file: Path to the test file that failed
        - feature: Associated feature name (optional)
        - failures: List of specific test failures (optional)
        """
        pass

    @abstractmethod
    def apply_commit_created(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply CommitCreated event to the state.

        Called when a git commit is successfully created. Records commit
        information including SHA, message, and affected files.

        Args:
            state: Current projection state.
            event: CommitCreated event with commit details.

        Returns:
            Dict[str, Any]: New state with commit information.

        Expected event.event_data fields:
        - commit_sha: SHA hash of the created commit
        - message: Commit message
        - files: List of files included in the commit (optional)
        """
        pass

    @abstractmethod
    def apply_commit_failed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply CommitFailed event to the state.

        Called when a git commit attempt fails. Records the failure reason
        and context for debugging and retry logic.

        Args:
            state: Current projection state.
            event: CommitFailed event with failure details.

        Returns:
            Dict[str, Any]: New state with commit failure information.

        Expected event.event_data fields:
        - error: Error message describing why the commit failed
        - files: List of files that were being committed (optional)
        """
        pass