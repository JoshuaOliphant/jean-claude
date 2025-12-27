# ABOUTME: Shared pytest fixtures for tests/core/ test suite
# ABOUTME: Provides common fixtures for BeadsTask, Message, subprocess mocks, and test data

"""Shared pytest fixtures for core module tests.

These fixtures are automatically available to all tests in tests/core/.
Import from the root conftest.py for fixtures that should be shared across
all test directories.

USAGE:
    def test_something(sample_message, mock_subprocess_success):
        # Fixtures are automatically injected
        pass

GUIDELINES:
    1. Use these fixtures instead of creating BeadsTask/Message inline
    2. Use mock_subprocess_* fixtures for subprocess.run mocking
    3. Add new fixtures here when a pattern is used 3+ times
"""

from datetime import datetime
from typing import Callable
from unittest.mock import Mock, patch

import pytest

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, BeadsTaskPriority, BeadsTaskType
from jean_claude.core.message import Message, MessagePriority


# =============================================================================
# BeadsTask Fixtures
# =============================================================================


@pytest.fixture
def sample_beads_task() -> BeadsTask:
    """Provide a fully-populated BeadsTask for testing."""
    return BeadsTask(
        id="test-task.1",
        title="Test Task Title",
        description="A comprehensive test task description for unit testing purposes.",
        acceptance_criteria=["Criterion 1", "Criterion 2", "Criterion 3"],
        status=BeadsTaskStatus.OPEN,
        priority=BeadsTaskPriority.MEDIUM,
        task_type=BeadsTaskType.FEATURE,
    )


@pytest.fixture
def minimal_beads_task() -> BeadsTask:
    """Provide a BeadsTask with only required fields."""
    return BeadsTask(
        id="minimal.1",
        title="Minimal Task",
        description="Minimal description",
        acceptance_criteria=[],
        status=BeadsTaskStatus.OPEN,
    )


@pytest.fixture
def beads_task_factory() -> Callable[..., BeadsTask]:
    """Factory fixture for creating BeadsTask with custom values.

    Usage:
        def test_something(beads_task_factory):
            task = beads_task_factory(id="custom-id", status="in_progress")
    """
    def _create_task(
        id: str = "factory-task.1",
        title: str = "Factory Task",
        description: str = "Created by factory fixture",
        acceptance_criteria: list[str] | None = None,
        status: str | BeadsTaskStatus = BeadsTaskStatus.OPEN,
        priority: str | BeadsTaskPriority | None = None,
        task_type: str | BeadsTaskType | None = None,
    ) -> BeadsTask:
        if isinstance(status, str):
            status = BeadsTaskStatus(status)
        return BeadsTask(
            id=id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria or [],
            status=status,
            priority=priority,
            task_type=task_type,
        )
    return _create_task


# =============================================================================
# Subprocess Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_subprocess_success():
    """Mock subprocess.run to return successful JSON response."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = '{"id": "test.1", "title": "Test", "description": "Desc", "acceptance_criteria": [], "status": "open"}'
    mock_result.stderr = ""

    with patch('jean_claude.core.beads.subprocess.run', return_value=mock_result) as mock:
        yield mock


@pytest.fixture
def mock_subprocess_failure():
    """Mock subprocess.run to return a failure."""
    mock_result = Mock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Command failed"

    with patch('jean_claude.core.beads.subprocess.run', return_value=mock_result) as mock:
        yield mock


@pytest.fixture
def mock_subprocess_factory():
    """Factory for creating custom subprocess mock responses.

    Usage:
        def test_something(mock_subprocess_factory):
            mock = mock_subprocess_factory(returncode=0, stdout='{"id": "x"}')
    """
    def _create_mock(returncode: int = 0, stdout: str = "", stderr: str = ""):
        mock_result = Mock()
        mock_result.returncode = returncode
        mock_result.stdout = stdout
        mock_result.stderr = stderr
        return patch('jean_claude.core.beads.subprocess.run', return_value=mock_result)
    return _create_mock


# =============================================================================
# JSON Response Fixtures
# =============================================================================


@pytest.fixture
def valid_beads_json() -> str:
    """Valid JSON response for a BeadsTask."""
    return '''{
        "id": "json-task.1",
        "title": "JSON Task",
        "description": "Task from JSON",
        "acceptance_criteria": ["AC1", "AC2"],
        "status": "open",
        "priority": 2,
        "issue_type": "feature"
    }'''


@pytest.fixture
def invalid_beads_json() -> str:
    """Invalid JSON (missing required fields)."""
    return '{"id": "incomplete"}'


@pytest.fixture
def malformed_json() -> str:
    """Malformed JSON that will fail parsing."""
    return '{not valid json}'


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
    ) -> Message:
        return Message(
            from_agent=from_agent,
            to_agent=to_agent,
            type=type,
            subject=subject,
            body=body,
            priority=priority,
            awaiting_response=awaiting_response,
        )
    return _create_message
