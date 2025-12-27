# ABOUTME: SubagentStop hook callback for checking outbox messages
# ABOUTME: Notifies orchestrator when subagent has urgent/awaiting_response messages

"""SubagentStop hook for agent mailbox communication.

This module provides the SubagentStop hook callback that checks a subagent's
outbox for urgent or awaiting_response messages. If found, it returns a
systemMessage to notify the orchestrator with message details.
"""

from pathlib import Path
from typing import Any, Optional, Dict

from jean_claude.core.mailbox_api import Mailbox
from jean_claude.core.message import Message, MessagePriority


async def subagent_stop_hook(
    hook_context: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, str]]:
    """SubagentStop hook that checks outbox for urgent/awaiting_response messages.

    This hook is called when a subagent stops execution. It checks the subagent's
    outbox for messages that require the orchestrator's attention (urgent priority
    or awaiting_response flag set). If such messages are found, it returns a
    systemMessage to notify the orchestrator.

    Args:
        hook_context: Optional context dict containing:
            - workflow_id: The workflow ID for the subagent
            - base_dir: Optional base directory for mailbox files

    Returns:
        A dict with "systemMessage" key containing the notification text if
        urgent/awaiting_response messages are found, otherwise None.

    Example:
        >>> # Called by SDK when subagent stops
        >>> context = {"workflow_id": "my-workflow"}
        >>> result = await subagent_stop_hook(hook_context=context)
        >>> if result:
        ...     print(result["systemMessage"])  # Notification for orchestrator

    Error Handling:
        - Returns None if context is None or missing workflow_id
        - Returns None if mailbox read fails (corrupted files, etc.)
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

    # Extract optional base_dir
    base_dir = hook_context.get("base_dir")
    if base_dir and isinstance(base_dir, (str, Path)):
        base_dir = Path(base_dir)
    else:
        base_dir = None

    try:
        # Create mailbox instance
        mailbox = Mailbox(workflow_id=workflow_id, base_dir=base_dir)

        # Read outbox messages
        outbox_messages = mailbox.get_outbox_messages()

        # Filter for urgent or awaiting_response messages
        important_messages = [
            msg for msg in outbox_messages
            if msg.priority == MessagePriority.URGENT or msg.awaiting_response
        ]

        # If no important messages, return None
        if not important_messages:
            return None

        # Build notification message
        notification = _build_notification(important_messages)

        return {"systemMessage": notification}

    except Exception:
        # Gracefully handle any errors (corrupted files, permission issues, etc.)
        # Return None to avoid breaking the agent
        return None


def _build_notification(messages: list[Message]) -> str:
    """Build a notification message for the orchestrator.

    Args:
        messages: List of important messages (urgent or awaiting response)

    Returns:
        A formatted notification string
    """
    if not messages:
        return ""

    # Build notification header
    count = len(messages)
    if count == 1:
        header = "⚠️  Subagent has 1 important message in outbox:"
    else:
        header = f"⚠️  Subagent has {count} important messages in outbox:"

    # Build message details
    message_details = []
    for msg in messages:
        # Determine tags
        tags = []
        if msg.priority == MessagePriority.URGENT:
            tags.append("URGENT")
        if msg.awaiting_response:
            tags.append("AWAITING RESPONSE")

        tag_str = " ".join([f"[{tag}]" for tag in tags])

        # Format message detail
        detail = f"\n  {tag_str} {msg.subject}\n    {msg.body}"
        message_details.append(detail)

    # Combine header and details
    notification = header + "".join(message_details)

    return notification
