# ABOUTME: Message reader module for reading messages from mailbox files
# ABOUTME: Implements read_messages function for parsing JSONL from inbox/outbox

"""Message reader module for agent mailbox communication.

This module provides the read_messages function that reads all messages
from either inbox.jsonl or outbox.jsonl files. It handles JSONL parsing,
gracefully handles missing or corrupted files by returning an empty list,
and validates message data.
"""

import json
from pathlib import Path
from typing import List

from pydantic import ValidationError

from jean_claude.core.message import Message
from jean_claude.core.mailbox_paths import MailboxPaths
from jean_claude.core.message_writer import MessageBox
from jean_claude.core.mailbox_storage import resolve_mailbox_path


def read_messages(
    mailbox: MessageBox,
    paths: MailboxPaths
) -> List[Message]:
    """Read all messages from the specified mailbox file.

    This function reads messages from either inbox.jsonl or outbox.jsonl,
    parsing each line as a JSON object and converting it to a Message object.
    It handles missing files, empty files, and corrupted data gracefully by
    returning an empty list or skipping invalid lines.

    Args:
        mailbox: The mailbox type (INBOX or OUTBOX)
        paths: MailboxPaths object containing the file paths

    Returns:
        A list of Message objects read from the file. Returns an empty list
        if the file doesn't exist, is empty, or contains no valid messages.

    Raises:
        TypeError: If mailbox is not a MessageBox enum or paths is None
        ValueError: If mailbox is not a valid MessageBox enum value
        AttributeError: If paths is None

    Example:
        >>> from jean_claude.core.message_reader import read_messages
        >>> from jean_claude.core.message_writer import MessageBox
        >>> from jean_claude.core.mailbox_paths import MailboxPaths
        >>>
        >>> # Set up paths
        >>> paths = MailboxPaths(workflow_id="my-workflow")
        >>>
        >>> # Read messages from inbox
        >>> messages = read_messages(MessageBox.INBOX, paths)
        >>> for msg in messages:
        ...     print(f"From: {msg.from_agent}, Subject: {msg.subject}")
    """
    # Use resolve_mailbox_path to get the file path
    # This validates mailbox type and paths, and returns the correct path
    file_path = resolve_mailbox_path(mailbox, paths)

    # If the file doesn't exist, return an empty list
    if not file_path.exists():
        return []

    # Read and parse messages from the file
    messages: List[Message] = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                # Skip empty lines or lines with only whitespace
                line = line.strip()
                if not line:
                    continue

                # Try to parse the JSON line
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    # Skip invalid JSON lines silently
                    # (corrupted data should be handled gracefully)
                    continue

                # Try to create a Message object from the data
                try:
                    message = Message(**data)
                    messages.append(message)
                except (ValidationError, TypeError):
                    # Skip invalid message data silently
                    # (missing required fields, wrong types, etc.)
                    continue

    except (OSError, IOError):
        # If there's an error reading the file, return empty list
        # This handles permission errors, disk errors, etc.
        return []

    return messages
