# ABOUTME: Evaluators for WorkflowState transitions and feature tracking
# ABOUTME: Tests phase transitions, feature completion, and progress calculation

"""Evaluators for WorkflowState management.

These evaluators test the correctness of WorkflowState operations,
including:
- Phase transitions (planning -> implementing -> verifying -> complete)
- Feature status tracking (not_started -> in_progress -> completed/failed)
- Progress percentage calculations
- State persistence and loading
"""

from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class WorkflowProgressEvaluator(Evaluator[dict[str, Any], dict[str, Any]]):
    """Evaluates workflow progress calculations.

    Verifies that progress_percentage and feature counts are
    calculated correctly based on feature statuses.
    """

    def evaluate(self, ctx: EvaluatorContext[dict[str, Any], dict[str, Any]]) -> dict[str, bool | float]:
        output = ctx.output
        expected = ctx.expected_output

        if output is None:
            return {
                "progress_correct": False,
                "counts_correct": False,
                "score": 0.0,
            }

        # Check progress percentage (with small tolerance for floating point)
        expected_progress = expected.get("progress_percentage", 0.0)
        actual_progress = output.get("progress_percentage", 0.0)
        progress_correct = abs(expected_progress - actual_progress) < 0.01

        # Check feature counts
        expected_completed = expected.get("completed_features", 0)
        actual_completed = output.get("completed_features", 0)
        completed_correct = expected_completed == actual_completed

        expected_total = expected.get("total_features", 0)
        actual_total = output.get("total_features", 0)
        total_correct = expected_total == actual_total

        counts_correct = completed_correct and total_correct

        # Calculate score
        checks = [progress_correct, completed_correct, total_correct]
        score = sum(checks) / len(checks)

        return {
            "progress_correct": progress_correct,
            "completed_count_correct": completed_correct,
            "total_count_correct": total_correct,
            "counts_correct": counts_correct,
            "score": score,
        }


@dataclass
class FeatureCompletionEvaluator(Evaluator[dict[str, Any], dict[str, Any]]):
    """Evaluates feature completion workflow.

    Tests the mark_feature_complete flow:
    - Status changes to 'completed'
    - completed_at timestamp is set
    - current_feature_index advances
    """

    def evaluate(self, ctx: EvaluatorContext[dict[str, Any], dict[str, Any]]) -> dict[str, bool]:
        output = ctx.output
        expected = ctx.expected_output

        if output is None:
            return {
                "status_updated": False,
                "timestamp_set": False,
                "index_advanced": False,
            }

        # Check status was updated
        status_updated = output.get("feature_status") == "completed"

        # Check timestamp was set
        timestamp_set = output.get("completed_at") is not None

        # Check index advanced
        expected_index = expected.get("expected_index", 1)
        actual_index = output.get("current_feature_index", 0)
        index_advanced = actual_index == expected_index

        return {
            "status_updated": status_updated,
            "timestamp_set": timestamp_set,
            "index_advanced": index_advanced,
        }


@dataclass
class PhaseTransitionEvaluator(Evaluator[str, str]):
    """Evaluates workflow phase transitions.

    Tests that phase transitions follow the valid sequence:
    planning -> implementing -> verifying -> complete
    """

    valid_transitions: dict[str, list[str]] = None

    def __post_init__(self):
        if self.valid_transitions is None:
            self.valid_transitions = {
                "planning": ["implementing"],
                "implementing": ["verifying", "complete"],
                "verifying": ["implementing", "complete"],
                "complete": [],  # Terminal state
            }

    def evaluate(self, ctx: EvaluatorContext[str, str]) -> dict[str, bool]:
        # Input is (from_phase, to_phase), output is resulting phase
        from_phase = ctx.attributes.get("from_phase", "planning")
        to_phase = ctx.output
        expected_phase = ctx.expected_output

        # Check if transition is valid
        allowed = self.valid_transitions.get(from_phase, [])
        transition_valid = to_phase in allowed or to_phase == from_phase

        # Check if we got expected result
        result_correct = to_phase == expected_phase

        return {
            "transition_valid": transition_valid,
            "result_correct": result_correct,
        }
