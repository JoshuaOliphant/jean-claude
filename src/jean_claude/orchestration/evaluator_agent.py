# ABOUTME: AI-powered workflow evaluator agent for qualitative analysis
# ABOUTME: Analyzes code changes, test quality, and provides contextual recommendations

"""AI evaluator agent for post-workflow quality analysis.

This module implements an evaluator agent that runs after workflow completion
to provide qualitative, contextual analysis that goes beyond simple metrics.

The evaluator agent analyzes:
- Git diff of changes made during the workflow
- Test coverage and test quality
- Code patterns and potential issues
- Commit message quality
- Alignment with workflow objectives

Unlike metric-based evaluation (in core/evaluation.py), this agent provides
human-like insights and actionable recommendations based on actual code review.
"""

import json
import subprocess
from pathlib import Path

from pydantic import BaseModel, Field

from jean_claude.core.agent import PromptRequest
from jean_claude.core.sdk_executor import execute_prompt_async
from jean_claude.core.state import WorkflowState


class AgentEvaluation(BaseModel):
    """Qualitative evaluation from the AI evaluator agent.

    Contains human-like insights about the workflow execution quality.
    """

    # Overall assessment
    overall_assessment: str = Field(
        description="1-2 sentence overall quality assessment"
    )
    quality_rating: str = Field(
        description="Rating: excellent, good, acceptable, needs_improvement, poor"
    )

    # Code quality insights
    code_quality_notes: list[str] = Field(
        default_factory=list,
        description="Specific observations about code quality"
    )

    # Test quality insights
    test_quality_notes: list[str] = Field(
        default_factory=list,
        description="Observations about test coverage and quality"
    )

    # Positive aspects
    strengths: list[str] = Field(
        default_factory=list,
        description="What was done well"
    )

    # Areas for improvement
    improvements: list[str] = Field(
        default_factory=list,
        description="Specific actionable improvements"
    )

    # Risk assessment
    potential_issues: list[str] = Field(
        default_factory=list,
        description="Potential bugs or issues identified"
    )

    # Raw response for debugging
    raw_response: str = Field(
        default="",
        description="Raw agent response (for debugging)"
    )


# Evaluator prompt template
EVALUATOR_PROMPT = """You are a code review agent evaluating a completed workflow.

## WORKFLOW SUMMARY

Workflow ID: {workflow_id}
Workflow Type: {workflow_type}
Features Planned: {total_features}
Features Completed: {completed_features}
Features Failed: {failed_features}
Total Cost: ${total_cost:.4f}
Total Duration: {duration_seconds:.1f} seconds

## FEATURES IMPLEMENTED

{features_summary}

## GIT DIFF OF CHANGES

```diff
{git_diff}
```

## YOUR MISSION

Analyze the workflow execution and code changes. Provide a thoughtful evaluation
covering:

1. **Overall Assessment**: Brief 1-2 sentence summary of quality
2. **Code Quality**: Observations about the implementation
3. **Test Quality**: Assessment of tests (if any)
4. **Strengths**: What was done well
5. **Improvements**: Actionable suggestions for future workflows
6. **Potential Issues**: Any bugs, security issues, or concerns

## OUTPUT FORMAT

You MUST output ONLY valid JSON in this exact structure:

```json
{{
  "overall_assessment": "Brief 1-2 sentence assessment",
  "quality_rating": "excellent|good|acceptable|needs_improvement|poor",
  "code_quality_notes": ["Note 1", "Note 2"],
  "test_quality_notes": ["Note 1", "Note 2"],
  "strengths": ["Strength 1", "Strength 2"],
  "improvements": ["Improvement 1", "Improvement 2"],
  "potential_issues": ["Issue 1", "Issue 2"]
}}
```

## GUIDELINES

- Be specific and actionable in your feedback
- Reference specific code when noting issues
- Balance positive observations with constructive criticism
- Focus on the most important observations (3-5 per category)
- Consider security, maintainability, and best practices
- If the diff is empty or minimal, note that appropriately

OUTPUT ONLY THE JSON. NO ADDITIONAL TEXT.
"""


