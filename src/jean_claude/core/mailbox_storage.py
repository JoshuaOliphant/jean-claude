# ABOUTME: Mailbox storage utilities for resolving mailbox paths
# ABOUTME: Provides resolve_mailbox_path() function to convert MessageBox enum to file path

"""Mailbox storage utilities for agent mailbox communication.

This module provides utility functions for working with mailbox storage,
including resolving MessageBox enum values to their corresponding file paths
using MailboxPaths.
"""

from pathlib import Path

from jean_claude.core.message_writer import MessageBox
from jean_claude.core.mailbox_paths import MailboxPaths


def resolve_mailbox_path(mailbox: MessageBox, paths: MailboxPaths) -> Path:
    """Convert MessageBox enum to file path using MailboxPaths.

    This function resolves a MessageBox enum value (INBOX or OUTBOX) to its
    corresponding file path (inbox.jsonl or outbox.jsonl) using the provided
    MailboxPaths object.

    Args:
        mailbox: The mailbox type (MessageBox.INBOX or MessageBox.OUTBOX)
        paths: MailboxPaths object containing the file paths

    Returns:
        Path object pointing to the mailbox file (inbox.jsonl or outbox.jsonl)

    Raises:
        ValueError: If mailbox is not a valid MessageBox enum value
        TypeError: If paths is None
        AttributeError: If paths is not a MailboxPaths object

    Example:
        >>> from jean_claude.core.mailbox_storage import resolve_mailbox_path
        >>> from jean_claude.core.message_writer import MessageBox
        >>> from jean_claude.core.mailbox_paths import MailboxPaths
        >>>
        >>> # Set up paths
        >>> paths = MailboxPaths(workflow_id="my-workflow")
        >>>
        >>> # Resolve inbox path
        >>> inbox_path = resolve_mailbox_path(MessageBox.INBOX, paths)
        >>> print(inbox_path)
        .../agents/my-workflow/mailbox/inbox.jsonl
        >>>
        >>> # Resolve outbox path
        >>> outbox_path = resolve_mailbox_path(MessageBox.OUTBOX, paths)
        >>> print(outbox_path)
        .../agents/my-workflow/mailbox/outbox.jsonl
    """
    # Validate mailbox type
    if not isinstance(mailbox, MessageBox):
        raise ValueError(
            f"mailbox must be a MessageBox enum value, got {type(mailbox).__name__}"
        )

    # Validate paths (will raise TypeError if None, AttributeError if wrong type)
    if paths is None:
        raise TypeError("paths cannot be None")

    # Determine the target file path based on mailbox type
    if mailbox == MessageBox.INBOX:
        file_path = paths.inbox_path
    elif mailbox == MessageBox.OUTBOX:
        file_path = paths.outbox_path
    else:
        raise ValueError(f"Invalid mailbox type: {mailbox}")

    return file_path
