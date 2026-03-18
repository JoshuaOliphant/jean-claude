# ABOUTME: SDK sandbox configuration for workflow-type-based OS-level isolation
# ABOUTME: Maps workflow types to SandboxSettings for the Claude Agent SDK

"""Sandbox configuration for Jean Claude workflows.

This module provides per-workflow-type sandbox configurations using the
Claude Agent SDK's SandboxSettings. Unlike the command-name allowlist
approach in security.py, the SDK sandbox provides OS-level isolation
that restricts file access and network connectivity.
"""

from typing import Literal, Optional

from claude_agent_sdk import SandboxSettings


SANDBOX_CONFIGS: dict[str, SandboxSettings] = {
    "readonly": SandboxSettings(
        enabled=True,
        autoAllowBashIfSandboxed=True,
        allowUnsandboxedCommands=False,
    ),
    "development": SandboxSettings(
        enabled=True,
        autoAllowBashIfSandboxed=True,
        excludedCommands=["docker", "git"],
    ),
    "testing": SandboxSettings(
        enabled=True,
        autoAllowBashIfSandboxed=True,
        excludedCommands=["docker", "git"],
    ),
}


def get_sandbox_settings(
    workflow_type: str,
    enabled: bool = True,
) -> Optional[SandboxSettings]:
    """Get sandbox settings for a workflow type.

    Args:
        workflow_type: Type of workflow (readonly, development, testing)
        enabled: Whether sandbox is enabled. Returns None if False.

    Returns:
        SandboxSettings for the SDK, or None if disabled
    """
    if not enabled:
        return None

    return SANDBOX_CONFIGS.get(workflow_type, SANDBOX_CONFIGS["development"])
