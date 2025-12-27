# ABOUTME: Mailbox API class providing high-level mailbox operations
# ABOUTME: Integrates message writer/reader and inbox count for complete mailbox management

"""Mailbox API for agent communication.

This module provides the Mailbox class, which offers a high-level API for
agent mailbox communication. It integrates message writing/reading and
inbox count management into a simple, cohesive interface.
"""

from pathlib import Path
from typing import List, Optional

from jean_claude.core.message import Message
from jean_claude.core.mailbox_paths import MailboxPaths
from jean_claude.core.message_writer import write_message, MessageBox
from jean_claude.core.message_reader import read_messages
from jean_claude.core.inbox_count_persistence import (
    read_inbox_count,
    write_inbox_count
)


class Mailbox:
    """High-level API for agent mailbox communication.

    The Mailbox class provides a simple, unified interface for all mailbox
    operations including sending messages, reading messages, and tracking
    unread counts. It encapsulates the complexity of working with separate
    message files and count persistence.

    Typical usage:
        >>> # Initialize mailbox for a workflow
        >>> mailbox = Mailbox(workflow_id="my-workflow")
        >>>
        >>> # Send a message to another agent (outbox)
        >>> msg = Message(
        ...     from_agent="me",
        ...     to_agent="other",
        ...     type="request",
        ...     subject="Help needed",
        ...     body="Can you assist?"
        ... )
        >>> mailbox.send_message(msg)
        >>>
        >>> # Check inbox
        >>> messages = mailbox.get_inbox_messages()
        >>> unread = mailbox.get_unread_count()
        >>>
        >>> # Mark messages as read
        >>> mailbox.mark_as_read()

    Attributes:
        workflow_id: The unique identifier for this workflow
        paths: MailboxPaths object containing all file paths
    """

    def __init__(self, workflow_id: str, base_dir: Optional[Path] = None):
        """Initialize the Mailbox.

        Args:
            workflow_id: The unique identifier for the workflow
            base_dir: Optional base directory for the mailbox. If not provided,
                     uses the default location.

        Raises:
            ValueError: If workflow_id is empty or only whitespace
            TypeError: If workflow_id is None
        """
        # MailboxPaths will validate the workflow_id
        self._paths = MailboxPaths(workflow_id=workflow_id, base_dir=base_dir)

    @property
    def workflow_id(self) -> str:
        """Get the workflow_id for this mailbox."""
        return self._paths.workflow_id

    @property
    def paths(self) -> MailboxPaths:
        """Get the MailboxPaths object for this mailbox."""
        return self._paths

    def send_message(
        self,
        message: Message,
        to_inbox: bool = False
    ) -> None:
        """Send a message to either inbox or outbox.

        This method writes a message to the specified mailbox and updates
        the unread count if sending to the inbox.

        Args:
            message: The Message object to send
            to_inbox: If True, send to inbox (incoming message).
                     If False, send to outbox (outgoing message).
                     Defaults to False (outbox).

        Raises:
            TypeError: If message is not a Message object
            PermissionError: If the file cannot be written due to permissions
            OSError: If there are other I/O errors

        Example:
            >>> mailbox = Mailbox(workflow_id="my-workflow")
            >>>
            >>> # Send outgoing message (default)
            >>> msg = Message(from_agent="me", to_agent="other",
            ...               type="request", subject="Hi", body="Hello")
            >>> mailbox.send_message(msg)
            >>>
            >>> # Receive incoming message
            >>> incoming = Message(from_agent="other", to_agent="me",
            ...                   type="response", subject="Re: Hi", body="Hello!")
            >>> mailbox.send_message(incoming, to_inbox=True)
        """
        # Determine which mailbox to write to
        mailbox_type = MessageBox.INBOX if to_inbox else MessageBox.OUTBOX

        # Write the message
        write_message(message, mailbox_type, self._paths)

        # If sending to inbox, increment the unread count
        if to_inbox:
            inbox_count = read_inbox_count(self._paths)
            inbox_count.increment()
            write_inbox_count(inbox_count, self._paths)

    def get_inbox_messages(self) -> List[Message]:
        """Get all messages from the inbox.

        Returns all messages that have been received in the inbox, regardless
        of whether they've been marked as read.

        Returns:
            A list of Message objects from the inbox. Returns an empty list
            if the inbox is empty or doesn't exist.

        Example:
            >>> mailbox = Mailbox(workflow_id="my-workflow")
            >>> messages = mailbox.get_inbox_messages()
            >>> for msg in messages:
            ...     print(f"From: {msg.from_agent}, Subject: {msg.subject}")
        """
        return read_messages(MessageBox.INBOX, self._paths)

    def get_outbox_messages(self) -> List[Message]:
        """Get all messages from the outbox.

        Returns all messages that have been sent from the outbox.

        Returns:
            A list of Message objects from the outbox. Returns an empty list
            if the outbox is empty or doesn't exist.

        Example:
            >>> mailbox = Mailbox(workflow_id="my-workflow")
            >>> messages = mailbox.get_outbox_messages()
            >>> for msg in messages:
            ...     print(f"To: {msg.to_agent}, Subject: {msg.subject}")
        """
        return read_messages(MessageBox.OUTBOX, self._paths)

    def get_unread_count(self) -> int:
        """Get the number of unread messages in the inbox.

        Returns:
            The number of unread messages. Returns 0 if there are no unread
            messages or if the inbox count file doesn't exist.

        Example:
            >>> mailbox = Mailbox(workflow_id="my-workflow")
            >>> unread = mailbox.get_unread_count()
            >>> print(f"You have {unread} unread messages")
        """
        inbox_count = read_inbox_count(self._paths)
        return inbox_count.unread

    def mark_as_read(self, count: Optional[int] = None) -> None:
        """Mark messages as read.

        This method decrements the unread count by the specified amount.
        If no count is provided, marks all messages as read (sets count to 0).

        The method also updates the last_checked timestamp.

        Args:
            count: The number of messages to mark as read. If None, marks
                  all messages as read. If the count is greater than the
                  number of unread messages, the unread count becomes 0.
                  Defaults to None (mark all as read).

        Example:
            >>> mailbox = Mailbox(workflow_id="my-workflow")
            >>>
            >>> # Mark all messages as read
            >>> mailbox.mark_as_read()
            >>>
            >>> # Mark 3 specific messages as read
            >>> mailbox.mark_as_read(count=3)
        """
        inbox_count = read_inbox_count(self._paths)

        if count is None:
            # Mark all as read
            inbox_count.unread = 0
            inbox_count.update_timestamp()
        else:
            # Mark specified count as read
            for _ in range(count):
                inbox_count.decrement()

        write_inbox_count(inbox_count, self._paths)
