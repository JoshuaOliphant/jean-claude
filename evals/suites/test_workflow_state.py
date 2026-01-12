# ABOUTME: Eval suite for WorkflowState management and transitions
# ABOUTME: Tests feature tracking, progress calculation, and phase transitions

"""Eval suite for WorkflowState management.

This suite tests the WorkflowState model's ability to correctly:
- Track feature progress (not_started -> in_progress -> completed)
- Calculate progress percentages
- Manage phase transitions
- Handle edge cases (empty features, all completed, failures)
"""

from datetime import datetime
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import IsInstance

from jean_claude.core.state import WorkflowState, Feature
from evals.evaluators import (
    WorkflowProgressEvaluator,
    FeatureCompletionEvaluator,
)


# ============================================================================
# Task: Calculate workflow progress
# ============================================================================

def calculate_progress(inputs: dict[str, Any]) -> dict[str, Any]:
    """Create a WorkflowState and calculate its progress."""
    # Create workflow state
    state = WorkflowState(
        workflow_id=inputs.get("workflow_id", "test-001"),
        workflow_name=inputs.get("workflow_name", "Test Workflow"),
        workflow_type=inputs.get("workflow_type", "feature"),
    )

    # Add features with specified statuses
    for feature_data in inputs.get("features", []):
        feature = Feature(
            name=feature_data["name"],
            description=feature_data.get("description", ""),
            status=feature_data.get("status", "not_started"),
        )
        if feature_data.get("status") == "completed":
            feature.completed_at = datetime.now()
        state.features.append(feature)

    # Get summary
    summary = state.get_summary()
    return {
        "progress_percentage": summary["progress_percentage"],
        "completed_features": summary["completed_features"],
        "total_features": summary["total_features"],
        "is_complete": summary["is_complete"],
    }


# Test cases for progress calculation
progress_cases = [
    Case(
        name="empty_workflow",
        inputs={
            "workflow_id": "test-empty",
            "features": [],
        },
        expected_output={
            "progress_percentage": 0.0,
            "completed_features": 0,
            "total_features": 0,
        },
        metadata={"category": "edge_case", "difficulty": "easy"},
    ),
    Case(
        name="no_completed_features",
        inputs={
            "workflow_id": "test-zero",
            "features": [
                {"name": "Feature 1", "status": "not_started"},
                {"name": "Feature 2", "status": "in_progress"},
            ],
        },
        expected_output={
            "progress_percentage": 0.0,
            "completed_features": 0,
            "total_features": 2,
        },
        metadata={"category": "progress", "difficulty": "easy"},
    ),
    Case(
        name="half_completed",
        inputs={
            "workflow_id": "test-half",
            "features": [
                {"name": "Feature 1", "status": "completed"},
                {"name": "Feature 2", "status": "in_progress"},
            ],
        },
        expected_output={
            "progress_percentage": 50.0,
            "completed_features": 1,
            "total_features": 2,
        },
        metadata={"category": "progress", "difficulty": "easy"},
    ),
    Case(
        name="all_completed",
        inputs={
            "workflow_id": "test-done",
            "features": [
                {"name": "Feature 1", "status": "completed"},
                {"name": "Feature 2", "status": "completed"},
                {"name": "Feature 3", "status": "completed"},
            ],
        },
        expected_output={
            "progress_percentage": 100.0,
            "completed_features": 3,
            "total_features": 3,
        },
        metadata={"category": "progress", "difficulty": "easy"},
    ),
    Case(
        name="one_third_completed",
        inputs={
            "workflow_id": "test-third",
            "features": [
                {"name": "Feature 1", "status": "completed"},
                {"name": "Feature 2", "status": "not_started"},
                {"name": "Feature 3", "status": "not_started"},
            ],
        },
        expected_output={
            "progress_percentage": 33.33333333333333,  # 1/3
            "completed_features": 1,
            "total_features": 3,
        },
        metadata={"category": "progress", "difficulty": "medium"},
    ),
]

progress_dataset = Dataset(
    cases=progress_cases,
    evaluators=[
        IsInstance(type_name="dict"),
        WorkflowProgressEvaluator(),
    ],
)


# ============================================================================
# Task: Feature completion workflow
# ============================================================================

def complete_feature(inputs: dict[str, Any]) -> dict[str, Any]:
    """Test the mark_feature_complete workflow."""
    # Create workflow with features
    state = WorkflowState(
        workflow_id="test-complete",
        workflow_name="Completion Test",
        workflow_type="feature",
    )

    # Add features
    for i in range(inputs.get("num_features", 2)):
        state.add_feature(f"Feature {i+1}", f"Description {i+1}")

    # Start and complete the specified number of features
    for _ in range(inputs.get("complete_count", 1)):
        state.start_feature()
        state.mark_feature_complete()

    # Return state info
    current = state.current_feature
    return {
        "current_feature_index": state.current_feature_index,
        "feature_status": state.features[0].status if state.features else None,
        "completed_at": state.features[0].completed_at if state.features else None,
        "is_complete": state.is_complete(),
    }


feature_completion_cases = [
    Case(
        name="complete_first_feature",
        inputs={
            "num_features": 3,
            "complete_count": 1,
        },
        expected_output={
            "expected_index": 1,  # Should advance from 0 to 1
        },
        metadata={"category": "completion", "difficulty": "easy"},
    ),
    Case(
        name="complete_all_features",
        inputs={
            "num_features": 2,
            "complete_count": 2,
        },
        expected_output={
            "expected_index": 2,  # Should be at end
        },
        metadata={"category": "completion", "difficulty": "medium"},
    ),
]

feature_completion_dataset = Dataset(
    cases=feature_completion_cases,
    evaluators=[
        FeatureCompletionEvaluator(),
    ],
)


# ============================================================================
# Run evals
# ============================================================================

def run_workflow_evals():
    """Run all WorkflowState evaluation suites."""
    print("\n" + "=" * 60)
    print("WorkflowState Evaluations")
    print("=" * 60)

    print("\n--- Progress Calculation ---")
    report = progress_dataset.evaluate_sync(calculate_progress)
    report.print(include_input=True, include_output=True)

    print("\n--- Feature Completion ---")
    report = feature_completion_dataset.evaluate_sync(complete_feature)
    report.print(include_input=True, include_output=True)


if __name__ == "__main__":
    run_workflow_evals()
