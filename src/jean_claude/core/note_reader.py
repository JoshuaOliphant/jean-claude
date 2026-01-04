# ABOUTME: Note reader module for reading notes from the shared notes file
# ABOUTME: Implements read_notes function for parsing JSONL from notes.jsonl

"""Note reader module for agent note-taking system.

This module provides the read_notes function that reads all notes
from the notes.jsonl file. It handles JSONL parsing, gracefully handles
missing or corrupted files by returning an empty list, and validates
note data.
"""

import json

from pydantic import ValidationError

from jean_claude.core.notes import Note, NoteCategory
from jean_claude.core.notes_paths import NotesPaths


def read_notes(
    paths: NotesPaths,
    agent_id: str | None = None,
    category: NoteCategory | None = None,
    tag: str | None = None,
    limit: int | None = None,
) -> list[Note]:
    """Read notes from the notes file with optional filtering.

    This function reads notes from notes.jsonl, parsing each line as a JSON
    object and converting it to a Note object. It handles missing files,
    empty files, and corrupted data gracefully by returning an empty list
    or skipping invalid lines.

    Args:
        paths: NotesPaths object containing the file paths
        agent_id: Optional filter by agent ID
        category: Optional filter by note category
        tag: Optional filter by tag (notes containing this tag)
        limit: Optional maximum number of notes to return (most recent first)

    Returns:
        A list of Note objects read from the file. Returns an empty list
        if the file doesn't exist, is empty, or contains no valid notes.
        Notes are returned in chronological order (oldest first) unless
        limit is specified, in which case most recent notes are returned.

    Example:
        >>> from jean_claude.core.note_reader import read_notes
        >>> from jean_claude.core.notes_paths import NotesPaths
        >>> from jean_claude.core.notes import NoteCategory
        >>>
        >>> # Set up paths
        >>> paths = NotesPaths(workflow_id="my-workflow")
        >>>
        >>> # Read all notes
        >>> notes = read_notes(paths)
        >>>
        >>> # Read only learning notes
        >>> learning_notes = read_notes(paths, category=NoteCategory.LEARNING)
        >>>
        >>> # Read notes from a specific agent
        >>> agent_notes = read_notes(paths, agent_id="coder-agent")
        >>>
        >>> # Read last 5 notes
        >>> recent_notes = read_notes(paths, limit=5)
    """
    # If the file doesn't exist, return an empty list
    if not paths.notes_path.exists():
        return []

    # Read and parse notes from the file
    notes: list[Note] = []

    try:
        with open(paths.notes_path, encoding="utf-8") as f:
            for line in f:
                # Skip empty lines or lines with only whitespace
                line = line.strip()
                if not line:
                    continue

                # Try to parse the JSON line
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    # Skip invalid JSON lines silently
                    continue

                # Try to create a Note object from the data
                try:
                    note = Note(**data)

                    # Apply filters
                    if agent_id and note.agent_id != agent_id:
                        continue

                    if category and note.category != category:
                        continue

                    if tag and tag not in note.tags:
                        continue

                    notes.append(note)
                except (ValidationError, TypeError):
                    # Skip invalid note data silently
                    continue

    except OSError:
        # If there's an error reading the file, return empty list
        return []

    # If limit is specified, return most recent notes
    if limit is not None and limit > 0:
        notes = notes[-limit:]

    return notes


def search_notes(
    paths: NotesPaths,
    query: str,
    search_content: bool = True,
    search_title: bool = True,
) -> list[Note]:
    """Search notes by text query.

    This function searches notes for the given query string in the title
    and/or content fields.

    Args:
        paths: NotesPaths object containing the file paths
        query: The text query to search for (case-insensitive)
        search_content: Whether to search in note content (default True)
        search_title: Whether to search in note title (default True)

    Returns:
        A list of Note objects matching the query. Returns an empty list
        if no matches are found or if the file doesn't exist.

    Example:
        >>> from jean_claude.core.note_reader import search_notes
        >>> from jean_claude.core.notes_paths import NotesPaths
        >>>
        >>> paths = NotesPaths(workflow_id="my-workflow")
        >>> results = search_notes(paths, "authentication")
    """
    if not query or not query.strip():
        return []

    query_lower = query.lower().strip()
    all_notes = read_notes(paths)
    matching_notes = []

    for note in all_notes:
        matches = False

        if search_title and query_lower in note.title.lower():
            matches = True

        if search_content and query_lower in note.content.lower():
            matches = True

        if matches:
            matching_notes.append(note)

    return matching_notes
