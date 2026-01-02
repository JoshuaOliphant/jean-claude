# ABOUTME: Tests for the workflow evaluation system
# ABOUTME: Tests metrics calculation, scoring, and evaluation persistence

"""Tests for jean_claude.core.evaluation module."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from jean_claude.core.evaluation import (
    EvaluationMetrics,
    WorkflowEvaluation,
    calculate_cost_efficiency,
    calculate_iteration_efficiency,
    calculate_quality_score,
    calculate_time_efficiency,
    evaluate_workflow,
    generate_recommendations,
    generate_summary,
    load_evaluation,
    save_evaluation,
    score_to_grade,
)
from jean_claude.core.state import Feature, WorkflowState


class TestCalculateIterationEfficiency:
    """Tests for calculate_iteration_efficiency function."""

    def test_perfect_efficiency(self):
        """One iteration per feature = 100% efficiency."""
        result = calculate_iteration_efficiency(
            completed_features=5, iteration_count=5
        )
        assert result == 1.0

    def test_half_efficiency(self):
        """Two iterations per feature = 50% efficiency."""
        result = calculate_iteration_efficiency(
            completed_features=5, iteration_count=10
        )
        assert result == 0.5

    def test_zero_features(self):
        """No features completed = 0% efficiency."""
        result = calculate_iteration_efficiency(
            completed_features=0, iteration_count=5
        )
        assert result == 0.0

    def test_zero_iterations(self):
        """No iterations = 0% efficiency."""
        result = calculate_iteration_efficiency(
            completed_features=5, iteration_count=0
        )
        assert result == 0.0

    def test_more_features_than_iterations(self):
        """More features than iterations caps at 100%."""
        result = calculate_iteration_efficiency(
            completed_features=10, iteration_count=5
        )
        assert result == 1.0


class TestCalculateCostEfficiency:
    """Tests for calculate_cost_efficiency function."""

    def test_at_threshold(self):
        """Cost at threshold = 100% efficiency."""
        result = calculate_cost_efficiency(
            total_cost_usd=2.50, completed_features=5, cost_threshold=0.50
        )
        assert result == 1.0

    def test_below_threshold(self):
        """Cost below threshold = 100% efficiency."""
        result = calculate_cost_efficiency(
            total_cost_usd=1.00, completed_features=5, cost_threshold=0.50
        )
        assert result == 1.0

    def test_above_threshold(self):
        """Cost above threshold degrades efficiency."""
        result = calculate_cost_efficiency(
            total_cost_usd=5.00, completed_features=5, cost_threshold=0.50
        )
        # $1.00 per feature, threshold $0.50, should be between 0 and 1
        assert 0.0 < result < 1.0

    def test_max_cost(self):
        """Cost at 4x threshold = 0% efficiency."""
        result = calculate_cost_efficiency(
            total_cost_usd=10.00, completed_features=5, cost_threshold=0.50
        )
        assert result == 0.0

    def test_zero_features(self):
        """No features = 0% efficiency."""
        result = calculate_cost_efficiency(
            total_cost_usd=5.00, completed_features=0
        )
        assert result == 0.0


class TestCalculateTimeEfficiency:
    """Tests for calculate_time_efficiency function."""

    def test_at_threshold(self):
        """Time at threshold = 100% efficiency."""
        result = calculate_time_efficiency(
            total_duration_ms=600000, completed_features=5, time_threshold_ms=120000
        )
        assert result == 1.0

    def test_below_threshold(self):
        """Time below threshold = 100% efficiency."""
        result = calculate_time_efficiency(
            total_duration_ms=300000, completed_features=5, time_threshold_ms=120000
        )
        assert result == 1.0

    def test_above_threshold(self):
        """Time above threshold degrades efficiency."""
        result = calculate_time_efficiency(
            total_duration_ms=1200000, completed_features=5, time_threshold_ms=120000
        )
        # 4 min per feature, threshold 2 min, should be between 0 and 1
        assert 0.0 < result < 1.0

    def test_zero_features(self):
        """No features = 0% efficiency."""
        result = calculate_time_efficiency(
            total_duration_ms=600000, completed_features=0
        )
        assert result == 0.0


class TestCalculateQualityScore:
    """Tests for calculate_quality_score function."""

    def test_perfect_score(self):
        """All metrics at 1.0 = 1.0 quality score."""
        metrics = EvaluationMetrics(
            completion_rate=1.0,
            test_pass_rate=1.0,
            iteration_efficiency=1.0,
            cost_efficiency=1.0,
            time_efficiency=1.0,
            verification_rate=1.0,
            no_failures=1.0,
        )
        result = calculate_quality_score(metrics)
        assert result == 1.0

    def test_zero_score(self):
        """All metrics at 0.0 = 0.0 quality score."""
        metrics = EvaluationMetrics(
            completion_rate=0.0,
            test_pass_rate=0.0,
            iteration_efficiency=0.0,
            cost_efficiency=0.0,
            time_efficiency=0.0,
            verification_rate=0.0,
            no_failures=0.0,
        )
        result = calculate_quality_score(metrics)
        assert result == 0.0

    def test_weighted_score(self):
        """Completion rate has highest weight."""
        # Only completion rate at 1.0, others at 0.0
        metrics = EvaluationMetrics(
            completion_rate=1.0,
            test_pass_rate=0.0,
            iteration_efficiency=0.0,
            cost_efficiency=0.0,
            time_efficiency=0.0,
            verification_rate=0.0,
            no_failures=0.0,
        )
        result = calculate_quality_score(metrics)
        assert result == 0.30  # 30% weight for completion_rate


class TestScoreToGrade:
    """Tests for score_to_grade function."""

    @pytest.mark.parametrize(
        "score,expected_grade",
        [
            (1.0, "A"),
            (0.95, "A"),
            (0.90, "A"),
            (0.89, "B"),
            (0.80, "B"),
            (0.79, "C"),
            (0.70, "C"),
            (0.69, "D"),
            (0.60, "D"),
            (0.59, "F"),
            (0.0, "F"),
        ],
    )
    def test_grade_thresholds(self, score: float, expected_grade: str):
        """Test grade boundaries."""
        assert score_to_grade(score) == expected_grade


class TestGenerateRecommendations:
    """Tests for generate_recommendations function."""

    def test_no_recommendations_for_perfect_workflow(self):
        """Perfect metrics generate no recommendations."""
        metrics = EvaluationMetrics(
            completion_rate=1.0,
            test_pass_rate=1.0,
            iteration_efficiency=1.0,
            cost_efficiency=1.0,
            time_efficiency=1.0,
            verification_rate=1.0,
            no_failures=1.0,
        )
        recommendations = generate_recommendations(
            metrics, completed_features=5, failed_features=0, total_features=5
        )
        assert recommendations == []

    def test_incomplete_features_recommendation(self):
        """Incomplete features generate resume recommendation."""
        metrics = EvaluationMetrics(
            completion_rate=0.6,
            test_pass_rate=1.0,
            iteration_efficiency=1.0,
            cost_efficiency=1.0,
            time_efficiency=1.0,
            verification_rate=1.0,
            no_failures=1.0,
        )
        recommendations = generate_recommendations(
            metrics, completed_features=3, failed_features=0, total_features=5
        )
        assert any("remaining feature" in r for r in recommendations)

    def test_failed_features_recommendation(self):
        """Failed features generate investigation recommendation."""
        metrics = EvaluationMetrics(
            completion_rate=0.8,
            test_pass_rate=1.0,
            iteration_efficiency=1.0,
            cost_efficiency=1.0,
            time_efficiency=1.0,
            verification_rate=1.0,
            no_failures=0.0,
        )
        recommendations = generate_recommendations(
            metrics, completed_features=4, failed_features=1, total_features=5
        )
        assert any("failed feature" in r for r in recommendations)


class TestGenerateSummary:
    """Tests for generate_summary function."""

    def test_completed_workflow_summary(self):
        """Completed workflow shows completed status."""
        summary = generate_summary(
            grade="A",
            completed_features=5,
            total_features=5,
            failed_features=0,
            quality_score=0.95,
        )
        assert "completed" in summary
        assert "5/5 features" in summary
        assert "Grade: A" in summary

    def test_partial_workflow_summary(self):
        """Partial workflow shows partially completed status."""
        summary = generate_summary(
            grade="C",
            completed_features=3,
            total_features=5,
            failed_features=0,
            quality_score=0.70,
        )
        assert "partially completed" in summary
        assert "3/5 features" in summary

    def test_failed_features_in_summary(self):
        """Failed features are mentioned in summary."""
        summary = generate_summary(
            grade="D",
            completed_features=3,
            total_features=5,
            failed_features=2,
            quality_score=0.65,
        )
        assert "failure" in summary


class TestEvaluateWorkflow:
    """Tests for evaluate_workflow function."""

    @pytest.fixture
    def complete_workflow_state(self) -> WorkflowState:
        """Create a completed workflow state for testing."""
        state = WorkflowState(
            workflow_id="test-workflow",
            workflow_name="Test Workflow",
            workflow_type="test",
            iteration_count=3,
            total_cost_usd=1.50,
            total_duration_ms=300000,
            verification_count=1,
            last_verification_passed=True,
        )
        # Add completed features
        state.features = [
            Feature(
                name="Feature 1",
                description="Test feature 1",
                status="completed",
                tests_passing=True,
                completed_at=datetime.now(),
            ),
            Feature(
                name="Feature 2",
                description="Test feature 2",
                status="completed",
                tests_passing=True,
                completed_at=datetime.now(),
            ),
            Feature(
                name="Feature 3",
                description="Test feature 3",
                status="completed",
                tests_passing=False,
                completed_at=datetime.now(),
            ),
        ]
        return state

    @pytest.fixture
    def partial_workflow_state(self) -> WorkflowState:
        """Create a partial workflow state for testing."""
        state = WorkflowState(
            workflow_id="partial-workflow",
            workflow_name="Partial Workflow",
            workflow_type="test",
            iteration_count=5,
            total_cost_usd=2.50,
            total_duration_ms=600000,
            verification_count=0,
        )
        state.features = [
            Feature(
                name="Feature 1",
                description="Test feature 1",
                status="completed",
                tests_passing=True,
            ),
            Feature(
                name="Feature 2",
                description="Test feature 2",
                status="failed",
            ),
            Feature(
                name="Feature 3",
                description="Test feature 3",
                status="not_started",
            ),
        ]
        return state

    def test_evaluate_complete_workflow(self, complete_workflow_state: WorkflowState):
        """Evaluate a fully completed workflow."""
        evaluation = evaluate_workflow(complete_workflow_state)

        assert evaluation.workflow_id == "test-workflow"
        assert evaluation.total_features == 3
        assert evaluation.completed_features == 3
        assert evaluation.failed_features == 0
        assert evaluation.metrics.completion_rate == 1.0
        assert 0.0 <= evaluation.metrics.test_pass_rate <= 1.0
        assert evaluation.grade in ["A", "B", "C", "D", "F"]
        assert evaluation.summary != ""

    def test_evaluate_partial_workflow(self, partial_workflow_state: WorkflowState):
        """Evaluate a partially completed workflow."""
        evaluation = evaluate_workflow(partial_workflow_state)

        assert evaluation.workflow_id == "partial-workflow"
        assert evaluation.total_features == 3
        assert evaluation.completed_features == 1
        assert evaluation.failed_features == 1
        assert evaluation.metrics.completion_rate < 1.0
        assert evaluation.metrics.no_failures == 0.0
        assert len(evaluation.recommendations) > 0

    def test_evaluate_empty_workflow(self):
        """Evaluate a workflow with no features."""
        state = WorkflowState(
            workflow_id="empty-workflow",
            workflow_name="Empty Workflow",
            workflow_type="test",
        )
        evaluation = evaluate_workflow(state)

        assert evaluation.total_features == 0
        assert evaluation.completed_features == 0
        assert evaluation.metrics.completion_rate == 0.0


class TestEvaluationPersistence:
    """Tests for save_evaluation and load_evaluation functions."""

    @pytest.fixture
    def sample_evaluation(self) -> WorkflowEvaluation:
        """Create a sample evaluation for testing."""
        return WorkflowEvaluation(
            workflow_id="persist-test",
            workflow_type="test",
            total_features=5,
            completed_features=4,
            failed_features=1,
            iteration_count=6,
            total_cost_usd=2.00,
            total_duration_ms=500000,
            verification_count=2,
            verification_passed=True,
            metrics=EvaluationMetrics(
                completion_rate=0.8,
                test_pass_rate=0.75,
                iteration_efficiency=0.67,
                cost_efficiency=0.8,
                time_efficiency=0.9,
                verification_rate=1.0,
                no_failures=0.0,
            ),
            quality_score=0.75,
            grade="C",
            summary="Test summary",
            recommendations=["Fix the failed feature"],
        )

    def test_save_and_load_evaluation(
        self, tmp_path: Path, sample_evaluation: WorkflowEvaluation
    ):
        """Test saving and loading evaluation."""
        # Save
        eval_path = save_evaluation(sample_evaluation, tmp_path)
        assert eval_path.exists()
        assert eval_path.name == "evaluation.json"

        # Load
        loaded = load_evaluation("persist-test", tmp_path)
        assert loaded is not None
        assert loaded.workflow_id == sample_evaluation.workflow_id
        assert loaded.quality_score == sample_evaluation.quality_score
        assert loaded.grade == sample_evaluation.grade
        assert loaded.metrics.completion_rate == sample_evaluation.metrics.completion_rate

    def test_load_nonexistent_evaluation(self, tmp_path: Path):
        """Loading non-existent evaluation returns None."""
        result = load_evaluation("nonexistent", tmp_path)
        assert result is None

    def test_save_creates_directory(
        self, tmp_path: Path, sample_evaluation: WorkflowEvaluation
    ):
        """Save creates agents directory if needed."""
        eval_path = save_evaluation(sample_evaluation, tmp_path)
        assert (tmp_path / "agents" / "persist-test").exists()
        assert eval_path.exists()

    def test_saved_evaluation_is_valid_json(
        self, tmp_path: Path, sample_evaluation: WorkflowEvaluation
    ):
        """Saved evaluation is valid JSON."""
        eval_path = save_evaluation(sample_evaluation, tmp_path)
        with open(eval_path) as f:
            data = json.load(f)

        assert data["workflow_id"] == "persist-test"
        assert data["grade"] == "C"
        assert "metrics" in data
        assert data["metrics"]["completion_rate"] == 0.8
