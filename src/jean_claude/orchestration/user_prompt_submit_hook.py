# ABOUTME: UserPromptSubmit hook callback for reading inbox messages
# ABOUTME: Injects unread inbox messages as additionalContext and updates inbox_count

"""UserPromptSubmit hook for agent mailbox communication.

This module provides the UserPromptSubmit hook callback that reads unread
inbox messages and injects them as additionalContext in the user prompt.
Messages are formatted clearly with priority, subject, and body. The inbox_count
is updated after reading to mark messages as read.
"""

from pathlib import Path
from typing import Any, Optional, Dict

from jean_claude.core.mailbox_api import Mailbox
from jean_claude.core.message import Message, MessagePriority


async def user_prompt_submit_hook(
    hook_context: Optional[Dict[str, Any]] = None,
    user_prompt: Optional[str] = None
) -> Optional[Dict[str, str]]:
    """UserPromptSubmit hook that reads unread inbox messages and injects as additionalContext.

    This hook is called when a user submits a prompt. It checks the agent's inbox
    for unread messages and injects them as additionalContext. Messages are formatted
    clearly with priority, subject, and body. After reading, the inbox_count is updated
    to mark all unread messages as read.

    Args:
        hook_context: Optional context dict containing:
            - workflow_id: The workflow ID for the agent
            - base_dir: Optional base directory for mailbox files
        user_prompt: The user's original prompt (not modified by this hook)

    Returns:
        A dict with "additionalContext" key containing the formatted messages if
        unread messages are found, otherwise None.

    Example:
        >>> # Called by SDK when user submits a prompt
        >>> context = {"workflow_id": "my-workflow"}
        >>> result = await user_prompt_submit_hook(
        ...     hook_context=context,
        ...     user_prompt="Continue with the task"
        ... )
        >>> if result:
        ...     print(result["additionalContext"])  # Formatted inbox messages

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

        # Check unread count
        unread_count = mailbox.get_unread_count()
        if unread_count == 0:
            return None

        # Read all inbox messages
        all_inbox_messages = mailbox.get_inbox_messages()

        # Get only the last N unread messages (most recent)
        # Since messages are appended to JSONL, the last N are the unread ones
        unread_messages = all_inbox_messages[-unread_count:] if unread_count <= len(all_inbox_messages) else all_inbox_messages

        # If no unread messages, return None
        if not unread_messages:
            return None

        # Build additionalContext with formatted messages
        additional_context = _format_messages(unread_messages)

        # Mark all unread messages as read
        mailbox.mark_as_read()

        return {"additionalContext": additional_context}

    except Exception:
        # Gracefully handle any errors (corrupted files, permission issues, etc.)
        # Return None to avoid breaking the agent
        return None


def _format_messages(messages: list[Message]) -> str:
    """Format messages for injection as additionalContext.

    Args:
        messages: List of unread messages from inbox

    Returns:
        A formatted string containing all messages with priority, subject, and body
    """
    if not messages:
        return ""

    # Build header
    count = len(messages)
    if count == 1:
        header = "📬 You have 1 new message in your inbox:\n"
    else:
        header = f"📬 You have {count} new messages in your inbox:\n"

    # Build message details
    message_details = []
    for i, msg in enumerate(messages, 1):
        # Format priority tag
        priority_str = ""
        if msg.priority == MessagePriority.URGENT:
            priority_str = "[URGENT] "
        elif msg.priority == MessagePriority.LOW:
            priority_str = "[LOW] "
        # NORMAL priority doesn't need a tag

        # Format message
        detail = (
            f"\n--- Message {i} ---\n"
            f"{priority_str}Subject: {msg.subject}\n"
            f"{msg.body}\n"
        )
        message_details.append(detail)

    # Combine header and details
    formatted = header + "".join(message_details)

    return formatted
