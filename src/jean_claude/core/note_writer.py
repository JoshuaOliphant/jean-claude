# ABOUTME: Note writer module for appending notes to the shared notes file
# ABOUTME: Implements write_note function for JSONL serialization to notes.jsonl

"""Note writer module for agent note-taking system.

This module provides the write_note function that appends Note objects
to the notes.jsonl file. It handles JSONL serialization, directory creation,
and error handling gracefully.
"""

from jean_claude.core.notes import Note
from jean_claude.core.notes_paths import NotesPaths


def write_note(note: Note, paths: NotesPaths) -> None:
    """Write a note to the notes file.

    This function appends a Note to notes.jsonl using JSONL (JSON Lines)
    format. Each note is written as a single line of JSON. The function
    creates the notes directory if it doesn't exist and handles errors
    gracefully.

    Args:
        note: The Note object to write
        paths: NotesPaths object containing the file paths

    Raises:
        TypeError: If note is not a Note object
        PermissionError: If the file cannot be written due to permissions
        OSError: If there are other I/O errors (disk full, etc.)

    Example:
        >>> from jean_claude.core.notes import Note, NoteCategory
        >>> from jean_claude.core.note_writer import write_note
        >>> from jean_claude.core.notes_paths import NotesPaths
        >>>
        >>> # Create a note
        >>> note = Note(
        ...     agent_id="coder-agent",
        ...     category=NoteCategory.LEARNING,
        ...     title="Found a bug in auth module",
        ...     content="The auth module has a race condition..."
        ... )
        >>>
        >>> # Set up paths
        >>> paths = NotesPaths(workflow_id="my-workflow")
        >>>
        >>> # Write the note
        >>> write_note(note, paths)
    """
    # Validate note type
    if not isinstance(note, Note):
        raise TypeError(
            f"note must be a Note object, got {type(note).__name__}"
        )

    # Ensure the notes directory exists
    paths.ensure_notes_dir()

    # Serialize the note to JSON (single line, no indentation)
    json_line = note.model_dump_json() + "\n"

    # Append the JSON line to the file
    try:
        with open(paths.notes_path, "a", encoding="utf-8") as f:
            f.write(json_line)
            f.flush()  # Ensure immediate write for streaming
    except PermissionError as e:
        # Re-raise permission errors with more context
        raise PermissionError(
            f"Permission denied when writing to {paths.notes_path}"
        ) from e
    except OSError as e:
        # Re-raise OS errors (disk full, etc.) with more context
        raise OSError(
            f"Failed to write note to {paths.notes_path}: {e}"
        ) from e