def _get_git_diff(project_root: Path, max_lines: int = 500) -> str:
    """Get git diff of changes made during the workflow.

    Args:
        project_root: Project root path
        max_lines: Maximum lines of diff to return

    Returns:
        Git diff string, truncated if too long
    """
    try:
        # Get diff of staged and unstaged changes
        result = subprocess.run(
            ["git", "diff", "HEAD~5", "--stat", "--patch"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            # Try simpler diff
            result = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

        diff = result.stdout or "(no changes detected)"

        # Truncate if too long
        lines = diff.split("\n")
        if len(lines) > max_lines:
            diff = "\n".join(lines[:max_lines]) + f"\n\n... (truncated, {len(lines) - max_lines} more lines)"

        return diff

    except subprocess.TimeoutExpired:
        return "(git diff timed out)"
    except FileNotFoundError:
        return "(git not available)"
    except Exception as e:
        return f"(error getting diff: {e})"


def _format_features_summary(state: WorkflowState) -> str:
    """Format feature list for the prompt.

    Args:
        state: Workflow state

    Returns:
        Formatted features summary
    """
    if not state.features:
        return "(no features defined)"

    lines = []
    for i, feature in enumerate(state.features, 1):
        status_emoji = {
            "completed": "✓",
            "failed": "✗",
            "in_progress": "→",
            "not_started": "○",
        }.get(feature.status, "?")

        test_status = "tests passing" if feature.tests_passing else "tests not passing"
        test_info = f" ({test_status})" if feature.status == "completed" else ""

        lines.append(f"{i}. [{status_emoji}] {feature.name}: {feature.description}{test_info}")

    return "\n".join(lines)


async def run_evaluator_agent(
    state: WorkflowState,
    project_root: Path,
    model: str = "haiku",
) -> AgentEvaluation:
    """Run the AI evaluator agent to analyze workflow quality.

    This agent provides qualitative, contextual analysis of the workflow
    execution, including code review insights and actionable recommendations.

    Args:
        state: Completed workflow state
        project_root: Project root path
        model: Model to use (default: haiku for cost efficiency)

    Returns:
        AgentEvaluation with qualitative insights
    """
    # Gather context for the evaluator
    git_diff = _get_git_diff(project_root)
    features_summary = _format_features_summary(state)

    # Build the prompt
    prompt = EVALUATOR_PROMPT.format(
        workflow_id=state.workflow_id,
        workflow_type=state.workflow_type,
        total_features=len(state.features),
        completed_features=sum(1 for f in state.features if f.status == "completed"),
        failed_features=sum(1 for f in state.features if f.status == "failed"),
        total_cost=state.total_cost_usd,
        duration_seconds=state.total_duration_ms / 1000,
        features_summary=features_summary,
        git_diff=git_diff,
    )

    # Set up output directory
    output_dir = project_root / "agents" / state.workflow_id / "evaluator"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create prompt request
    request = PromptRequest(
        prompt=prompt,
        model=model,
        working_dir=project_root,
        output_dir=output_dir,
        dangerously_skip_permissions=True,  # Evaluator is read-only analysis
    )

    # Execute the evaluator agent
    result = await execute_prompt_async(request, max_retries=2)

    # Parse the response
    return _parse_evaluation_response(result.output)


def _parse_evaluation_response(response: str) -> AgentEvaluation:
    """Parse the evaluator agent's JSON response.

    Args:
        response: Raw response from the agent

    Returns:
        Parsed AgentEvaluation
    """
    # Try to extract JSON from the response
    try:
        # Look for JSON in code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "{" in response:
            # Try to find JSON object directly
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
        else:
            json_str = response

        data = json.loads(json_str)

        return AgentEvaluation(
            overall_assessment=data.get("overall_assessment", "Evaluation completed"),
            quality_rating=data.get("quality_rating", "acceptable"),
            code_quality_notes=data.get("code_quality_notes", []),
            test_quality_notes=data.get("test_quality_notes", []),
            strengths=data.get("strengths", []),
            improvements=data.get("improvements", []),
            potential_issues=data.get("potential_issues", []),
            raw_response=response,
        )

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        # Return a default evaluation with the raw response
        return AgentEvaluation(
            overall_assessment=f"Could not parse evaluation response: {e}",
            quality_rating="acceptable",
            raw_response=response,
        )


def run_evaluator_agent_sync(
    state: WorkflowState,
    project_root: Path,
    model: str = "haiku",
) -> AgentEvaluation:
    """Synchronous wrapper for run_evaluator_agent.

    Args:
        state: Completed workflow state
        project_root: Project root path
        model: Model to use (default: haiku)

    Returns:
        AgentEvaluation with qualitative insights
    """
    import anyio
    return anyio.run(run_evaluator_agent, state, project_root, model)


async def run_full_evaluation(
    state: WorkflowState,
    project_root: Path,
    include_agent_eval: bool = True,
    agent_model: str = "haiku",
) -> tuple:
    """Run both metric-based and AI agent evaluation.

    This combines:
    1. Quantitative metrics (from core/evaluation.py)
    2. Qualitative AI analysis (from this module)

    Args:
        state: Workflow state to evaluate
        project_root: Project root path
        include_agent_eval: Whether to run AI agent evaluation
        agent_model: Model for AI agent (default: haiku)

    Returns:
        Tuple of (WorkflowEvaluation, AgentEvaluation or None)
    """
    from jean_claude.core.evaluation import evaluate_workflow

    # Run metric-based evaluation
    metrics_eval = evaluate_workflow(state)

    # Optionally run AI agent evaluation
    agent_eval = None
    if include_agent_eval:
        agent_eval = await run_evaluator_agent(state, project_root, agent_model)

    return metrics_eval, agent_eval
