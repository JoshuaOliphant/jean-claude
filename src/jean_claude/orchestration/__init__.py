# ABOUTME: Orchestration modules for multi-phase workflow execution
# ABOUTME: Contains workflow engine, phase tracking, and auto-continue loops

"""Orchestration modules for workflow execution."""

from jean_claude.orchestration.auto_continue import (
    run_auto_continue,
    initialize_workflow,
    resume_workflow,
    AutoContinueError,
)
from jean_claude.orchestration.subagent_stop_hook import subagent_stop_hook
from jean_claude.orchestration.user_prompt_submit_hook import user_prompt_submit_hook
from jean_claude.orchestration.post_tool_use_hook import post_tool_use_hook

__all__ = [
    "run_auto_continue",
    "initialize_workflow",
    "resume_workflow",
    "AutoContinueError",
    "subagent_stop_hook",
    "user_prompt_submit_hook",
    "post_tool_use_hook",
]
