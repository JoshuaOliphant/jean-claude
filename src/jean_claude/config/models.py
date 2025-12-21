# ABOUTME: Pydantic configuration models for Jean Claude CLI
# ABOUTME: Defines schema for .jc-project.yaml project configuration

"""Pydantic configuration models."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DirectoriesConfig(BaseModel):
    """Directory structure configuration."""

    specs: str = "specs/"
    agents: str = "agents/"
    trees: str = "trees/"
    source: str = "src/"
    tests: str = "tests/"


class ToolingConfig(BaseModel):
    """Development tooling configuration."""

    test_command: Optional[str] = "uv run pytest"
    linter_command: Optional[str] = "uv run ruff check ."
    format_command: Optional[str] = "uv run ruff format ."
    build_command: Optional[str] = None


class WorkflowsConfig(BaseModel):
    """Workflow execution configuration."""

    default_model: str = "sonnet"
    auto_commit: bool = True


class VCSConfig(BaseModel):
    """Version control configuration."""

    platform: str = "github"  # github, gitlab, bitbucket
    issue_tracker: str = "beads"  # beads, github-issues, jira


class ProjectConfig(BaseModel):
    """Root configuration model for .jc-project.yaml."""

    name: Optional[str] = None
    directories: DirectoriesConfig = Field(default_factory=DirectoriesConfig)
    tooling: ToolingConfig = Field(default_factory=ToolingConfig)
    workflows: WorkflowsConfig = Field(default_factory=WorkflowsConfig)
    vcs: VCSConfig = Field(default_factory=VCSConfig)
    plugins: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def load(cls, config_path: Path) -> "ProjectConfig":
        """Load configuration from YAML file."""
        import yaml

        if not config_path.exists():
            return cls()

        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        return cls.model_validate(data)

    def save(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        import yaml

        with open(config_path, "w") as f:
            yaml.dump(self.model_dump(exclude_none=True), f, default_flow_style=False)
