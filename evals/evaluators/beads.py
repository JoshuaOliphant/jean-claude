# ABOUTME: Evaluators for BeadsTask parsing and validation
# ABOUTME: Tests ID format validation, status normalization, and JSON parsing

"""Evaluators for BeadsTask parsing and validation.

These evaluators test the correctness of BeadsTask model parsing,
including:
- ID format validation (security-critical)
- Status normalization from various input formats
- Priority mapping (P0-P4 to low/medium/high/critical)
- JSON and dict parsing
"""

from dataclasses import dataclass
from typing import Any

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class BeadsTaskValidEvaluator(Evaluator[dict[str, Any], dict[str, Any]]):
    """Evaluates whether a BeadsTask was parsed correctly.

    Checks that all expected fields are present and have correct values
    after parsing through the BeadsTask model.
    """

    def evaluate(self, ctx: EvaluatorContext[dict[str, Any], dict[str, Any]]) -> dict[str, bool | float]:
        output = ctx.output
        expected = ctx.expected_output

        if output is None:
            return {
                "parsed_successfully": False,
                "fields_match": False,
                "score": 0.0,
            }

        # Check critical fields
        id_match = output.get("id") == expected.get("id")
        title_match = output.get("title") == expected.get("title")
        status_match = output.get("status") == expected.get("status")

        # Check optional fields if present in expected
        priority_match = True
        if "priority" in expected:
            priority_match = output.get("priority") == expected.get("priority")

        task_type_match = True
        if "task_type" in expected:
            task_type_match = output.get("task_type") == expected.get("task_type")

        all_match = all([id_match, title_match, status_match, priority_match, task_type_match])

        # Calculate partial score
        checks = [id_match, title_match, status_match, priority_match, task_type_match]
        score = sum(checks) / len(checks)

        return {
            "parsed_successfully": True,
            "id_correct": id_match,
            "title_correct": title_match,
            "status_correct": status_match,
            "priority_correct": priority_match,
            "task_type_correct": task_type_match,
            "fields_match": all_match,
            "score": score,
        }


@dataclass
class BeadsIdFormatEvaluator(Evaluator[str, bool]):
    """Evaluates BeadsTask ID format validation.

    Tests that the validate_beads_id function correctly identifies
    valid and invalid ID formats. This is security-critical as it
    prevents command injection attacks.
    """

    def evaluate(self, ctx: EvaluatorContext[str, bool]) -> dict[str, bool]:
        # output is True if validation passed, False if it raised
        # expected_output is what we expect (True = valid ID, False = invalid)
        validation_passed = ctx.output
        expected_valid = ctx.expected_output

        correct = validation_passed == expected_valid

        return {
            "validation_correct": correct,
            "caught_invalid": not validation_passed if not expected_valid else True,
            "allowed_valid": validation_passed if expected_valid else True,
        }
