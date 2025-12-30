# ABOUTME: MailboxDirectoryManager that ensures INBOX/OUTBOX directories exist
# ABOUTME: Provides paths to INBOX and OUTBOX directories in workflow agent directory

"""MailboxDirectoryManager for workflow agent mailbox directories.

This module provides the MailboxDirectoryManager class which ensures that
INBOX and OUTBOX directories exist in a workflow agent directory and provides
methods to get their paths.

The expected directory structure is:
    workflow_agent_dir/
        - INBOX/           # Directory for incoming messages
        - OUTBOX/          # Directory for outgoing messages
        - other_files...
"""

from pathlib import Path
from typing import Union


class MailboxDirectoryManager:
    """Manager for ensuring INBOX/OUTBOX directories exist in workflow agent directory.

    This class provides functionality to ensure that INBOX and OUTBOX directories
    are created within a workflow agent directory structure, and provides methods
    to get their paths.

    The manager is responsible for:
    - Creating the workflow directory if it doesn't exist
    - Creating INBOX and OUTBOX subdirectories
    - Providing methods to get paths to these directories

    Attributes:
        workflow_dir: The workflow agent directory path
        inbox_dir: Path to the INBOX subdirectory
        outbox_dir: Path to the OUTBOX subdirectory
    """

    def __init__(self, workflow_dir: Union[str, Path]):
        """Initialize MailboxDirectoryManager with a workflow directory.

        Args:
            workflow_dir: The workflow agent directory path (str or Path)

        Raises:
            TypeError: If workflow_dir is None
            ValueError: If workflow_dir is empty string or invalid
        """
        if workflow_dir is None:
            raise TypeError("workflow_dir cannot be None")

        # Convert to Path object if it's a string
        if isinstance(workflow_dir, str):
            if not workflow_dir.strip():
                raise ValueError("workflow_dir cannot be empty")
            workflow_dir = Path(workflow_dir)

        # Ensure we have a Path object
        if not isinstance(workflow_dir, Path):
            raise TypeError(f"workflow_dir must be str or Path, got {type(workflow_dir).__name__}")

        # Resolve to absolute path
        self._workflow_dir = workflow_dir.resolve()

        # Set up INBOX and OUTBOX directory paths
        self._inbox_dir = self._workflow_dir / "INBOX"
        self._outbox_dir = self._workflow_dir / "OUTBOX"

    @property
    def workflow_dir(self) -> Path:
        """Get the workflow directory path."""
        return self._workflow_dir

    @property
    def inbox_dir(self) -> Path:
        """Get the INBOX directory path."""
        return self._inbox_dir

    @property
    def outbox_dir(self) -> Path:
        """Get the OUTBOX directory path."""
        return self._outbox_dir

    def ensure_directories(self) -> None:
        """Create the INBOX and OUTBOX directories if they don't exist.

        This method creates the workflow directory and both INBOX and OUTBOX
        subdirectories. It is safe to call multiple times (idempotent).

        The method uses parents=True to create all intermediate directories
        and exist_ok=True to avoid errors if directories already exist.

        Raises:
            PermissionError: If directories cannot be created due to permissions
            OSError: If there are other I/O errors (disk full, etc.)
        """
        # Create workflow directory first (with parents if needed)
        self._workflow_dir.mkdir(parents=True, exist_ok=True)

        # Create INBOX and OUTBOX directories
        self._inbox_dir.mkdir(exist_ok=True)
        self._outbox_dir.mkdir(exist_ok=True)

    def get_inbox_path(self) -> Path:
        """Get the path to the INBOX directory.

        Returns:
            Path object pointing to the INBOX directory
        """
        return self._inbox_dir

    def get_outbox_path(self) -> Path:
        """Get the path to the OUTBOX directory.

        Returns:
            Path object pointing to the OUTBOX directory
        """
        return self._outbox_dir

    def __str__(self) -> str:
        """Return string representation of MailboxDirectoryManager.

        Returns:
            A string showing the workflow directory path
        """
        return f"MailboxDirectoryManager(workflow_dir='{self._workflow_dir}')"

    def __repr__(self) -> str:
        """Return detailed representation of MailboxDirectoryManager.

        Returns:
            A string that could be used to recreate the object
        """
        return f"MailboxDirectoryManager(workflow_dir={self._workflow_dir!r})"