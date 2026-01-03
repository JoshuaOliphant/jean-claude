# ABOUTME: Post-workflow evaluation system for quality assessment
# ABOUTME: Analyzes workflow runs and generates quality scores/metrics

"""Post-workflow evaluation module.

This module provides automated evaluation of workflow runs, analyzing:
- Feature completion rates and test coverage
- Iteration efficiency (features per iteration)
- Cost and time efficiency metrics
- Verification success rates
- Overall quality scoring

Evaluations run automatically after each workflow and emit events for tracking.
"""

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from jean_claude.core.state import WorkflowState


class EvaluationMetrics(BaseModel):
    """Individual evaluation metrics for a workflow run.

    Each metric is a score from 0.0 to 1.0 representing quality.
    """

    # Core completion metrics
    completion_rate: float = Field(
        ge=0.0, le=1.0,
        description="Ratio of completed features to total features"
    )
    test_pass_rate: float = Field(
        ge=0.0, le=1.0,
        description="Ratio of features with passing tests"
    )

    # Efficiency metrics
    iteration_efficiency: float = Field(
        ge=0.0, le=1.0,
        description="Features completed per iteration (normalized)"
    )
    cost_efficiency: float = Field(
        ge=0.0, le=1.0,
        description="Score based on cost per feature (lower is better)"
    )
    time_efficiency: float = Field(
        ge=0.0, le=1.0,
        description="Score based on time per feature (lower is better)"
    )

    # Quality metrics
    verification_rate: float = Field(
        ge=0.0, le=1.0,
        description="Ratio of successful verifications"
    )
    no_failures: float = Field(
        ge=0.0, le=1.0,
        description="1.0 if no features failed, 0.0 otherwise"
    )


class WorkflowEvaluation(BaseModel):
    """Complete evaluation result for a workflow run.

    Contains metrics, scores, and metadata about the evaluation.
    """

    # Identity
    workflow_id: str
    workflow_type: str
    evaluated_at: datetime = Field(default_factory=datetime.now)

    # Raw stats from workflow
    total_features: int
    completed_features: int
    failed_features: int
    iteration_count: int
    total_cost_usd: float
    total_duration_ms: int
    verification_count: int
    verification_passed: bool

    # Computed metrics
    metrics: EvaluationMetrics

    # Overall scores
    quality_score: float = Field(
        ge=0.0, le=1.0,
        description="Weighted overall quality score"
    )
    grade: Literal["A", "B", "C", "D", "F"] = Field(
        description="Letter grade based on quality score"
    )

    # Human-readable summary
    summary: str = Field(description="Brief evaluation summary")
    recommendations: list[str] = Field(
        default_factory=list,
        description="Improvement recommendations"
    )


def calculate_iteration_efficiency(
    completed_features: int,
    iteration_count: int,
    max_iterations: int = 50
) -> float:
    """Calculate iteration efficiency score.

    Ideal: 1 iteration per feature. Score degrades as iterations increase.

    Args:
        completed_features: Number of features completed
        iteration_count: Total iterations used
        max_iterations: Maximum allowed iterations (for normalization)

    Returns:
        Score from 0.0 to 1.0
    """
    if completed_features == 0 or iteration_count == 0:
        return 0.0

    # Ideal ratio is 1:1 (one iteration per feature)
    ideal_iterations = completed_features
    actual_ratio = ideal_iterations / iteration_count

    # Clamp to [0, 1]
    return min(1.0, max(0.0, actual_ratio))


def calculate_cost_efficiency(
    total_cost_usd: float,
    completed_features: int,
    cost_threshold: float = 0.50
) -> float:
    """Calculate cost efficiency score.

    Lower cost per feature is better. Uses threshold as reference point.

    Args:
        total_cost_usd: Total workflow cost
        completed_features: Number of features completed
        cost_threshold: Target cost per feature (default $0.50)

    Returns:
        Score from 0.0 to 1.0
    """
    if completed_features == 0:
        return 0.0

    cost_per_feature = total_cost_usd / completed_features

    # Score based on how close to threshold
    # At or below threshold = 1.0, degrades as cost increases
    if cost_per_feature <= cost_threshold:
        return 1.0

    # Linear degradation up to 4x threshold
    max_cost = cost_threshold * 4
    if cost_per_feature >= max_cost:
        return 0.0

    return 1.0 - ((cost_per_feature - cost_threshold) / (max_cost - cost_threshold))


