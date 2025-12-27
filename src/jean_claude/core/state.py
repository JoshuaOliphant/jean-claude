# ABOUTME: Workflow state management module
# ABOUTME: Handles JSON persistence for workflow state in agents/{workflow_id}/

"""Workflow state management."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class WorkflowPhase(BaseModel):
    """State of a single workflow phase."""

    name: str
    status: str = "pending"  # pending, running, completed, failed
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


class Feature(BaseModel):
    """A single feature or task to be implemented."""

    name: str
    description: str
    status: Literal["not_started", "in_progress", "completed", "failed"] = "not_started"
    test_file: str | None = None
    tests_passing: bool = False
    started_at: datetime | None = None
    completed_at: datetime | None = None


class WorkflowState(BaseModel):
    """Persistent state for a workflow execution with feature-based progress tracking."""

    workflow_id: str
    workflow_name: str
    workflow_type: str  # chore, feature, bug, sdlc, etc.
    phases: dict[str, WorkflowPhase] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    process_id: int | None = None

    # Beads integration
    beads_task_id: str | None = None
    beads_task_title: str | None = None
    phase: Literal["planning", "implementing", "verifying", "complete"] = "planning"

    # Feature tracking
    features: list[Feature] = Field(default_factory=list)
    current_feature_index: int = 0

    # Execution tracking
    iteration_count: int = 0
    max_iterations: int = 50

    # Session tracking
    session_ids: list[str] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    total_duration_ms: int = 0

    # Verification tracking
    last_verification_at: datetime | None = None
    last_verification_passed: bool = True
    verification_count: int = 0

    # Mailbox communication
    waiting_for_response: bool = False

    @classmethod
    def load(cls, workflow_id: str, project_root: Path) -> "WorkflowState":
        """Load workflow state from disk."""
        state_path = project_root / "agents" / workflow_id / "state.json"
        if not state_path.exists():
            raise FileNotFoundError(f"No state found for workflow: {workflow_id}")
        with open(state_path) as f:
            data = json.load(f)
        return cls.model_validate(data)

    @classmethod
    def load_from_file(cls, state_path: Path) -> "WorkflowState":
        """Load workflow state from a specific file path."""
        if not state_path.exists():
            raise FileNotFoundError(f"State file not found: {state_path}")
        with open(state_path) as f:
            data = json.load(f)
        return cls.model_validate(data)

    def save(self, project_root: Path) -> None:
        """Save workflow state to disk."""
        self.updated_at = datetime.now()
        state_dir = project_root / "agents" / self.workflow_id
        state_dir.mkdir(parents=True, exist_ok=True)
        state_path = state_dir / "state.json"
        with open(state_path, "w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2, default=str)

    def update_phase(self, phase_name: str, status: str) -> None:
        """Update a phase's status."""
        if phase_name not in self.phases:
            self.phases[phase_name] = WorkflowPhase(name=phase_name)

        phase = self.phases[phase_name]
        phase.status = status

        if status == "running" and phase.started_at is None:
            phase.started_at = datetime.now()
        elif status in ("completed", "failed"):
            phase.completed_at = datetime.now()

    @property
    def progress_percentage(self) -> float:
        """Calculate completion percentage based on features."""
        if not self.features:
            return 0.0
        completed = sum(1 for f in self.features if f.status == "completed")
        return (completed / len(self.features)) * 100

    @property
    def current_feature(self) -> Feature | None:
        """Get the current feature being worked on."""
        if 0 <= self.current_feature_index < len(self.features):
            return self.features[self.current_feature_index]
        return None

    def add_feature(self, name: str, description: str, test_file: str | None = None) -> Feature:
        """Add a new feature to track."""
        feature = Feature(name=name, description=description, test_file=test_file)
        self.features.append(feature)
        return feature

    def get_next_feature(self) -> Feature | None:
        """Get the next feature to work on, or None if all complete."""
        if self.current_feature_index >= len(self.features):
            return None
        return self.features[self.current_feature_index]

    def mark_feature_complete(self) -> None:
        """Mark the current feature as complete and advance to next."""
        if self.current_feature:
            self.current_feature.status = "completed"
            self.current_feature.completed_at = datetime.now()
            self.current_feature_index += 1

    def mark_feature_failed(self, error: str | None = None) -> None:
        """Mark the current feature as failed."""
        if self.current_feature:
            self.current_feature.status = "failed"
            self.current_feature.completed_at = datetime.now()

    def start_feature(self) -> Feature | None:
        """Mark current feature as in_progress and return it."""
        feature = self.current_feature
        if feature and feature.status == "not_started":
            feature.status = "in_progress"
            feature.started_at = datetime.now()
        return feature

    def is_complete(self) -> bool:
        """Check if all features are completed."""
        if not self.features:
            return False
        return all(f.status == "completed" for f in self.features)

    def is_failed(self) -> bool:
        """Check if any feature has failed."""
        return any(f.status == "failed" for f in self.features)

    def should_verify(self) -> bool:
        """Check if verification should run before continuing.

        Verification should run if:
        - There are completed features with test files
        - It's been more than 5 minutes since last verification (or never verified)

        Returns:
            True if verification is needed, False otherwise
        """
        # No completed features with tests → no need to verify
        completed_with_tests = [
            f for f in self.features if f.status == "completed" and f.test_file
        ]

        if not completed_with_tests:
            return False

        # If never verified, should verify
        if self.last_verification_at is None:
            return True

        # If last verified more than 5 minutes ago, verify again
        import time

        time_since_last = time.time() - self.last_verification_at.timestamp()
        return time_since_last > 300  # 5 minutes

    def mark_verification(self, passed: bool) -> None:
        """Record a verification run.

        Args:
            passed: Whether verification tests passed
        """
        self.last_verification_at = datetime.now()
        self.last_verification_passed = passed
        self.verification_count += 1

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of workflow progress."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "beads_task_id": self.beads_task_id,
            "beads_task_title": self.beads_task_title,
            "phase": self.phase,
            "total_features": len(self.features),
            "completed_features": sum(1 for f in self.features if f.status == "completed"),
            "failed_features": sum(1 for f in self.features if f.status == "failed"),
            "in_progress_features": sum(1 for f in self.features if f.status == "in_progress"),
            "progress_percentage": self.progress_percentage,
            "is_complete": self.is_complete(),
            "is_failed": self.is_failed(),
            "iteration_count": self.iteration_count,
            "total_cost_usd": self.total_cost_usd,
            "total_duration_ms": self.total_duration_ms,
        }
