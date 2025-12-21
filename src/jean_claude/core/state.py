# ABOUTME: Workflow state management module
# ABOUTME: Handles JSON persistence for workflow state in agents/{workflow_id}/

"""Workflow state management."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowPhase(BaseModel):
    """State of a single workflow phase."""

    name: str
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class WorkflowState(BaseModel):
    """Persistent state for a workflow execution."""

    workflow_id: str
    workflow_name: str
    workflow_type: str  # chore, feature, bug, sdlc, etc.
    phases: Dict[str, WorkflowPhase] = Field(default_factory=dict)
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    process_id: Optional[int] = None

    @classmethod
    def load(cls, workflow_id: str, project_root: Path) -> "WorkflowState":
        """Load workflow state from disk."""
        state_path = project_root / "agents" / workflow_id / "state.json"
        if not state_path.exists():
            raise FileNotFoundError(f"No state found for workflow: {workflow_id}")
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
