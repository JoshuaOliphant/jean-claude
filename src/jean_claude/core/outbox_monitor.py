# ABOUTME: OutboxMonitor class for polling OUTBOX directory for new messages
# ABOUTME: Provides high-level interface for monitoring and parsing messages from agent outboxes

"""OutboxMonitor for agent mailbox communication.

This module provides the OutboxMonitor class that polls OUTBOX directories
for new message files and returns parsed Message objects. It provides a simple
interface for detecting when users or other agents have placed responses in
the outbox.

The monitor scans the OUTBOX directory for JSON files, attempts to parse each
file as a Message object, and returns a list of successfully parsed messages.
It handles errors gracefully by skipping invalid or corrupted files.
"""

import json
from pathlib import Path
from typing import List, Union

from pydantic import ValidationError

from jean_claude.core.message import Message
from jean_claude.core.mailbox_directory_manager import MailboxDirectoryManager


class OutboxMonitor:
    """Monitor for polling OUTBOX directories for new messages.

    OutboxMonitor provides functionality to poll OUTBOX directories within a
    workflow and return parsed Message objects found in JSON files. It handles
    directory scanning, file parsing, and error recovery gracefully.

    The monitor looks for all .json files in the OUTBOX directory and attempts
    to parse each one as a Message object. Invalid files are silently skipped
    to ensure robust operation.

    Attributes:
        workflow_dir: Path to the workflow directory containing the OUTBOX
        _directory_manager: MailboxDirectoryManager for directory operations
    """

    def __init__(self, workflow_dir: Union[str, Path]):
        """Initialize OutboxMonitor with workflow directory.

        Args:
            workflow_dir: Path to the workflow directory where OUTBOX should be monitored

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

    def poll_for_new_messages(self) -> List[Message]:
        """Poll the OUTBOX directory for new message files.

        This method scans the OUTBOX directory for JSON files and attempts to
        parse each file as a Message object. Successfully parsed messages are
        returned in a list. Invalid or corrupted files are silently skipped.

        The method handles various error conditions gracefully:
        - Missing OUTBOX directory returns empty list
        - Permission errors return empty list
        - Invalid JSON files are skipped
        - Files missing required Message fields are skipped

        Returns:
            List of Message objects found in the OUTBOX directory.
            Returns empty list if no valid messages found or if errors occur.

        Example:
            >>> from jean_claude.core.outbox_monitor import OutboxMonitor
            >>>
            >>> # Monitor outbox for new messages
            >>> monitor = OutboxMonitor("/path/to/workflow")
            >>> messages = monitor.poll_for_new_messages()
            >>>
            >>> # Process each message
            >>> for message in messages:
            ...     print(f"New message from {message.from_agent}: {message.subject}")
        """
        try:
            # Get outbox directory path
            outbox_path = self._directory_manager.get_outbox_path()

            # If outbox doesn't exist, return empty list
            if not outbox_path.exists():
                return []

            # Scan for JSON files in outbox
            try:
                json_files = list(outbox_path.glob("*.json"))
            except (PermissionError, OSError):
                # Handle permission or I/O errors gracefully
                return []

            # Parse each JSON file into Message objects
            messages = []
            for json_file in json_files:
                try:
                    # Read the JSON file
                    with open(json_file, 'r', encoding='utf-8') as f:
                        file_content = f.read().strip()

                    # Skip empty files
                    if not file_content:
                        continue

                    # Parse JSON content
                    try:
                        message_data = json.loads(file_content)
                    except json.JSONDecodeError:
                        # Skip files with invalid JSON
                        continue

                    # Validate and create Message object
                    try:
                        message = Message(**message_data)
                        messages.append(message)
                    except (ValidationError, TypeError, ValueError):
                        # Skip files that don't represent valid Message objects
                        continue

                except (PermissionError, OSError, UnicodeDecodeError):
                    # Skip files that can't be read
                    continue

            # Sort messages by creation time (newest first)
            # Note: created_at is a datetime field in the Message model
            try:
                messages.sort(key=lambda msg: msg.created_at, reverse=False)
            except (AttributeError, TypeError):
                # If sorting fails, return messages in arbitrary order
                pass

            return messages

        except Exception:
            # Handle any unexpected errors by returning empty list
            # This ensures the monitor is robust and doesn't crash the calling code
            return []

    def __str__(self) -> str:
        """Return string representation of OutboxMonitor.

        Returns:
            A string showing the workflow directory
        """
        return f"OutboxMonitor(workflow_dir='{self.workflow_dir}')"

    def __repr__(self) -> str:
        """Return detailed representation of OutboxMonitor.

        Returns:
            A string that could be used to recreate the object
        """
        return f"OutboxMonitor(workflow_dir={self.workflow_dir!r})"