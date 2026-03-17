# ABOUTME: Tests for max_budget_usd support in PromptRequest and SDK options
# ABOUTME: Verifies budget limits flow from config through to ClaudeAgentOptions

"""Tests for budget limit feature.

Ensures max_budget_usd is properly wired from PromptRequest through
to ClaudeAgentOptions, and that WorkflowsConfig supports project-level defaults.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from jean_claude.core.agent import PromptRequest
from jean_claude.config.models import WorkflowsConfig, ProjectConfig


class TestPromptRequestBudget:
    """Tests for max_budget_usd on PromptRequest."""

    def test_default_budget_is_none(self):
        """Budget should be None by default (no limit)."""
        request = PromptRequest(prompt="test")
        assert request.max_budget_usd is None

    def test_budget_can_be_set(self):
        """Budget should accept a float value."""
        request = PromptRequest(prompt="test", max_budget_usd=5.0)
        assert request.max_budget_usd == 5.0

    def test_budget_zero_is_valid(self):
        """Zero budget should be accepted (effectively no work)."""
        request = PromptRequest(prompt="test", max_budget_usd=0.0)
        assert request.max_budget_usd == 0.0


class TestWorkflowsConfigBudget:
    """Tests for max_budget_usd on WorkflowsConfig."""

    def test_default_budget_is_none(self):
        """Project config should have no budget by default."""
        config = WorkflowsConfig()
        assert config.max_budget_usd is None

    def test_budget_from_yaml(self, tmp_path):
        """Budget should load from .jc-project.yaml."""
        config_path = tmp_path / ".jc-project.yaml"
        config_path.write_text(
            "workflows:\n"
            "  default_model: sonnet\n"
            "  max_budget_usd: 10.0\n"
        )
        config = ProjectConfig.load(config_path)
        assert config.workflows.max_budget_usd == 10.0


class TestBudgetPassthrough:
    """Tests that budget flows through to ClaudeAgentOptions."""

    @pytest.mark.asyncio
    @patch("jean_claude.core.sdk_executor.query")
    async def test_budget_passed_to_sdk_options(self, mock_query):
        """max_budget_usd should be passed through to ClaudeAgentOptions."""
        from jean_claude.core.sdk_executor import _execute_prompt_async

        # Make query return empty (no messages)
        mock_query.return_value = AsyncMock()
        mock_query.return_value.__aiter__ = AsyncMock(return_value=iter([]))

        request = PromptRequest(
            prompt="test",
            max_budget_usd=5.0,
            sandbox_enabled=False,
        )

        await _execute_prompt_async(request)

        # Verify query was called and inspect the options
        mock_query.assert_called_once()
        call_kwargs = mock_query.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options.max_budget_usd == 5.0

    @pytest.mark.asyncio
    @patch("jean_claude.core.sdk_executor.query")
    async def test_no_budget_passes_none(self, mock_query):
        """When no budget set, max_budget_usd should not be set on options."""
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
        assert options.max_budget_usd is None
