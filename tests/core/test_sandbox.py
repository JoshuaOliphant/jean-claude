# ABOUTME: Tests for SDK sandbox mode configuration and passthrough
# ABOUTME: Verifies sandbox settings flow from PromptRequest to ClaudeAgentOptions

"""Tests for sandbox mode feature.

Ensures SandboxSettings are properly configured per workflow type
and wired through to ClaudeAgentOptions.
"""

from unittest.mock import AsyncMock, patch

import pytest

from jean_claude.core.agent import PromptRequest
from jean_claude.core.sandbox import get_sandbox_settings, SANDBOX_CONFIGS


class TestGetSandboxSettings:
    """Tests for get_sandbox_settings function."""

    def test_returns_none_when_disabled(self):
        """When sandbox_enabled=False, returns None."""
        result = get_sandbox_settings("development", enabled=False)
        assert result is None

    def test_development_workflow(self):
        """Development workflow gets sandbox with docker/git excluded."""
        result = get_sandbox_settings("development", enabled=True)
        assert result is not None
        assert result["enabled"] is True
        assert result["autoAllowBashIfSandboxed"] is True
        assert "docker" in result["excludedCommands"]
        assert "git" in result["excludedCommands"]

    def test_readonly_workflow(self):
        """Readonly workflow gets stricter sandbox."""
        result = get_sandbox_settings("readonly", enabled=True)
        assert result is not None
        assert result["enabled"] is True
        assert result["allowUnsandboxedCommands"] is False

    def test_testing_workflow(self):
        """Testing workflow gets sandbox with docker/git excluded."""
        result = get_sandbox_settings("testing", enabled=True)
        assert result is not None
        assert result["enabled"] is True
        assert "docker" in result["excludedCommands"]

    def test_unknown_workflow_falls_back_to_development(self):
        """Unknown workflow type falls back to development config."""
        result = get_sandbox_settings("unknown", enabled=True)
        assert result is not None
        assert result["enabled"] is True

    def test_sandbox_configs_has_all_workflow_types(self):
        """All expected workflow types are configured."""
        assert "readonly" in SANDBOX_CONFIGS
        assert "development" in SANDBOX_CONFIGS
        assert "testing" in SANDBOX_CONFIGS


class TestPromptRequestSandbox:
    """Tests for sandbox_enabled on PromptRequest."""

    def test_sandbox_enabled_by_default(self):
        """Sandbox should be enabled by default."""
        request = PromptRequest(prompt="test")
        assert request.sandbox_enabled is True

    def test_sandbox_can_be_disabled(self):
        """Sandbox can be explicitly disabled."""
        request = PromptRequest(prompt="test", sandbox_enabled=False)
        assert request.sandbox_enabled is False


class TestSandboxPassthrough:
    """Tests that sandbox flows through to ClaudeAgentOptions."""

    @pytest.mark.asyncio
    @patch("jean_claude.core.sdk_executor.query")
    async def test_sandbox_passed_to_sdk_options(self, mock_query):
        """Sandbox settings should be passed to ClaudeAgentOptions."""
        from jean_claude.core.sdk_executor import _execute_prompt_async

        mock_query.return_value = AsyncMock()
        mock_query.return_value.__aiter__ = AsyncMock(return_value=iter([]))

        request = PromptRequest(
            prompt="test",
            sandbox_enabled=True,
            workflow_type="development",
        )

        await _execute_prompt_async(request)

        mock_query.assert_called_once()
        call_kwargs = mock_query.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options.sandbox is not None
        assert options.sandbox["enabled"] is True

    @pytest.mark.asyncio
    @patch("jean_claude.core.sdk_executor.query")
    async def test_sandbox_disabled_passes_none(self, mock_query):
        """When sandbox disabled, options.sandbox should be None."""
        from jean_claude.core.sdk_executor import _execute_prompt_async

        mock_query.return_value = AsyncMock()
        mock_query.return_value.__aiter__ = AsyncMock(return_value=iter([]))

        request = PromptRequest(
            prompt="test",
            sandbox_enabled=False,
        )

        await _execute_prompt_async(request)

        mock_query.assert_called_once()
        call_kwargs = mock_query.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options.sandbox is None
