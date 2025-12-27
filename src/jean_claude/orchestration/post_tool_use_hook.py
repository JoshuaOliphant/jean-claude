# ABOUTME: PostToolUse hook callback for detecting mailbox writes
# ABOUTME: Detects writes to mailbox paths and updates inbox_count.json accordingly

"""PostToolUse hook for agent mailbox communication.

This module provides the PostToolUse hook callback that detects writes to
mailbox paths (inbox/outbox/inbox_count) and updates inbox_count.json accordingly.
It increments the unread count on inbox writes and performs no-op on outbox writes.
"""

from pathlib import Path
from typing import Any, Optional, Dict

from jean_claude.core.mailbox_paths import MailboxPaths
from jean_claude.core.inbox_count_persistence import read_inbox_count, write_inbox_count


async def post_tool_use_hook(
    hook_context: Optional[Dict[str, Any]] = None,
    tool_name: Optional[str] = None,
    tool_input: Optional[Dict[str, Any]] = None,
    tool_output: Optional[Any] = None
) -> None:
    """PostToolUse hook that detects writes to mailbox paths and updates inbox_count.

    This hook is called after a tool is used. It checks if the tool wrote to any
    mailbox file paths. When inbox.jsonl is written, it increments the unread count.
    When outbox.jsonl or inbox_count.json is written, it performs no operation.

    The hook detects writes by checking the tool_input for a file_path parameter
    and comparing it against the expected mailbox paths for the workflow.

    Args:
        hook_context: Optional context dict containing:
            - workflow_id: The workflow ID for the agent
            - base_dir: Optional base directory for mailbox files
        tool_name: The name of the tool that was used (e.g., "Write", "Edit")
        tool_input: The input parameters passed to the tool (must contain file_path for writes)
        tool_output: The output/result from the tool execution

    Returns:
        Always returns None (this hook performs silent background operations)

    Example:
        >>> # Called by SDK after a tool is used
        >>> context = {"workflow_id": "my-workflow"}
        >>> result = await post_tool_use_hook(
        ...     hook_context=context,
        ...     tool_name="Write",
        ...     tool_input={"file_path": "/path/to/inbox.jsonl"},
        ...     tool_output={"success": True}
        ... )
        >>> # Result is None, but inbox_count has been incremented

    Behavior:
        - Write to inbox.jsonl: Increments unread count by 1
        - Write to outbox.jsonl: No operation (no-op)
        - Write to inbox_count.json: No operation (already updated)
        - Write to other files: No operation (not a mailbox file)
        - Read operations: No operation (only writes are tracked)

    Error Handling:
        - Returns None if context is None or missing workflow_id
        - Returns None if tool_input is None or missing file_path
        - Returns None if file path is not a mailbox path
        - Gracefully handles all exceptions to avoid breaking the agent
    """
    # Handle missing or invalid context
    if hook_context is None:
        return None

    if not isinstance(hook_context, dict):
        return None

    # Extract workflow_id from context
    workflow_id = hook_context.get("workflow_id")
    if not workflow_id:
        return None

    # Handle missing or invalid tool_input
    if tool_input is None:
        return None

    if not isinstance(tool_input, dict):
        return None

    # Extract file_path from tool_input
    file_path = tool_input.get("file_path")
    if not file_path:
        return None

    # Extract optional base_dir
    base_dir = hook_context.get("base_dir")
    if base_dir and isinstance(base_dir, (str, Path)):
        base_dir = Path(base_dir)
    else:
        base_dir = None

    try:
        # Create mailbox paths instance
        paths = MailboxPaths(workflow_id=workflow_id, base_dir=base_dir)

        # Normalize the file path to absolute for comparison
        written_path = Path(file_path).resolve()

        # Check if the written path is the inbox path
        if written_path == paths.inbox_path.resolve():
            # Increment the unread count
            inbox_count = read_inbox_count(paths)
            inbox_count.increment()
            write_inbox_count(inbox_count, paths)
            return None

        # Check if the written path is the outbox path
        if written_path == paths.outbox_path.resolve():
            # No-op for outbox writes
            return None

        # Check if the written path is the inbox_count path
        if written_path == paths.inbox_count_path.resolve():
            # No-op for inbox_count writes (already updated)
            return None

        # Not a mailbox path - no operation needed
        return None

    except Exception:
        # Gracefully handle any errors (path resolution, permission issues, etc.)
        # Return None to avoid breaking the agent
        return None
