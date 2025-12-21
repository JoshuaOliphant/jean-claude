"""ABOUTME: Data models and types for AI Developer Workflow (ADW) system.
ABOUTME: Provides Pydantic models for issues, state, agents, and workflow coordination."""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class GitHubIssue(BaseModel):
    """GitHub issue representation (also used for Beads compatibility)."""
    number: int
    title: str
    body: str
    state: str
    author: Dict[str, str]
    assignees: List[Dict[str, str]] = Field(default_factory=list)
    labels: List[Dict[str, str]] = Field(default_factory=list)
    milestone: Optional[Dict[str, Any]] = None
    comments: List[Dict[str, Any]] = Field(default_factory=list)
    createdAt: str
    updatedAt: str
    closedAt: Optional[str] = None
    url: str


class ADWStateData(BaseModel):
    """Persistent state data for ADW workflows."""
    adw_id: str
    issue_number: Optional[str] = None  # Can be GitHub number or Beads ID
    branch_name: Optional[str] = None
    plan_file: Optional[str] = None
    issue_class: Optional[str] = None
    worktree_path: Optional[str] = None
    backend_port: Optional[int] = None
    frontend_port: Optional[int] = None
    model_set: str = "base"  # base, advanced, or custom
    all_adws: List[str] = Field(default_factory=list)


class AgentTemplateRequest(BaseModel):
    """Claude Code agent template execution request."""
    agent_name: str
    slash_command: str
    args: List[str]
    adw_id: str
    model: Literal["sonnet", "opus", "haiku"] = "sonnet"
    working_dir: Optional[str] = None


class AgentPromptResponse(BaseModel):
    """Claude Code agent response."""
    output: str
    success: bool
    session_id: Optional[str] = None
    retry_code: str = "none"


class IssueClassSlashCommand(BaseModel):
    """Mapping of issue class to slash command."""
    issue_class: str
    slash_command: str
    description: Optional[str] = None


class ADWExtractionResult(BaseModel):
    """Result from ADW ID extraction."""
    adw_id: str
    issue_number: Optional[str] = None
    branch_name: Optional[str] = None
    source: str  # "branch", "state", or "generated"
    error: Optional[str] = None
