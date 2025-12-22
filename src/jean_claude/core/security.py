# ABOUTME: Security validation module for Claude Code SDK tool execution
# ABOUTME: Provides pre-tool-use hooks with command allowlists and configurable restrictions

"""Security module for Jean Claude CLI.

This module implements defense-in-depth security for autonomous agent execution
using pre-tool-use hooks from the Claude Code SDK. It validates bash commands
against configurable allowlists before they execute.

Security layers:
1. Environment isolation (Docker/sandbox)
2. SDK tool permissions (allowed_tools)
3. Command allowlist validation (this module)
"""

import logging
import shlex
from typing import Any, Dict, Literal, Optional, Set

logger = logging.getLogger(__name__)

# Default allowed commands for safe autonomous execution
DEFAULT_ALLOWED_COMMANDS: Set[str] = {
    # File inspection
    "ls",
    "cat",
    "head",
    "tail",
    "grep",
    "wc",
    "find",
    # File operations (safe)
    "cp",
    "mkdir",
    "touch",
    "chmod",
    # Git operations
    "git",
    # Python tooling
    "uv",
    "python",
    "python3",
    "pytest",
    "ruff",
    # Node/npm tooling
    "npm",
    "node",
    "npx",
    # Process inspection
    "ps",
    "lsof",
    # Utilities
    "sleep",
    "echo",
    "date",
}

# Restricted commands per workflow type
WORKFLOW_ALLOWLISTS: Dict[str, Set[str]] = {
    "readonly": {
        # Only inspection commands
        "ls",
        "cat",
        "head",
        "tail",
        "grep",
        "wc",
        "find",
        "git",
        "ps",
    },
    "development": DEFAULT_ALLOWED_COMMANDS
    | {
        # Additional dev tools
        "pkill",
        "docker",
        "curl",
        "wget",
    },
    "testing": DEFAULT_ALLOWED_COMMANDS
    | {
        # Testing-specific
        "coverage",
        "tox",
    },
}


class CommandSecurityError(Exception):
    """Raised when a command fails security validation."""

    pass


def extract_base_command(command: str) -> str:
    """Extract the base command from a shell command string.

    Handles:
    - Full paths (/usr/bin/python -> python)
    - Piped commands (takes first command)
    - Environment variables (FOO=bar cmd -> cmd)
    - Shell redirects (cmd > file -> cmd)

    Args:
        command: The shell command string

    Returns:
        The base command name

    Examples:
        >>> extract_base_command("ls -la")
        'ls'
        >>> extract_base_command("/usr/bin/python script.py")
        'python'
        >>> extract_base_command("FOO=bar npm install")
        'npm'
    """
    if not command:
        return ""

    try:
        # Split command respecting shell quoting
        parts = shlex.split(command)
        if not parts:
            return ""

        # Skip environment variable assignments (FOO=bar)
        cmd_part = None
        for part in parts:
            if "=" not in part or part.startswith("/"):
                cmd_part = part
                break

        if not cmd_part:
            return ""

        # Extract base command from full path
        base_cmd = cmd_part.split("/")[-1]

        # Handle redirects and pipes (take leftmost command)
        if "|" in base_cmd:
            base_cmd = base_cmd.split("|")[0].strip()
        if ">" in base_cmd:
            base_cmd = base_cmd.split(">")[0].strip()

        return base_cmd

    except (ValueError, IndexError):
        # If parsing fails, return empty string to be safe
        logger.warning(f"Failed to parse command: {command}")
        return ""


def validate_command(
    command: str,
    allowlist: Optional[Set[str]] = None,
    workflow_type: Literal["readonly", "development", "testing"] = "development",
) -> tuple[bool, Optional[str]]:
    """Validate a bash command against the allowlist.

    Args:
        command: The shell command to validate
        allowlist: Custom allowlist (overrides workflow_type)
        workflow_type: Type of workflow (determines allowlist if not custom)

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if command is allowed
        - (False, reason) if command is blocked

    Examples:
        >>> validate_command("ls -la")
        (True, None)
        >>> validate_command("rm -rf /")
        (False, "Command 'rm' not in allowlist")
    """
    # Determine which allowlist to use
    if allowlist is None:
        allowlist = WORKFLOW_ALLOWLISTS.get(workflow_type, DEFAULT_ALLOWED_COMMANDS)

    # Extract base command
    base_cmd = extract_base_command(command)

    if not base_cmd:
        # Empty commands are allowed (no-op)
        return True, None

    # Check against allowlist
    if base_cmd in allowlist:
        logger.debug(f"Command allowed: {base_cmd}")
        return True, None
    else:
        reason = f"Command '{base_cmd}' not in allowlist for workflow type '{workflow_type}'"
        logger.warning(f"Command blocked: {reason}")
        return False, reason


async def bash_security_hook(
    tool_input: Dict[str, Any],
    tool_use_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Pre-tool-use hook for validating bash commands.

    This hook is called by the Claude Code SDK before executing Bash tools.
    It validates commands against an allowlist and blocks unauthorized commands.

    Args:
        tool_input: The tool input dict, expected to have a 'command' key
        tool_use_id: Optional ID of the tool use (for logging)
        context: Optional context dict with workflow metadata

    Returns:
        Dict with:
        - decision: "allow" or "block"
        - reason: (optional) explanation if blocked

    Example:
        >>> import asyncio
        >>> result = asyncio.run(bash_security_hook({"command": "ls"}))
        >>> result['decision']
        'allow'
    """
    command = tool_input.get("command", "")

    # Extract workflow type from context if available
    workflow_type = "development"
    custom_allowlist = None

    if context:
        workflow_type = context.get("workflow_type", "development")
        custom_allowlist = context.get("command_allowlist")

    # Validate command
    is_valid, reason = validate_command(
        command=command,
        allowlist=custom_allowlist,
        workflow_type=workflow_type,
    )

    if is_valid:
        logger.info(f"[SECURITY] Allowed command: {command[:100]}")
        return {"decision": "allow"}
    else:
        logger.warning(f"[SECURITY] Blocked command: {command[:100]} - {reason}")
        return {"decision": "block", "reason": reason or "Command not allowed"}


def create_custom_allowlist(*commands: str) -> Set[str]:
    """Create a custom allowlist from command names.

    Useful for workflow-specific restrictions.

    Args:
        *commands: Command names to allow

    Returns:
        Set of allowed commands

    Example:
        >>> allowlist = create_custom_allowlist("ls", "cat", "grep")
        >>> validate_command("ls", allowlist=allowlist)
        (True, None)
    """
    return set(commands)


def get_allowlist_for_workflow(
    workflow_type: Literal["readonly", "development", "testing"],
) -> Set[str]:
    """Get the allowlist for a specific workflow type.

    Args:
        workflow_type: Type of workflow

    Returns:
        Set of allowed commands for that workflow

    Example:
        >>> allowlist = get_allowlist_for_workflow("readonly")
        >>> "rm" in allowlist
        False
    """
    return WORKFLOW_ALLOWLISTS.get(workflow_type, DEFAULT_ALLOWED_COMMANDS).copy()
