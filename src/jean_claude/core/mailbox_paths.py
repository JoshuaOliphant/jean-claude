# ABOUTME: MailboxPaths class for generating mailbox file paths
# ABOUTME: Generates paths for inbox.jsonl, outbox.jsonl, and inbox_count.json

"""MailboxPaths class and utilities for agent mailbox communication.

This module provides the MailboxPaths class which generates correct paths
for mailbox files (inbox.jsonl, outbox.jsonl, and inbox_count.json) given
a workflow_id. It also includes utilities for creating the mailbox directory
structure.
"""

from pathlib import Path
from typing import Optional


class MailboxPaths:
    """Helper class for generating mailbox file paths.

    This class provides a centralized way to generate consistent paths for
    all mailbox-related files within a workflow directory structure.

    The expected directory structure is:
        base_dir/workflow_id/mailbox/
            - inbox.jsonl
            - outbox.jsonl
            - inbox_count.json

    Attributes:
        workflow_id: The unique identifier for the workflow
        base_dir: The base directory containing all agent workflows
        mailbox_dir: The mailbox directory for this workflow
        inbox_path: Path to the inbox.jsonl file
        outbox_path: Path to the outbox.jsonl file
        inbox_count_path: Path to the inbox_count.json file
    """

    def __init__(self, workflow_id: str, base_dir: Optional[Path] = None):
        """Initialize MailboxPaths with a workflow_id.

        Args:
            workflow_id: The unique identifier for the workflow
            base_dir: Optional base directory for agents. If not provided,
                     uses the default agents directory.

        Raises:
            ValueError: If workflow_id is empty or only whitespace
            TypeError: If workflow_id is None
        """
        if workflow_id is None:
            raise TypeError("workflow_id cannot be None")

        if not workflow_id or not workflow_id.strip():
            raise ValueError("workflow_id cannot be empty")

        self._workflow_id = workflow_id

        # Set base_dir to provided value or use default
        if base_dir is None:
            # Default to agents directory in the project root
            # This assumes the typical structure where code is in src/
            # and agents/ is at the project root
            project_root = Path(__file__).resolve().parent.parent.parent
            self._base_dir = project_root / "agents"
        else:
            self._base_dir = base_dir

        # Ensure base_dir is absolute
        self._base_dir = self._base_dir.resolve()

        # Construct the mailbox directory path
        self._mailbox_dir = self._base_dir / self._workflow_id / "mailbox"

        # Construct paths for mailbox files
        self._inbox_path = self._mailbox_dir / "inbox.jsonl"
        self._outbox_path = self._mailbox_dir / "outbox.jsonl"
        self._inbox_count_path = self._mailbox_dir / "inbox_count.json"

    @property
    def workflow_id(self) -> str:
        """Get the workflow_id."""
        return self._workflow_id

    @property
    def base_dir(self) -> Path:
        """Get the base directory for agents."""
        return self._base_dir

    @property
    def mailbox_dir(self) -> Path:
        """Get the mailbox directory path."""
        return self._mailbox_dir

    @property
    def inbox_path(self) -> Path:
        """Get the path to inbox.jsonl."""
        return self._inbox_path

    @property
    def outbox_path(self) -> Path:
        """Get the path to outbox.jsonl."""
        return self._outbox_path

    @property
    def inbox_count_path(self) -> Path:
        """Get the path to inbox_count.json."""
        return self._inbox_count_path

    def ensure_mailbox_dir(self) -> None:
        """Create the mailbox directory if it doesn't exist.

        This method creates the mailbox directory and all necessary parent
        directories. It is safe to call multiple times (idempotent).

        The method uses parents=True to create all intermediate directories
        and exist_ok=True to avoid errors if the directory already exists.
        """
        self._mailbox_dir.mkdir(parents=True, exist_ok=True)

    def __str__(self) -> str:
        """Return string representation of MailboxPaths.

        Returns:
            A string showing the workflow_id and mailbox directory
        """
        return f"MailboxPaths(workflow_id='{self._workflow_id}', mailbox_dir='{self._mailbox_dir}')"

    def __repr__(self) -> str:
        """Return detailed representation of MailboxPaths.

        Returns:
            A string that could be used to recreate the object
        """
        return f"MailboxPaths(workflow_id='{self._workflow_id}', base_dir={self._base_dir!r})"
