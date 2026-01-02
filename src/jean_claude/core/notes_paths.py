# ABOUTME: NotesPaths class for generating notes file paths
# ABOUTME: Generates paths for notes.jsonl in agents/{workflow_id}/notes/

"""NotesPaths class and utilities for agent note-taking system.

This module provides the NotesPaths class which generates correct paths
for notes files given a workflow_id. Notes are stored in JSONL format
for easy appending and streaming.
"""

from pathlib import Path


class NotesPaths:
    """Helper class for generating notes file paths.

    This class provides a centralized way to generate consistent paths for
    notes-related files within a workflow directory structure.

    The expected directory structure is:
        base_dir/workflow_id/notes/
            - notes.jsonl

    Attributes:
        workflow_id: The unique identifier for the workflow
        base_dir: The base directory containing all agent workflows
        notes_dir: The notes directory for this workflow
        notes_path: Path to the notes.jsonl file
    """

    def __init__(self, workflow_id: str, base_dir: Path | None = None):
        """Initialize NotesPaths with a workflow_id.

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

        # Construct the notes directory path
        self._notes_dir = self._base_dir / self._workflow_id / "notes"

        # Construct path for notes file
        self._notes_path = self._notes_dir / "notes.jsonl"

    @property
    def workflow_id(self) -> str:
        """Get the workflow_id."""
        return self._workflow_id

    @property
    def base_dir(self) -> Path:
        """Get the base directory for agents."""
        return self._base_dir

    @property
    def notes_dir(self) -> Path:
        """Get the notes directory path."""
        return self._notes_dir

    @property
    def notes_path(self) -> Path:
        """Get the path to notes.jsonl."""
        return self._notes_path

    def ensure_notes_dir(self) -> None:
        """Create the notes directory if it doesn't exist.

        This method creates the notes directory and all necessary parent
        directories. It is safe to call multiple times (idempotent).

        The method uses parents=True to create all intermediate directories
        and exist_ok=True to avoid errors if the directory already exists.
        """
        self._notes_dir.mkdir(parents=True, exist_ok=True)

    def __str__(self) -> str:
        """Return string representation of NotesPaths.

        Returns:
            A string showing the workflow_id and notes directory
        """
        return f"NotesPaths(workflow_id='{self._workflow_id}', notes_dir='{self._notes_dir}')"

    def __repr__(self) -> str:
        """Return detailed representation of NotesPaths.

        Returns:
            A string that could be used to recreate the object
        """
        return f"NotesPaths(workflow_id='{self._workflow_id}', base_dir={self._base_dir!r})"
