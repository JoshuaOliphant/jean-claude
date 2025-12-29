"""File utility functions for reading and processing files."""

import json
from pathlib import Path
from typing import Generator, Union


def read_jsonl_file(file_path: Union[str, Path]) -> Generator[dict, None, None]:
    """
    Read a JSONL (JSON Lines) file line by line and yield parsed dictionaries.

    This function reads a JSONL file where each line contains a separate JSON object.
    It handles errors gracefully by:
    - Skipping invalid JSON lines silently
    - Skipping empty lines and whitespace-only lines
    - Returning an empty generator if the file doesn't exist

    Args:
        file_path: Path to the JSONL file (can be string or Path object)

    Yields:
        dict: Parsed JSON object from each valid line

    Example:
        >>> for record in read_jsonl_file('data.jsonl'):
        ...     print(record['id'], record['name'])
    """
    # Convert to Path object if it's a string
    path = Path(file_path)

    # Handle missing files gracefully - return empty generator
    if not path.exists():
        return

    # Read file line by line
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                # Skip empty lines and whitespace-only lines
                line = line.strip()
                if not line:
                    continue

                # Try to parse JSON, skip invalid lines silently
                try:
                    data = json.loads(line)
                    yield data
                except json.JSONDecodeError:
                    # Silently skip invalid JSON lines
                    continue
    except (IOError, OSError):
        # Handle file read errors gracefully
        return