def calculate_time_efficiency(
    total_duration_ms: int,
    completed_features: int,
    time_threshold_ms: int = 120000  # 2 minutes per feature
) -> float:
    """Calculate time efficiency score.

    Lower time per feature is better. Uses threshold as reference point.

    Args:
        total_duration_ms: Total workflow duration in milliseconds
        completed_features: Number of features completed
        time_threshold_ms: Target time per feature (default 2 min)

    Returns:
        Score from 0.0 to 1.0
    """
    if completed_features == 0:
        return 0.0

    time_per_feature = total_duration_ms / completed_features

    # Score based on how close to threshold
    if time_per_feature <= time_threshold_ms:
        return 1.0

    # Linear degradation up to 4x threshold
    max_time = time_threshold_ms * 4
    if time_per_feature >= max_time:
        return 0.0

    return 1.0 - ((time_per_feature - time_threshold_ms) / (max_time - time_threshold_ms))


def calculate_quality_score(metrics: EvaluationMetrics) -> float:
    """Calculate weighted overall quality score.

    Weights:
    - completion_rate: 30% (most important)
    - test_pass_rate: 20%
    - no_failures: 15%
    - iteration_efficiency: 10%
    - cost_efficiency: 10%
    - time_efficiency: 10%
    - verification_rate: 5%

    Args:
        metrics: Computed evaluation metrics

    Returns:
        Weighted score from 0.0 to 1.0
    """
    weights = {
        "completion_rate": 0.30,
        "test_pass_rate": 0.20,
        "no_failures": 0.15,
        "iteration_efficiency": 0.10,
        "cost_efficiency": 0.10,
        "time_efficiency": 0.10,
        "verification_rate": 0.05,
    }

    score = (
        metrics.completion_rate * weights["completion_rate"]
        + metrics.test_pass_rate * weights["test_pass_rate"]
        + metrics.no_failures * weights["no_failures"]
        + metrics.iteration_efficiency * weights["iteration_efficiency"]
        + metrics.cost_efficiency * weights["cost_efficiency"]
        + metrics.time_efficiency * weights["time_efficiency"]
        + metrics.verification_rate * weights["verification_rate"]
    )

    return round(score, 4)


def score_to_grade(score: float) -> Literal["A", "B", "C", "D", "F"]:
    """Convert quality score to letter grade.

    Args:
        score: Quality score from 0.0 to 1.0

    Returns:
        Letter grade (A, B, C, D, or F)
    """
    if score >= 0.90:
        return "A"
    elif score >= 0.80:
        return "B"
    elif score >= 0.70:
        return "C"
    elif score >= 0.60:
        return "D"
    else:
        return "F"


def generate_recommendations(
    metrics: EvaluationMetrics,
    completed_features: int,
    failed_features: int,
    total_features: int
) -> list[str]:
    """Generate improvement recommendations based on metrics.

    Args:
        metrics: Computed evaluation metrics
        completed_features: Number of completed features
        failed_features: Number of failed features
        total_features: Total number of features

    Returns:
        List of actionable recommendations
    """
    recommendations = []

    if metrics.completion_rate < 1.0:
        incomplete = total_features - completed_features
        recommendations.append(
            f"Resume workflow to complete {incomplete} remaining feature(s)"
        )

    if failed_features > 0:
        recommendations.append(
            f"Investigate {failed_features} failed feature(s) and retry"
        )

    if metrics.test_pass_rate < 0.8:
        recommendations.append(
            "Improve test coverage by adding test files to features"
        )

    if metrics.iteration_efficiency < 0.5:
        recommendations.append(
            "Consider breaking down complex features into smaller tasks"
        )

    if metrics.cost_efficiency < 0.5:
        recommendations.append(
            "Review feature complexity - consider using smaller models for simple tasks"
        )

    if metrics.time_efficiency < 0.5:
        recommendations.append(
            "Optimize prompts and reduce context to improve execution time"
        )

    if metrics.verification_rate < 0.5 and metrics.verification_rate > 0:
        recommendations.append(
            "Review failing verifications - tests may need updates"
        )

    return recommendations


