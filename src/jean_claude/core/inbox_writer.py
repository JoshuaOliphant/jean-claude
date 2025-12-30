# ABOUTME: InboxWriter class for writing Message objects to INBOX directories
# ABOUTME: Provides high-level interface for writing messages to agent inboxes

"""InboxWriter for agent mailbox communication.

This module provides the InboxWriter class that writes Message objects to
INBOX directories using the existing Message save functionality. It wraps
the lower-level message writing infrastructure to provide a simple interface
for sending messages to agent inboxes.
"""

import json
from pathlib import Path
from typing import Union
from uuid import uuid4

from jean_claude.core.message import Message
from jean_claude.core.mailbox_directory_manager import MailboxDirectoryManager


class InboxWriter:
    """Writer for sending messages to agent INBOX directories.

    InboxWriter provides a high-level interface for writing Message objects
    to INBOX directories within a workflow. It handles directory creation,
    message serialization, and file writing using the existing mailbox
    infrastructure.

    The writer saves each message as a separate JSON file in the INBOX
    directory, using the message ID as the filename.

    Attributes:
        workflow_dir: Path to the workflow directory containing the INBOX
        _directory_manager: MailboxDirectoryManager for directory operations
    """

    def __init__(self, workflow_dir: Union[str, Path]):
        """Initialize InboxWriter with workflow directory.

        Args:
            workflow_dir: Path to the workflow directory where INBOX should be created

        Raises:
            TypeError: If workflow_dir is None
            ValueError: If workflow_dir is empty string
        """
        if workflow_dir is None:
            raise TypeError("workflow_dir cannot be None")

        if isinstance(workflow_dir, str) and not workflow_dir.strip():
            raise ValueError("workflow_dir cannot be empty")

        self.workflow_dir = Path(workflow_dir)
        self._directory_manager = MailboxDirectoryManager(self.workflow_dir)

    def write_to_inbox(self, message: Message) -> None:
        """Write a message to the INBOX directory.

        This method saves a Message object to the INBOX directory as a JSON file.
        The INBOX directory will be created if it doesn't exist. Each message
        is saved as a separate file using the message ID as the filename.

        Args:
            message: The Message object to write to the inbox

        Raises:
            TypeError: If message is not a Message object
            ValueError: If message validation fails
            PermissionError: If unable to create directory or write file
            OSError: If there are other I/O errors

        Example:
            >>> from jean_claude.core.message import Message, MessagePriority
            >>> from jean_claude.core.inbox_writer import InboxWriter
            >>>
            >>> # Create a message
            >>> msg = Message(
            ...     from_agent="implementation-agent",
            ...     to_agent="coordinator",
            ...     type="blocker_detected",
            ...     subject="Test Failure",
            ...     body="Tests failed in authentication module",
            ...     priority=MessagePriority.URGENT,
            ...     awaiting_response=True
            ... )
            >>>
            >>> # Write to inbox
            >>> writer = InboxWriter("/path/to/workflow")
            >>> writer.write_to_inbox(msg)
        """
        # Validate message type
        if not isinstance(message, Message):
            raise TypeError(
                f"message must be a Message object, got {type(message).__name__}"
            )

        # Ensure INBOX directory exists
        try:
            self._directory_manager.ensure_directories()
        except (PermissionError, OSError) as e:
            # Re-raise with context
            raise type(e)(f"Failed to create INBOX directory: {e}") from e

        # Get inbox path
        inbox_path = self._directory_manager.get_inbox_path()

        # Create filename using message ID
        filename = f"{message.id}.json"
        file_path = inbox_path / filename

        # Serialize message to JSON
        try:
            message_json = message.model_dump_json(indent=2)
        except Exception as e:
            raise ValueError(f"Failed to serialize message: {e}") from e

        # Write message to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(message_json)
        except PermissionError as e:
            raise PermissionError(
                f"Permission denied when writing to {file_path}"
            ) from e
        except OSError as e:
            raise OSError(
                f"Failed to write message to {file_path}: {e}"
            ) from e

    def __str__(self) -> str:
        """Return string representation of InboxWriter.

        Returns:
            A string showing the workflow directory
        """
        return f"InboxWriter(workflow_dir='{self.workflow_dir}')"

    def __repr__(self) -> str:
        """Return detailed representation of InboxWriter.

        Returns:
            A string that could be used to recreate the object
        """
        return f"InboxWriter(workflow_dir={self.workflow_dir!r})"