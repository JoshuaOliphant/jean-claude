# ABOUTME: Evaluation framework for Jean Claude using pydantic-evals
# ABOUTME: Provides deterministic and LLM-based grading of agent behavior

"""Jean Claude Evaluation Framework.

This module provides evaluation infrastructure for testing Jean Claude's
components using pydantic-evals. It includes:

- Custom evaluators for BeadsTask parsing and WorkflowState transitions
- Eval suites organized by component
- Integration with LLMJudge for subjective quality assessment
"""

from .evaluators import (
    BeadsTaskValidEvaluator,
    WorkflowProgressEvaluator,
    FeatureCompletionEvaluator,
)

__all__ = [
    "BeadsTaskValidEvaluator",
    "WorkflowProgressEvaluator",
    "FeatureCompletionEvaluator",
]
