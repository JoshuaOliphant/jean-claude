# ABOUTME: InboxCount persistence module for loading/saving inbox_count.json
# ABOUTME: Implements read_inbox_count and write_inbox_count with atomic writes

"""InboxCount persistence module for agent mailbox communication.

This module provides functions to read and write InboxCount objects to/from
inbox_count.json files. It handles missing files gracefully and uses atomic
writes to ensure data integrity.
"""

import json
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from jean_claude.core.inbox_count import InboxCount
from jean_claude.core.mailbox_paths import MailboxPaths


def read_inbox_count(paths: MailboxPaths) -> InboxCount:
    """Read inbox count from inbox_count.json file.

    This function reads the inbox count from the inbox_count.json file.
    If the file doesn't exist or contains invalid data, it returns a
    default InboxCount with unread=0.

    Args:
        paths: MailboxPaths object containing the file paths

    Returns:
        InboxCount object loaded from file, or default InboxCount(unread=0)
        if the file doesn't exist or contains invalid data

    Raises:
        TypeError: If paths is None

    Example:
        >>> from jean_claude.core.inbox_count_persistence import read_inbox_count
        >>> from jean_claude.core.mailbox_paths import MailboxPaths
        >>>
        >>> # Set up paths
        >>> paths = MailboxPaths(workflow_id="my-workflow")
        >>>
        >>> # Read inbox count
        >>> inbox_count = read_inbox_count(paths)
        >>> print(f"Unread messages: {inbox_count.unread}")
    """
    # Validate paths
    if paths is None:
        raise TypeError("paths cannot be None")

    # Get the inbox count file path
    file_path = paths.inbox_count_path

    # If the file doesn't exist, return default InboxCount
    if not file_path.exists():
        return InboxCount(unread=0)

    # Try to read and parse the file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Try to create InboxCount from the data
        try:
            inbox_count = InboxCount(**data)
            return inbox_count
        except (ValidationError, TypeError):
            # Invalid data in file, return default
            return InboxCount(unread=0)

    except (json.JSONDecodeError, OSError, IOError):
        # File is corrupted or unreadable, return default
        return InboxCount(unread=0)


def write_inbox_count(inbox_count: InboxCount, paths: MailboxPaths) -> None:
    """Write inbox count to inbox_count.json file.

    This function writes the InboxCount to inbox_count.json using an atomic
    write operation with a temporary file. This ensures that the file is never
    left in a corrupted state, even if the write operation is interrupted.

    The function creates the mailbox directory if it doesn't exist.

    Args:
        inbox_count: The InboxCount object to write
        paths: MailboxPaths object containing the file paths

    Raises:
        TypeError: If inbox_count is not an InboxCount object or paths is None
        PermissionError: If the file cannot be written due to permissions
        OSError: If there are other I/O errors (disk full, etc.)

    Example:
        >>> from jean_claude.core.inbox_count import InboxCount
        >>> from jean_claude.core.inbox_count_persistence import write_inbox_count
        >>> from jean_claude.core.mailbox_paths import MailboxPaths
        >>>
        >>> # Create inbox count
        >>> inbox_count = InboxCount(unread=5)
        >>>
        >>> # Set up paths
        >>> paths = MailboxPaths(workflow_id="my-workflow")
        >>>
        >>> # Write inbox count
        >>> write_inbox_count(inbox_count, paths)
    """
    # Validate inbox_count type
    if inbox_count is None:
        raise TypeError("inbox_count cannot be None")

    if not isinstance(inbox_count, InboxCount):
        raise TypeError(
            f"inbox_count must be an InboxCount object, got {type(inbox_count).__name__}"
        )

    # Validate paths
    if paths is None:
        raise TypeError("paths cannot be None")

    # Ensure the mailbox directory exists
    paths.ensure_mailbox_dir()

    # Get the target file path
    file_path = paths.inbox_count_path

    # Create a temporary file path (same directory, .tmp extension)
    temp_path = file_path.parent / f"{file_path.name}.tmp"

    # Serialize the inbox count to JSON
    data = inbox_count.model_dump()

    try:
        # Write to temporary file first (atomic write pattern)
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        # Atomic rename (on most systems, this is an atomic operation)
        temp_path.replace(file_path)

    except PermissionError as e:
        # Clean up temp file if it exists
        if temp_path.exists():
            try:
                temp_path.unlink()
            except:
                pass  # Ignore errors during cleanup

        # Re-raise permission errors with more context
        raise PermissionError(
            f"Permission denied when writing to {file_path}"
        ) from e

    except OSError as e:
        # Clean up temp file if it exists
        if temp_path.exists():
            try:
                temp_path.unlink()
            except:
                pass  # Ignore errors during cleanup

        # Re-raise OS errors (disk full, etc.) with more context
        raise OSError(
            f"Failed to write inbox count to {file_path}: {e}"
        ) from e
