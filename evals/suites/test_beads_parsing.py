# ABOUTME: Eval suite for BeadsTask parsing and validation
# ABOUTME: Tests JSON parsing, status normalization, priority mapping, and ID validation

"""Eval suite for BeadsTask parsing.

This suite tests the BeadsTask model's ability to correctly parse
and validate task data from various input formats, including:
- JSON strings from 'bd show --json' output
- Status normalization (open/not_started/todo -> OPEN)
- Priority mapping (P0-P4 -> critical/high/medium/low)
- ID format validation (security-critical)
"""

from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import IsInstance

from jean_claude.core.beads import (
    BeadsTask,
    BeadsTaskStatus,
    BeadsTaskPriority,
    validate_beads_id,
)
from evals.evaluators import BeadsTaskValidEvaluator, BeadsIdFormatEvaluator


# ============================================================================
# Task: Parse BeadsTask from dict
# ============================================================================

def parse_beads_task(inputs: dict[str, Any]) -> dict[str, Any]:
    """Parse a BeadsTask from a dictionary and return key fields."""
    task = BeadsTask.from_dict(inputs)
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value if task.priority else None,
        "task_type": task.task_type.value if task.task_type else None,
        "acceptance_criteria": task.acceptance_criteria,
    }


# Test cases for BeadsTask parsing
beads_parsing_cases = [
    Case(
        name="basic_task_parsing",
        inputs={
            "id": "beads-123",
            "title": "Fix login bug",
            "description": "Users cannot log in with SSO",
            "status": "open",
        },
        expected_output={
            "id": "beads-123",
            "title": "Fix login bug",
            "status": "open",
        },
        metadata={"category": "parsing", "difficulty": "easy"},
    ),
    Case(
        name="status_normalization_not_started",
        inputs={
            "id": "gt-abc",
            "title": "Add feature",
            "description": "New feature request",
            "status": "not_started",  # Should normalize to 'open'
        },
        expected_output={
            "id": "gt-abc",
            "title": "Add feature",
            "status": "open",  # Normalized
        },
        metadata={"category": "normalization", "difficulty": "easy"},
    ),
    Case(
        name="status_normalization_done",
        inputs={
            "id": "hq-x1y2",
            "title": "Completed task",
            "description": "Already finished",
            "status": "done",  # Should normalize to 'closed'
        },
        expected_output={
            "id": "hq-x1y2",
            "title": "Completed task",
            "status": "closed",  # Normalized
        },
        metadata={"category": "normalization", "difficulty": "easy"},
    ),
    Case(
        name="priority_mapping_p0",
        inputs={
            "id": "beads-456",
            "title": "Critical outage",
            "description": "Production is down",
            "status": "in_progress",
            "priority": "P0",  # Should map to 'critical'
        },
        expected_output={
            "id": "beads-456",
            "title": "Critical outage",
            "status": "in_progress",
            "priority": "critical",
        },
        metadata={"category": "priority", "difficulty": "medium"},
    ),
    Case(
        name="priority_mapping_integer",
        inputs={
            "id": "beads-789",
            "title": "Low priority task",
            "description": "Can wait",
            "status": "open",
            "priority": 3,  # Integer 3 should map to 'low'
        },
        expected_output={
            "id": "beads-789",
            "title": "Low priority task",
            "status": "open",
            "priority": "low",
        },
        metadata={"category": "priority", "difficulty": "medium"},
    ),
    Case(
        name="acceptance_criteria_parsing",
        inputs={
            "id": "beads-ac1",
            "title": "Feature with criteria",
            "description": "Needs acceptance criteria",
            "status": "open",
            "acceptance_criteria": "- [ ] First criterion\n- [ ] Second criterion",
        },
        expected_output={
            "id": "beads-ac1",
            "title": "Feature with criteria",
            "status": "open",
        },
        metadata={"category": "parsing", "difficulty": "medium"},
    ),
]

beads_parsing_dataset = Dataset(
    cases=beads_parsing_cases,
    evaluators=[
        IsInstance(type_name="dict"),
        BeadsTaskValidEvaluator(),
    ],
)


# ============================================================================
# Task: Validate BeadsTask ID format
# ============================================================================

def validate_id_format(task_id: str) -> bool:
    """Validate a BeadsTask ID and return whether it's valid."""
    try:
        validate_beads_id(task_id)
        return True
    except ValueError:
        return False


# Test cases for ID validation (security-critical)
id_validation_cases = [
    # Valid IDs
    Case(
        name="valid_beads_prefix",
        inputs="beads-123",
        expected_output=True,
        metadata={"category": "valid", "security": True},
    ),
    Case(
        name="valid_short_prefix",
        inputs="gt-abc",
        expected_output=True,
        metadata={"category": "valid", "security": True},
    ),
    Case(
        name="valid_mixed_alphanumeric",
        inputs="hq-x1y2z3",
        expected_output=True,
        metadata={"category": "valid", "security": True},
    ),
    # Invalid IDs (potential injection attempts)
    Case(
        name="invalid_path_traversal",
        inputs="../etc/passwd",
        expected_output=False,
        metadata={"category": "injection", "security": True},
    ),
    Case(
        name="invalid_command_injection",
        inputs="beads-123; rm -rf /",
        expected_output=False,
        metadata={"category": "injection", "security": True},
    ),
    Case(
        name="invalid_pipe_injection",
        inputs="beads-123 | cat /etc/shadow",
        expected_output=False,
        metadata={"category": "injection", "security": True},
    ),
    Case(
        name="invalid_underscore_separator",
        inputs="beads_123",  # Underscore instead of hyphen
        expected_output=False,
        metadata={"category": "format", "security": True},
    ),
    Case(
        name="invalid_empty_string",
        inputs="",
        expected_output=False,
        metadata={"category": "format", "security": True},
    ),
    Case(
        name="invalid_single_letter_prefix",
        inputs="a-123",  # Prefix too short (minimum 2)
        expected_output=False,
        metadata={"category": "format", "security": True},
    ),
]

id_validation_dataset = Dataset(
    cases=id_validation_cases,
    evaluators=[
        BeadsIdFormatEvaluator(),
    ],
)


# ============================================================================
# Run evals
# ============================================================================

def run_beads_evals():
    """Run all BeadsTask evaluation suites."""
    print("\n" + "=" * 60)
    print("BeadsTask Parsing Evaluations")
    print("=" * 60)

    print("\n--- Task Parsing ---")
    report = beads_parsing_dataset.evaluate_sync(parse_beads_task)
    report.print(include_input=True, include_output=True)

    print("\n--- ID Validation (Security) ---")
    report = id_validation_dataset.evaluate_sync(validate_id_format)
    report.print(include_input=True, include_output=True)


if __name__ == "__main__":
    run_beads_evals()
