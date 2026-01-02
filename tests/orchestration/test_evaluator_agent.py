# ABOUTME: Tests for the AI evaluator agent
# ABOUTME: Tests parsing, helper functions, and evaluation logic

"""Tests for jean_claude.orchestration.evaluator_agent module."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from jean_claude.core.state import Feature, WorkflowState
from jean_claude.orchestration.evaluator_agent import (
    AgentEvaluation,
    _format_features_summary,
    _get_git_diff,
    _parse_evaluation_response,
    run_evaluator_agent,
)


class TestParseEvaluationResponse:
    """Tests for _parse_evaluation_response function."""

    def test_parse_valid_json(self):
        """Parse valid JSON response."""
        response = json.dumps({
            "overall_assessment": "Good implementation",
            "quality_rating": "good",
            "code_quality_notes": ["Clean code"],
            "test_quality_notes": ["Good coverage"],
            "strengths": ["Well structured"],
            "improvements": ["Add docstrings"],
            "potential_issues": [],
        })

        result = _parse_evaluation_response(response)

        assert result.overall_assessment == "Good implementation"
        assert result.quality_rating == "good"
        assert result.strengths == ["Well structured"]
        assert result.improvements == ["Add docstrings"]

    def test_parse_json_in_code_block(self):
        """Parse JSON wrapped in markdown code block."""
        response = """Here is my evaluation:

```json
{
    "overall_assessment": "Excellent work",
    "quality_rating": "excellent",
    "code_quality_notes": [],
    "test_quality_notes": [],
    "strengths": ["Fast"],
    "improvements": [],
    "potential_issues": []
}
```

That's my assessment."""

        result = _parse_evaluation_response(response)

        assert result.overall_assessment == "Excellent work"
        assert result.quality_rating == "excellent"
        assert result.strengths == ["Fast"]

    def test_parse_json_in_generic_code_block(self):
        """Parse JSON wrapped in generic code block."""
        response = """```
{
    "overall_assessment": "Needs work",
    "quality_rating": "needs_improvement",
    "code_quality_notes": [],
    "test_quality_notes": [],
    "strengths": [],
    "improvements": ["Refactor"],
    "potential_issues": ["Bug risk"]
}
```"""

        result = _parse_evaluation_response(response)

        assert result.quality_rating == "needs_improvement"
        assert result.improvements == ["Refactor"]
        assert result.potential_issues == ["Bug risk"]

    def test_parse_invalid_json(self):
        """Handle invalid JSON gracefully."""
        response = "This is not JSON at all"

        result = _parse_evaluation_response(response)

        assert "Could not parse" in result.overall_assessment
        assert result.quality_rating == "acceptable"
        assert result.raw_response == response

    def test_parse_partial_json(self):
        """Handle partial/incomplete JSON."""
        response = '{"overall_assessment": "Test"'  # Missing closing brace

        result = _parse_evaluation_response(response)

        assert "Could not parse" in result.overall_assessment
        assert result.raw_response == response

    def test_parse_missing_fields_uses_defaults(self):
        """Missing fields get default values."""
        response = json.dumps({
            "overall_assessment": "Minimal",
            "quality_rating": "acceptable",
        })

        result = _parse_evaluation_response(response)

        assert result.overall_assessment == "Minimal"
        assert result.code_quality_notes == []
        assert result.strengths == []


class TestFormatFeaturesSummary:
    """Tests for _format_features_summary function."""

    def test_format_empty_features(self):
        """Format empty feature list."""
        state = WorkflowState(
            workflow_id="test",
            workflow_name="Test",
            workflow_type="test",
        )

        result = _format_features_summary(state)

        assert result == "(no features defined)"

    def test_format_completed_features(self):
        """Format completed features."""
        state = WorkflowState(
            workflow_id="test",
            workflow_name="Test",
            workflow_type="test",
        )
        state.features = [
            Feature(
                name="Feature 1",
                description="First feature",
                status="completed",
                tests_passing=True,
            ),
            Feature(
                name="Feature 2",
                description="Second feature",
                status="completed",
                tests_passing=False,
            ),
        ]

        result = _format_features_summary(state)

        assert "[✓]" in result
        assert "Feature 1" in result
        assert "Feature 2" in result
        assert "tests passing" in result
        assert "tests not passing" in result

    def test_format_mixed_status_features(self):
        """Format features with various statuses."""
        state = WorkflowState(
            workflow_id="test",
            workflow_name="Test",
            workflow_type="test",
        )
        state.features = [
            Feature(name="Done", description="Completed", status="completed"),
            Feature(name="Failed", description="Failed", status="failed"),
            Feature(name="Working", description="In progress", status="in_progress"),
            Feature(name="Pending", description="Not started", status="not_started"),
        ]

        result = _format_features_summary(state)

        assert "[✓]" in result  # completed
        assert "[✗]" in result  # failed
        assert "[→]" in result  # in_progress
        assert "[○]" in result  # not_started