def generate_summary(
    grade: str,
    completed_features: int,
    total_features: int,
    failed_features: int,
    quality_score: float
) -> str:
    """Generate human-readable evaluation summary.

    Args:
        grade: Letter grade
        completed_features: Number completed
        total_features: Total features
        failed_features: Number failed
        quality_score: Overall quality score

    Returns:
        Brief summary string
    """
    status = "completed" if completed_features == total_features else "partially completed"
    failure_note = f" with {failed_features} failure(s)" if failed_features > 0 else ""

    return (
        f"Workflow {status}{failure_note}. "
        f"Grade: {grade} ({quality_score:.0%}). "
        f"{completed_features}/{total_features} features implemented."
    )


def evaluate_workflow(state: WorkflowState) -> WorkflowEvaluation:
    """Evaluate a workflow run and generate quality assessment.

    This is the main entry point for workflow evaluation. It analyzes
    the workflow state and produces a comprehensive evaluation.

    Args:
        state: The completed (or partially completed) WorkflowState

    Returns:
        WorkflowEvaluation with metrics, scores, and recommendations
    """
    # Extract raw stats
    total_features = len(state.features)
    completed_features = sum(1 for f in state.features if f.status == "completed")
    failed_features = sum(1 for f in state.features if f.status == "failed")
    features_with_passing_tests = sum(
        1 for f in state.features
        if f.status == "completed" and f.tests_passing
    )

    # Calculate individual metrics
    completion_rate = completed_features / total_features if total_features > 0 else 0.0
    test_pass_rate = (
        features_with_passing_tests / completed_features
        if completed_features > 0
        else 0.0
    )
    iteration_efficiency = calculate_iteration_efficiency(
        completed_features, state.iteration_count
    )
    cost_efficiency = calculate_cost_efficiency(
        state.total_cost_usd, completed_features
    )
    time_efficiency = calculate_time_efficiency(
        state.total_duration_ms, completed_features
    )
    verification_rate = (
        1.0 if state.last_verification_passed else 0.0
    ) if state.verification_count > 0 else 1.0  # No verification needed = pass
    no_failures = 1.0 if failed_features == 0 else 0.0

    # Build metrics object
    metrics = EvaluationMetrics(
        completion_rate=completion_rate,
        test_pass_rate=test_pass_rate,
        iteration_efficiency=iteration_efficiency,
        cost_efficiency=cost_efficiency,
        time_efficiency=time_efficiency,
        verification_rate=verification_rate,
        no_failures=no_failures,
    )

    # Calculate overall score and grade
    quality_score = calculate_quality_score(metrics)
    grade = score_to_grade(quality_score)

    # Generate recommendations and summary
    recommendations = generate_recommendations(
        metrics, completed_features, failed_features, total_features
    )
    summary = generate_summary(
        grade, completed_features, total_features, failed_features, quality_score
    )

    return WorkflowEvaluation(
        workflow_id=state.workflow_id,
        workflow_type=state.workflow_type,
        total_features=total_features,
        completed_features=completed_features,
        failed_features=failed_features,
        iteration_count=state.iteration_count,
        total_cost_usd=state.total_cost_usd,
        total_duration_ms=state.total_duration_ms,
        verification_count=state.verification_count,
        verification_passed=state.last_verification_passed,
        metrics=metrics,
        quality_score=quality_score,
        grade=grade,
        summary=summary,
        recommendations=recommendations,
    )


def save_evaluation(
    evaluation: WorkflowEvaluation,
    project_root: Path
) -> Path:
    """Save evaluation results to the workflow's agent directory.

    Args:
        evaluation: The evaluation to save
        project_root: Project root path

    Returns:
        Path to the saved evaluation file
    """
    import json

    eval_dir = project_root / "agents" / evaluation.workflow_id
    eval_dir.mkdir(parents=True, exist_ok=True)
    eval_path = eval_dir / "evaluation.json"

    with open(eval_path, "w") as f:
        json.dump(evaluation.model_dump(mode="json"), f, indent=2, default=str)

    return eval_path


def load_evaluation(
    workflow_id: str,
    project_root: Path
) -> WorkflowEvaluation | None:
    """Load a saved evaluation from disk.

    Args:
        workflow_id: The workflow ID to load evaluation for
        project_root: Project root path

    Returns:
        WorkflowEvaluation if found, None otherwise
    """
    import json

    eval_path = project_root / "agents" / workflow_id / "evaluation.json"
    if not eval_path.exists():
        return None

    with open(eval_path) as f:
        data = json.load(f)

    return WorkflowEvaluation.model_validate(data)
