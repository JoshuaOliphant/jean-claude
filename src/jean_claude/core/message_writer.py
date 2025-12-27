# ABOUTME: Message writer module for appending messages to mailbox files
# ABOUTME: Implements write_message function for JSONL serialization to inbox/outbox

"""Message writer module for agent mailbox communication.

This module provides the write_message function that appends Message objects
to either inbox.jsonl or outbox.jsonl files. It handles JSONL serialization,
directory creation, and error handling gracefully.
"""

from enum import Enum
from pathlib import Path
from typing import Union

from jean_claude.core.message import Message
from jean_claude.core.mailbox_paths import MailboxPaths


class MessageBox(str, Enum):
    """Enum representing the type of mailbox.

    Attributes:
        INBOX: The inbox mailbox (for receiving messages)
        OUTBOX: The outbox mailbox (for sending messages)
    """

    INBOX = 'inbox'
    OUTBOX = 'outbox'


def write_message(
    message: Message,
    mailbox: MessageBox,
    paths: MailboxPaths
) -> None:
    """Write a message to the specified mailbox file.

    This function appends a Message to either inbox.jsonl or outbox.jsonl
    using JSONL (JSON Lines) format. Each message is written as a single
    line of JSON. The function creates the mailbox directory if it doesn't
    exist and handles errors gracefully.

    Args:
        message: The Message object to write
        mailbox: The mailbox type (INBOX or OUTBOX)
        paths: MailboxPaths object containing the file paths

    Raises:
        TypeError: If message is not a Message object
        ValueError: If mailbox is not a valid MessageBox enum value
        PermissionError: If the file cannot be written due to permissions
        OSError: If there are other I/O errors (disk full, etc.)

    Example:
        >>> from jean_claude.core.message import Message
        >>> from jean_claude.core.message_writer import write_message, MessageBox
        >>> from jean_claude.core.mailbox_paths import MailboxPaths
        >>>
        >>> # Create a message
        >>> msg = Message(
        ...     from_agent="agent-1",
        ...     to_agent="agent-2",
        ...     type="notification",
        ...     subject="Hello",
        ...     body="Hello, agent-2!"
        ... )
        >>>
        >>> # Set up paths
        >>> paths = MailboxPaths(workflow_id="my-workflow")
        >>>
        >>> # Write to inbox
        >>> write_message(msg, MessageBox.INBOX, paths)
    """
    # Validate message type
    if not isinstance(message, Message):
        raise TypeError(
            f"message must be a Message object, got {type(message).__name__}"
        )

    # Validate mailbox type
    if not isinstance(mailbox, MessageBox):
        raise ValueError(
            f"mailbox must be a MessageBox enum value, got {type(mailbox).__name__}"
        )

    # Determine the target file path based on mailbox type
    if mailbox == MessageBox.INBOX:
        file_path = paths.inbox_path
    elif mailbox == MessageBox.OUTBOX:
        file_path = paths.outbox_path
    else:
        raise ValueError(f"Invalid mailbox type: {mailbox}")

    # Ensure the mailbox directory exists
    paths.ensure_mailbox_dir()

    # Serialize the message to JSON (single line, no indentation)
    json_line = message.model_dump_json() + '\n'

    # Append the JSON line to the file
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json_line)
    except PermissionError as e:
        # Re-raise permission errors with more context
        raise PermissionError(
            f"Permission denied when writing to {file_path}"
        ) from e
    except OSError as e:
        # Re-raise OS errors (disk full, etc.) with more context
        raise OSError(
            f"Failed to write message to {file_path}: {e}"
        ) from e
