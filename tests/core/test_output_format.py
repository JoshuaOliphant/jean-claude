# ABOUTME: Tests for output_format support in PromptRequest and SDK options
# ABOUTME: Verifies structured output schemas flow through to ClaudeAgentOptions

"""Tests for output_format feature.

Ensures output_format is properly wired from PromptRequest through
to ClaudeAgentOptions for SDK-enforced structured output.
"""

from unittest.mock import AsyncMock, patch

import pytest

from jean_claude.core.agent import PromptRequest


class TestPromptRequestOutputFormat:
    """Tests for output_format on PromptRequest."""

    def test_default_output_format_is_none(self):
        """Output format should be None by default (freeform text)."""
        request = PromptRequest(prompt="test")
        assert request.output_format is None

    def test_output_format_accepts_json_schema(self):
        """Output format should accept a JSON schema dict."""
        schema = {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "features": {
                        "type": "array",
                        "items": {"type": "object"},
                    }
                },
                "required": ["features"],
            },
        }
        request = PromptRequest(prompt="test", output_format=schema)
        assert request.output_format == schema
        assert request.output_format["type"] == "json_schema"


class TestOutputFormatPassthrough:
    """Tests that output_format flows through to ClaudeAgentOptions."""

    @pytest.mark.asyncio
    @patch("jean_claude.core.sdk_executor.query")
    async def test_output_format_passed_to_sdk_options(self, mock_query):
        """output_format should be passed through to ClaudeAgentOptions."""
        from jean_claude.core.sdk_executor import _execute_prompt_async

        mock_query.return_value = AsyncMock()
        mock_query.return_value.__aiter__ = AsyncMock(return_value=iter([]))

        schema = {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {"features": {"type": "array"}},
                "required": ["features"],
            },
        }

        request = PromptRequest(
            prompt="test",
            output_format=schema,
            enable_security_hooks=False,
        )

        await _execute_prompt_async(request)

        mock_query.assert_called_once()
        call_kwargs = mock_query.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options.output_format == schema

    @pytest.mark.asyncio
    @patch("jean_claude.core.sdk_executor.query")
    async def test_no_output_format_passes_none(self, mock_query):
        """When no output_format set, it should be None on options."""
        from jean_claude.core.sdk_executor import _execute_prompt_async

        mock_query.return_value = AsyncMock()
        mock_query.return_value.__aiter__ = AsyncMock(return_value=iter([]))

        request = PromptRequest(prompt="test", enable_security_hooks=False)
        await _execute_prompt_async(request)

        mock_query.assert_called_once()
        call_kwargs = mock_query.call_args
        options = call_kwargs.kwargs.get("options") or call_kwargs[1].get("options")
        assert options.output_format is None
