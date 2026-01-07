# ABOUTME: Shared pytest fixtures for Jean Claude test suite
# ABOUTME: Provides common fixtures for CliRunner, mocks, and test data

"""Shared pytest fixtures for Jean Claude tests.

MOCKING ASYNC FUNCTIONS:
- Use `Mock` for sync functions (e.g., fetch_beads_task, update_beads_status)
- Use `Mock` for mocking the result of async functions called via anyio.run()
- Use `AsyncMock` only when directly testing async code with pytest.mark.asyncio
- The anyio.run() wrapper handles the async context, so we mock its return value
"""

from pathlib import Path
from typing import Callable, Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, BeadsTaskPriority, BeadsTaskType
from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.state import WorkflowState


# =============================================================================
# CLI Testing Fixtures
# =============================================================================


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a reusable CliRunner instance."""
    return CliRunner()


@pytest.fixture
def isolated_cli_runner(cli_runner: CliRunner, tmp_path: Path) -> Generator[CliRunner, None, None]:
    """Provide a CliRunner with isolated filesystem using pytest's tmp_path.

    Using tmp_path instead of isolated_filesystem() is faster because:
    - tmp_path is managed by pytest and can be reused
    - No need to change working directory
    """
    with cli_runner.isolated_filesystem(temp_dir=tmp_path):
        yield cli_runner


# =============================================================================
# Beads Task Fixtures
# =============================================================================


@pytest.fixture
def mock_beads_task() -> BeadsTask:
    """Provide a standard mock BeadsTask for testing."""
    return BeadsTask(
        id="test-task.1",
        title="Test Task",
        description="A test task for unit testing",
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        status=BeadsTaskStatus.OPEN
    )


@pytest.fixture
def mock_beads_task_factory():
    """Factory fixture for creating BeadsTask with custom values."""
    def _create_task(
        id: str = "test-task.1",
        title: str = "Test Task",
        description: str = "A test task",
        acceptance_criteria: list[str] | None = None,
        status: str | BeadsTaskStatus = BeadsTaskStatus.OPEN,
        priority: str | BeadsTaskPriority | None = None,
        task_type: str | BeadsTaskType | None = None,
        created_at=None,
        updated_at=None,
    ) -> BeadsTask:
        # Convert string to enum if needed
        if isinstance(status, str):
            status = BeadsTaskStatus(status)

        # Build kwargs dict
        kwargs = {
            "id": id,
            "title": title,
            "description": description,
            "acceptance_criteria": acceptance_criteria or [],
            "status": status,
            "priority": priority,
            "task_type": task_type,
        }

        # Only add created_at/updated_at if provided
        if created_at is not None:
            kwargs["created_at"] = created_at
        if updated_at is not None:
            kwargs["updated_at"] = updated_at

        return BeadsTask(**kwargs)
    return _create_task


# =============================================================================
# WorkflowState Fixtures
# =============================================================================


@pytest.fixture
def mock_workflow_state() -> WorkflowState:
    """Provide a standard mock WorkflowState for testing."""
    return WorkflowState(
        workflow_id="test-workflow-123",
        workflow_name="Test Workflow",
        workflow_type="two-agent",
    )


@pytest.fixture
def mock_workflow_state_instance() -> Mock:
    """Provide a basic mock WorkflowState instance.

    Use this when you need to mock a WorkflowState that's being patched
    in the work command. This fixture provides a clean mock with default
    behavior for common methods.
    """
    mock_state = Mock(spec=WorkflowState)
    mock_state.workflow_id = "test-workflow-123"
    mock_state.workflow_name = "Test Workflow"
    mock_state.workflow_type = "two-agent"
    mock_state.phase = "planning"
    mock_state.features = []
    mock_state.current_feature_index = 0
    mock_state.is_complete.return_value = False
    mock_state.is_failed.return_value = False
    mock_state.get_summary.return_value = {
        'completed_features': 0,
        'total_features': 0,
        'failed_features': 0,
        'progress_percentage': 0.0,
        'iteration_count': 0,
        'total_cost_usd': 0.0,
        'total_duration_ms': 0
    }
    return mock_state


@pytest.fixture
def completed_workflow_state() -> Mock:
    """Provide a mock WorkflowState that reports as complete.

    Includes phase and save attributes required by work.py phase transitions.
    """
    state = Mock(spec=WorkflowState)
    state.is_complete.return_value = True
    state.is_failed.return_value = False
    state.workflow_id = "test-workflow-123"
    state.phase = "implementing"
    state.save = Mock()
    return state


@pytest.fixture
def failed_workflow_state() -> Mock:
    """Provide a mock WorkflowState that reports as failed.

    Includes phase and save attributes required by work.py phase transitions.
    """
    state = Mock(spec=WorkflowState)
    state.is_complete.return_value = False
    state.is_failed.return_value = True
    state.workflow_id = "test-workflow-123"
    state.phase = "implementing"
    state.save = Mock()
    return state


@pytest.fixture
def workflow_state_factory():
    """Factory fixture for creating WorkflowState with custom values."""
    def _create_state(
        workflow_id: str = "test-workflow-123",
        workflow_name: str = "Test Workflow",
        workflow_type: str = "feature",
        beads_task_id: str = None,
        beads_task_title: str = None,
        phase: str = None,
        max_iterations: int = 10,
        updated_at=None,
        total_cost_usd: float = None,
        total_duration_ms: int = None,
        save_to_path=None,
    ) -> WorkflowState:
        kwargs = {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "workflow_type": workflow_type,
        }

        # Add optional parameters only if provided
        if beads_task_id is not None:
            kwargs["beads_task_id"] = beads_task_id
        if beads_task_title is not None:
            kwargs["beads_task_title"] = beads_task_title
        if phase is not None:
            kwargs["phase"] = phase
        if max_iterations != 10:
            kwargs["max_iterations"] = max_iterations
        if updated_at is not None:
            kwargs["updated_at"] = updated_at
        if total_cost_usd is not None:
            kwargs["total_cost_usd"] = total_cost_usd
        if total_duration_ms is not None:
            kwargs["total_duration_ms"] = total_duration_ms

        state = WorkflowState(**kwargs)

        if save_to_path is not None:
            state.save(save_to_path)

        return state

    return _create_state


# =============================================================================
# Work Command Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_fetch_beads_task(mock_beads_task: BeadsTask):
    """Mock fetch_beads_task to return the mock task."""
    with patch('jean_claude.cli.commands.work.fetch_beads_task', return_value=mock_beads_task) as mock:
        yield mock


@pytest.fixture
def mock_generate_spec():
    """Mock generate_spec_from_beads to return simple spec content."""
    with patch('jean_claude.cli.commands.work.generate_spec_from_beads', return_value="# Test Spec\n\nTest content") as mock:
        yield mock


@pytest.fixture
def mock_update_beads_status():
    """Mock update_beads_status to do nothing."""
    with patch('jean_claude.cli.commands.work.update_beads_status') as mock:
        yield mock


@pytest.fixture
def mock_close_beads_task():
    """Mock close_beads_task to do nothing."""
    with patch('jean_claude.cli.commands.work.close_beads_task') as mock:
        yield mock


@pytest.fixture
def mock_anyio_run_success(completed_workflow_state: Mock):
    """Mock anyio.run to return a successful workflow state."""
    with patch('jean_claude.cli.commands.work.anyio.run', return_value=completed_workflow_state) as mock:
        yield mock


@pytest.fixture
def mock_anyio_run_failure(failed_workflow_state: Mock):
    """Mock anyio.run to return a failed workflow state."""
    with patch('jean_claude.cli.commands.work.anyio.run', return_value=failed_workflow_state) as mock:
        yield mock


@pytest.fixture
def mock_event_logger():
    """Mock EventLogger and return both the class and instance mocks."""
    with patch('jean_claude.cli.commands.work.EventLogger') as mock_class:
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        yield {"class": mock_class, "instance": mock_instance}


@pytest.fixture
def mock_workflow_state_class(mock_workflow_state_instance: Mock):
    """Mock the WorkflowState class in the work command module.

    Returns a dict with:
    - 'class': The mocked WorkflowState class
    - 'instance': The instance that will be returned when the class is instantiated
    """
    with patch('jean_claude.cli.commands.work.WorkflowState') as mock_class:
        mock_class.return_value = mock_workflow_state_instance
        yield {"class": mock_class, "instance": mock_workflow_state_instance}


@pytest.fixture
def mock_task_validator():
    """Mock TaskValidator to return clean validation result."""
    from jean_claude.core.task_validator import ValidationResult
    mock_result = ValidationResult(is_valid=True, warnings=[], errors=[])
    with patch('jean_claude.cli.commands.work.TaskValidator') as mock_class:
        mock_instance = Mock()
        mock_instance.validate.return_value = mock_result
        mock_class.return_value = mock_instance
        yield {"class": mock_class, "instance": mock_instance, "result": mock_result}


# =============================================================================
# Combined Work Command Fixtures
# =============================================================================


@pytest.fixture
def work_command_mocks(
    mock_fetch_beads_task,
    mock_generate_spec,
    mock_update_beads_status,
    mock_close_beads_task,
    mock_anyio_run_success,
    mock_event_logger,
    mock_workflow_state_class,
    mock_task_validator,
):
    """Combine all work command mocks for integration tests.

    Usage:
        def test_work_does_something(isolated_cli_runner, work_command_mocks):
            result = isolated_cli_runner.invoke(work, ["task-123"])
            assert result.exit_code == 0

            # Access individual mocks
            work_command_mocks["event_logger"]["instance"].emit.assert_called()
            work_command_mocks["workflow_state"]["class"].assert_called()
    """
    return {
        "fetch_beads_task": mock_fetch_beads_task,
        "generate_spec": mock_generate_spec,
        "update_status": mock_update_beads_status,
        "close_task": mock_close_beads_task,
        "anyio_run": mock_anyio_run_success,
        "event_logger": mock_event_logger,
        "workflow_state": mock_workflow_state_class,
        "task_validator": mock_task_validator,
    }


# =============================================================================
# Subprocess Mock Fixtures (for beads.py tests)
# =============================================================================


@pytest.fixture
def mock_subprocess_success():
    """Mock subprocess.run to return success."""
    with patch('jean_claude.core.beads.subprocess.run') as mock:
        mock.return_value = Mock(
            returncode=0,
            stdout='{"id": "test.1", "title": "Test", "description": "Desc", "acceptance_criteria": [], "status": "open"}',
            stderr=""
        )
        yield mock


@pytest.fixture
def mock_subprocess_failure():
    """Mock subprocess.run to return failure."""
    with patch('jean_claude.core.beads.subprocess.run') as mock:
        mock.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error: Task not found"
        )
        yield mock


# =============================================================================
# Message Fixtures
# =============================================================================


@pytest.fixture
def sample_message() -> Message:
    """Provide a standard Message for testing."""
    return Message(
        from_agent="agent-1",
        to_agent="agent-2",
        type="test",
        subject="Test Message",
        body="This is a test message body."
    )


@pytest.fixture
def urgent_message() -> Message:
    """Provide an urgent priority Message for testing."""
    return Message(
        from_agent="agent-1",
        to_agent="coordinator",
        type="help_request",
        subject="Urgent Help Needed",
        body="I need immediate assistance.",
        priority=MessagePriority.URGENT,
        awaiting_response=True
    )


@pytest.fixture
def message_factory() -> Callable[..., Message]:
    """Factory fixture for creating Message with custom values.

    Usage:
        def test_something(message_factory):
            msg = message_factory(priority=MessagePriority.URGENT)
    """
    def _create_message(
        from_agent: str = "agent-1",
        to_agent: str = "agent-2",
        type: str = "test",
        subject: str = "Test Subject",
        body: str = "Test body content",
        priority: MessagePriority = MessagePriority.NORMAL,
        awaiting_response: bool = False,
        id: str | None = None,
        correlation_id: str | None = None,
    ) -> Message:
        kwargs = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "type": type,
            "subject": subject,
            "body": body,
            "priority": priority,
            "awaiting_response": awaiting_response,
        }
        # Only add id if provided (otherwise let Message auto-generate)
        if id is not None:
            kwargs["id"] = id
        # Only add correlation_id if provided
        if correlation_id is not None:
            kwargs["correlation_id"] = correlation_id
        return Message(**kwargs)
    return _create_message


# =============================================================================
# Integration Test Helpers
# =============================================================================


def query_events(project_root: Path, event_type: str = None, **filters):
    """Helper to query events from .jc/events.db with optional filters.

    Reduces 15-line boilerplate used in 15+ integration tests.

    Args:
        project_root: Project root directory
        event_type: Filter by event type (optional)
        **filters: Additional WHERE clause filters (e.g., workflow_id='abc')

    Returns:
        List[dict]: Query results as dicts

    Example:
        events = query_events(project_root, event_type="workflow.started")
        events = query_events(project_root, workflow_id="test-123")
    """
    import sqlite3

    db_path = project_root / ".jc" / "events.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM events"
    conditions = []
    params = []

    if event_type:
        conditions.append("event_type = ?")
        params.append(event_type)

    for key, value in filters.items():
        conditions.append(f"{key} = ?")
        params.append(value)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor = conn.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results


@pytest.fixture
def notes_api_with_logger(tmp_path):
    """Fixture providing Notes API with EventLogger configured.

    Used across 25+ notes integration tests.

    Returns:
        tuple: (Notes instance, EventLogger instance, workflow_id, project_root)

    Example:
        def test_notes(notes_api_with_logger):
            notes, event_logger, workflow_id, project_root = notes_api_with_logger
            notes.add_observation(..., event_logger=event_logger)
    """
    from jean_claude.core.notes_api import Notes
    from jean_claude.core.events import EventLogger
    import uuid

    project_root = tmp_path / "project"
    project_root.mkdir()

    workflow_id = str(uuid.uuid4())[:8]

    event_logger = EventLogger(project_root)
    notes = Notes(
        workflow_id=workflow_id,
        base_dir=project_root / "agents"
    )

    return notes, event_logger, workflow_id, project_root


@pytest.fixture
def event_store_with_logger(tmp_path):
    """Fixture providing EventStore with initialized database.

    Common pattern across event-related tests.

    Returns:
        tuple: (EventStore instance, project_root)

    Example:
        def test_events(event_store_with_logger):
            event_store, project_root = event_store_with_logger
            event_store.log_event(...)
    """
    from jean_claude.core.event_store import EventStore

    project_root = tmp_path / "project"
    project_root.mkdir()

    event_store = EventStore(project_root)
    event_store.initialize()

    return event_store, project_root
