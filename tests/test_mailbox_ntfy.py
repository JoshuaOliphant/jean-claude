# ABOUTME: Tests for ntfy.sh notification functions in mailbox_tools
# ABOUTME: Tests escalate_to_human, poll_ntfy_responses, process_ntfy_responses

"""Tests for ntfy.sh notification functionality in mailbox_tools.

This module tests the external notification capabilities:
- escalate_to_human: Send push notifications via ntfy.sh
- poll_ntfy_responses: Poll for responses from ntfy.sh
- process_ntfy_responses: Process and route ntfy responses
- _send_ntfy_notification: Internal notification sending
"""

import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import urllib.error

import pytest

from jean_claude.tools.mailbox_tools import (
    escalate_to_human,
    poll_ntfy_responses,
    process_ntfy_responses,
    _send_ntfy_notification,
    set_workflow_context,
)
from jean_claude.core.state import WorkflowState


class TestSendNtfyNotification:
    """Tests for _send_ntfy_notification internal function."""

    def test_sends_notification_successfully(self):
        """Test that notification is sent via HTTP POST to ntfy.sh."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"id": "msg123"}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch('jean_claude.tools.mailbox_tools.urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            with patch.dict(os.environ, {'JEAN_CLAUDE_NTFY_TOPIC': 'test_topic'}):
                _send_ntfy_notification(
                    title="Test Title",
                    message="Test message body",
                    debug=False
                )

                # Verify urlopen was called
                mock_urlopen.assert_called_once()
                call_args = mock_urlopen.call_args
                request = call_args[0][0]

                # Verify request structure
                assert 'ntfy.sh' in request.full_url
                assert request.method == 'POST'

    def test_handles_missing_topic_gracefully(self):
        """Test that missing JEAN_CLAUDE_NTFY_TOPIC is handled."""
        # Clear the env var
        env_without_topic = {k: v for k, v in os.environ.items() if k != 'JEAN_CLAUDE_NTFY_TOPIC'}

        with patch.dict(os.environ, env_without_topic, clear=True):
            # Should not raise - just returns early
            _send_ntfy_notification(
                title="Test",
                message="Message",
                debug=False
            )

    def test_handles_network_error_gracefully(self):
        """Test that network errors are handled gracefully."""
        with patch('jean_claude.tools.mailbox_tools.urllib.request.urlopen',
                   side_effect=urllib.error.URLError("Network error")):
            with patch.dict(os.environ, {'JEAN_CLAUDE_NTFY_TOPIC': 'test_topic'}):
                # Should not raise, should handle gracefully
                _send_ntfy_notification(
                    title="Test",
                    message="Message",
                    debug=False
                )

    def test_includes_priority_in_notification(self):
        """Test that priority is included in ntfy notification."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch('jean_claude.tools.mailbox_tools.urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            with patch.dict(os.environ, {'JEAN_CLAUDE_NTFY_TOPIC': 'test_topic'}):
                _send_ntfy_notification(
                    title="Urgent Issue",
                    message="Critical bug found",
                    priority=5,  # Max priority
                    debug=False
                )

                mock_urlopen.assert_called_once()
                call_args = mock_urlopen.call_args
                request = call_args[0][0]
                # Priority should be in headers
                headers = {k.lower(): v for k, v in request.headers.items()}
                assert 'priority' in headers


class TestEscalateToHuman:
    """Tests for escalate_to_human function."""

    def test_escalate_sends_ntfy_notification(self):
        """Test that escalate_to_human sends a ntfy notification."""
        with patch('jean_claude.tools.mailbox_tools._send_ntfy_notification') as mock_send:
            with patch('jean_claude.tools.mailbox_tools._send_desktop_notification'):
                escalate_to_human(
                    title="Need Help",
                    message="I'm stuck on implementing auth",
                    priority=4
                )

                mock_send.assert_called_once()
                call_kwargs = mock_send.call_args[1]
                # Title should include project name prefix
                assert "Need Help" in call_kwargs.get('title', '') or "Need Help" in str(mock_send.call_args)

    def test_escalate_includes_project_name_in_title(self):
        """Test that project name is included in notification title."""
        with patch('jean_claude.tools.mailbox_tools._send_ntfy_notification') as mock_send:
            with patch('jean_claude.tools.mailbox_tools._send_desktop_notification'):
                escalate_to_human(
                    title="Question",
                    message="What auth method?",
                    project_name="my-project"
                )

                mock_send.assert_called_once()
                call_kwargs = mock_send.call_args[1]

                # Check title includes project name
                title = call_kwargs.get('title', '')
                assert "my-project" in title


