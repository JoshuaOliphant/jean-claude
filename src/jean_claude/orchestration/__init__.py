# ABOUTME: Orchestration modules for multi-phase workflow execution
# ABOUTME: Contains workflow engine, phase tracking, and auto-continue loops

"""Orchestration modules for workflow execution."""

from jean_claude.orchestration.auto_continue import (
    run_auto_continue,
    initialize_workflow,
    resume_workflow,
    AutoContinueError,
)

__all__ = [
    "run_auto_continue",
    "initialize_workflow",
    "resume_workflow",
    "AutoContinueError",
]