class TestGetGitDiff:
    """Tests for _get_git_diff function."""

    def test_get_diff_handles_missing_git(self, tmp_path: Path):
        """Handle missing git gracefully."""
        # tmp_path won't be a git repo
        result = _get_git_diff(tmp_path)

        # Should return an error message, not crash
        assert isinstance(result, str)

    @patch("subprocess.run")
    def test_get_diff_truncates_long_output(self, mock_run, tmp_path: Path):
        """Long diffs are truncated."""
        # Generate long diff output
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "\n".join([f"line {i}" for i in range(1000)])

        result = _get_git_diff(tmp_path, max_lines=100)

        assert "truncated" in result.lower()
        lines = result.split("\n")
        assert len(lines) <= 105  # 100 lines + truncation message

    @patch("subprocess.run")
    def test_get_diff_timeout_handling(self, mock_run, tmp_path: Path):
        """Handle git timeout gracefully."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("git", 30)

        result = _get_git_diff(tmp_path)

        assert "timed out" in result.lower()


class TestAgentEvaluationModel:
    """Tests for AgentEvaluation Pydantic model."""

    def test_create_minimal_evaluation(self):
        """Create evaluation with minimal fields."""
        eval_result = AgentEvaluation(
            overall_assessment="Test assessment",
            quality_rating="good",
        )

        assert eval_result.overall_assessment == "Test assessment"
        assert eval_result.quality_rating == "good"
        assert eval_result.strengths == []
        assert eval_result.improvements == []

    def test_create_full_evaluation(self):
        """Create evaluation with all fields."""
        eval_result = AgentEvaluation(
            overall_assessment="Complete assessment",
            quality_rating="excellent",
            code_quality_notes=["Clean", "Well-organized"],
            test_quality_notes=["Good coverage"],
            strengths=["Fast", "Reliable"],
            improvements=["Add docs"],
            potential_issues=["Edge case"],
            raw_response="raw output",
        )

        assert len(eval_result.code_quality_notes) == 2
        assert len(eval_result.strengths) == 2
        assert eval_result.raw_response == "raw output"

    def test_rating_values(self):
        """Verify different rating values work."""
        ratings = ["excellent", "good", "acceptable", "needs_improvement", "poor"]

        for rating in ratings:
            eval_result = AgentEvaluation(
                overall_assessment="Test",
                quality_rating=rating,
            )
            assert eval_result.quality_rating == rating


class TestRunEvaluatorAgent:
    """Tests for run_evaluator_agent function."""

    @pytest.fixture
    def sample_state(self) -> WorkflowState:
        """Create sample workflow state."""
        state = WorkflowState(
            workflow_id="test-eval",
            workflow_name="Test Evaluation",
            workflow_type="test",
            iteration_count=3,
            total_cost_usd=0.50,
            total_duration_ms=60000,
        )
        state.features = [
            Feature(
                name="Feature 1",
                description="Test feature",
                status="completed",
                tests_passing=True,
            ),
        ]
        return state

    @pytest.mark.asyncio
    @patch("jean_claude.orchestration.evaluator_agent.execute_prompt_async")
    async def test_run_evaluator_returns_evaluation(
        self,
        mock_execute: AsyncMock,
        sample_state: WorkflowState,
        tmp_path: Path,
    ):
        """Run evaluator and get evaluation result."""
        mock_execute.return_value.output = json.dumps({
            "overall_assessment": "Good work",
            "quality_rating": "good",
            "code_quality_notes": ["Clean"],
            "test_quality_notes": [],
            "strengths": ["Fast"],
            "improvements": [],
            "potential_issues": [],
        })

        result = await run_evaluator_agent(sample_state, tmp_path, "haiku")

        assert isinstance(result, AgentEvaluation)
        assert result.overall_assessment == "Good work"
        assert result.quality_rating == "good"

    @pytest.mark.asyncio
    @patch("jean_claude.orchestration.evaluator_agent.execute_prompt_async")
    async def test_run_evaluator_handles_sdk_error(
        self,
        mock_execute: AsyncMock,
        sample_state: WorkflowState,
        tmp_path: Path,
    ):
        """Handle SDK errors gracefully."""
        mock_execute.return_value.output = "Error: SDK failed"

        result = await run_evaluator_agent(sample_state, tmp_path, "haiku")

        # Should still return an AgentEvaluation, even if parsing failed
        assert isinstance(result, AgentEvaluation)
        assert "Could not parse" in result.overall_assessment

    @pytest.mark.asyncio
    @patch("jean_claude.orchestration.evaluator_agent.execute_prompt_async")
    async def test_run_evaluator_creates_output_dir(
        self,
        mock_execute: AsyncMock,
        sample_state: WorkflowState,
        tmp_path: Path,
    ):
        """Evaluator creates output directory."""
        mock_execute.return_value.output = json.dumps({
            "overall_assessment": "Test",
            "quality_rating": "acceptable",
        })

        await run_evaluator_agent(sample_state, tmp_path, "haiku")

        # Check that output directory was created
        output_dir = tmp_path / "agents" / sample_state.workflow_id / "evaluator"
        assert output_dir.exists()