class TestPollNtfyResponses:
    """Tests for poll_ntfy_responses function."""

    def test_poll_returns_empty_when_no_topic(self):
        """Test that polling returns empty list when no topic configured."""
        # Clear the env var
        env_without_topic = {k: v for k, v in os.environ.items()
                           if k != 'JEAN_CLAUDE_NTFY_RESPONSE_TOPIC'}

        with patch.dict(os.environ, env_without_topic, clear=True):
            result = poll_ntfy_responses()
            assert result == []

    def test_poll_returns_empty_when_no_responses(self):
        """Test that polling returns empty list when no responses available."""
        mock_response = MagicMock()
        mock_response.read.return_value = b''
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch('jean_claude.tools.mailbox_tools.urllib.request.urlopen', return_value=mock_response):
            with patch.dict(os.environ, {'JEAN_CLAUDE_NTFY_RESPONSE_TOPIC': 'responses_topic'}):
                result = poll_ntfy_responses()
                assert result == []

    def test_poll_handles_network_error_gracefully(self):
        """Test that network errors during polling are handled."""
        with patch('jean_claude.tools.mailbox_tools.urllib.request.urlopen',
                   side_effect=urllib.error.URLError("Timeout")):
            with patch.dict(os.environ, {'JEAN_CLAUDE_NTFY_RESPONSE_TOPIC': 'responses_topic'}):
                result = poll_ntfy_responses()
                # Should return empty list on error
                assert result == []


class TestProcessNtfyResponses:
    """Tests for process_ntfy_responses function."""

    def test_process_returns_zero_when_no_responses(self, tmp_path):
        """Test that 0 is returned when no responses available."""
        # Create agents dir structure
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True)

        with patch('jean_claude.tools.mailbox_tools.poll_ntfy_responses', return_value=[]):
            result = process_ntfy_responses(tmp_path)
            assert result == 0

    def test_process_writes_responses_to_workflow_outbox(self, tmp_path):
        """Test that responses are written to correct workflow mailbox."""
        # Create agents dir structure
        workflow_id = "abc123"
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True)

        mock_responses = [
            {"workflow_id": workflow_id, "response": "Yes, proceed", "timestamp": "2024-01-01T12:00:00Z"},
        ]

        with patch('jean_claude.tools.mailbox_tools.poll_ntfy_responses', return_value=mock_responses):
            result = process_ntfy_responses(tmp_path)

            # Should process 1 response
            assert result == 1

            # Check mailbox/outbox.jsonl was created with message
            # Path is: agents/{workflow_id}/mailbox/outbox.jsonl
            outbox_path = agents_dir / workflow_id / "mailbox" / "outbox.jsonl"
            assert outbox_path.exists()

            # Verify message content
            content = outbox_path.read_text().strip()
            message_data = json.loads(content)
            assert message_data["body"] == "Yes, proceed"
            assert message_data["from_agent"] == "user"

    def test_process_creates_mailbox_for_any_workflow_id(self, tmp_path):
        """Test that responses create mailbox even for non-existing workflows."""
        # Create agents dir but no pre-existing workflows
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True)

        mock_responses = [
            {"workflow_id": "new-workflow", "response": "Response text", "timestamp": "2024-01-01T12:00:00Z"},
        ]

        with patch('jean_claude.tools.mailbox_tools.poll_ntfy_responses', return_value=mock_responses):
            result = process_ntfy_responses(tmp_path)

            # Should process the response (creates mailbox on demand)
            assert result == 1

            # Mailbox/outbox.jsonl should be created
            outbox_path = agents_dir / "new-workflow" / "mailbox" / "outbox.jsonl"
            assert outbox_path.exists()


class TestNtfyIntegration:
    """Integration tests for ntfy functionality."""

    def test_full_escalation_flow(self, tmp_path):
        """Test complete escalation and response flow."""
        workflow_id = "integration-test"
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True)

        # Mock the ntfy and desktop notifications
        with patch('jean_claude.tools.mailbox_tools._send_ntfy_notification') as mock_ntfy:
            with patch('jean_claude.tools.mailbox_tools._send_desktop_notification'):
                # Send escalation
                escalate_to_human(
                    title="Architecture Decision",
                    message="Should I use Redis or Memcached?",
                    project_name="my-api"
                )

                mock_ntfy.assert_called_once()

        # Mock response polling and process
        mock_responses = [
            {"workflow_id": workflow_id, "response": "Use Redis for persistence", "timestamp": "2024-01-01T12:00:00Z"}
        ]

        with patch('jean_claude.tools.mailbox_tools.poll_ntfy_responses', return_value=mock_responses):
            result = process_ntfy_responses(tmp_path)
            assert result == 1

            # Verify response was written to mailbox/outbox.jsonl
            outbox_path = agents_dir / workflow_id / "mailbox" / "outbox.jsonl"
            assert outbox_path.exists()
            content = outbox_path.read_text()
            assert "Use Redis for persistence" in content
