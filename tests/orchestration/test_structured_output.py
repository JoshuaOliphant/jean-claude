# ABOUTME: Tests for structured output in the initializer agent
# ABOUTME: Verifies the initializer uses output_format for guaranteed JSON responses

"""Tests for structured output in the two-agent initializer.

Ensures the initializer agent uses output_format to get SDK-enforced
structured responses, eliminating fragile JSON parsing.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from jean_claude.core.agent import ExecutionResult
from jean_claude.orchestration.two_agent import (
    run_initializer,
    FEATURE_LIST_SCHEMA,
)


class TestInitializerStructuredOutput:
    """Tests for structured output in run_initializer."""

    @pytest.mark.asyncio
    async def test_initializer_sets_output_format(self, project_root: Path):
        """Initializer should pass output_format to the PromptRequest."""
        result = ExecutionResult(
            success=True,
            output='{"features": [{"name": "test", "description": "Test feature", "test_file": "tests/test.py"}]}',
            session_id="test",
            cost_usd=0.01,
            duration_ms=1000,
        )

        with patch(
            "jean_claude.orchestration.two_agent.execute_prompt_async",
            new_callable=AsyncMock,
        ) as mock_execute:
            mock_execute.return_value = result

            await run_initializer(
                description="Test task",
                project_root=project_root,
                workflow_id="test-structured",
            )

            # Verify the PromptRequest had output_format set
            call_args = mock_execute.call_args
            request = call_args[0][0]
            assert request.output_format is not None
            assert request.output_format["type"] == "json_schema"

    def test_feature_list_schema_is_valid(self):
        """The exported schema should have the expected structure."""
        assert "type" in FEATURE_LIST_SCHEMA
        assert FEATURE_LIST_SCHEMA["type"] == "json_schema"
        schema = FEATURE_LIST_SCHEMA["schema"]
        assert "features" in schema["properties"]
        assert schema["required"] == ["features"]

    @pytest.mark.asyncio
    async def test_initializer_parses_clean_json(self, project_root: Path):
        """With structured output, response is clean JSON — no markdown extraction needed."""
        # Structured output guarantees clean JSON, no code blocks
        clean_json = '{"features": [{"name": "auth", "description": "Add authentication", "test_file": "tests/test_auth.py"}]}'

        result = ExecutionResult(
            success=True,
            output=clean_json,
            session_id="test",
            cost_usd=0.01,
            duration_ms=1000,
        )

        with patch(
            "jean_claude.orchestration.two_agent.execute_prompt_async",
            new_callable=AsyncMock,
        ) as mock_execute:
            mock_execute.return_value = result

            state = await run_initializer(
                description="Add auth",
                project_root=project_root,
                workflow_id="test-clean",
            )

            assert len(state.features) == 1
            assert state.features[0].name == "auth"
