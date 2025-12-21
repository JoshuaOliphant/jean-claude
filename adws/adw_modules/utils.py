"""ABOUTME: Utility functions for ADW workflows including JSON parsing, logging, and ID generation.
ABOUTME: Provides common helper functions used across multiple ADW modules."""

import json
import logging
import uuid
import re
from typing import Any, TypeVar, Type, Optional

T = TypeVar('T')


def make_adw_id() -> str:
    """Generate a short 8-character ADW ID."""
    return str(uuid.uuid4())[:8]


def parse_json(text: str, expected_type: Type[T]) -> T:
    """Parse JSON from text, handling markdown code blocks.

    Args:
        text: The text to parse (may contain markdown)
        expected_type: The expected type to return (dict or list)

    Returns:
        Parsed JSON object of expected_type

    Raises:
        ValueError: If parsing fails or result doesn't match expected_type
    """
    # Try direct parsing first
    try:
        result = json.loads(text)
        if isinstance(result, expected_type):
            return result
        raise ValueError(f"Expected {expected_type.__name__}, got {type(result).__name__}")
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    json_pattern = r'```(?:json)?\s*\n(.*?)\n```'
    match = re.search(json_pattern, text, re.DOTALL)

    if match:
        json_str = match.group(1)
        try:
            result = json.loads(json_str)
            if isinstance(result, expected_type):
                return result
            raise ValueError(f"Expected {expected_type.__name__}, got {type(result).__name__}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from markdown block: {e}")

    raise ValueError("No valid JSON found in text")


def setup_logging(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """Set up a logger with consistent formatting.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
        format_string: Custom format string (optional)

    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


def truncate_string(
    text: str,
    max_length: int = 100,
    suffix: str = "..."
) -> str:
    """Truncate a string to a maximum length.

    Args:
        text: The text to truncate
        max_length: Maximum length before truncation
        suffix: Suffix to add when truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing/replacing invalid characters.

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename safe for filesystem use
    """
    # Replace invalid characters with underscores
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')

    # Collapse multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)

    return sanitized


def extract_issue_number_from_branch(branch_name: str) -> Optional[str]:
    """Extract issue number from a branch name.

    Supports patterns like:
    - issue-123-description
    - feat-issue-123-description
    - bug/issue-123

    Args:
        branch_name: The branch name

    Returns:
        Issue number as string, or None if not found
    """
    # Try pattern: issue-123
    match = re.search(r'issue-(\d+)', branch_name)
    if match:
        return match.group(1)

    # Try pattern for beads: poc-abc, feat-xyz
    match = re.search(r'([a-z]+-[a-z0-9]+)', branch_name)
    if match:
        return match.group(1)

    return None


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "2m 30s", "1h 15m")
    """
    if seconds < 60:
        return f"{seconds:.0f}s"

    minutes = seconds // 60
    remaining_seconds = seconds % 60

    if minutes < 60:
        if remaining_seconds > 0:
            return f"{minutes:.0f}m {remaining_seconds:.0f}s"
        return f"{minutes:.0f}m"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes > 0:
        return f"{hours:.0f}h {remaining_minutes:.0f}m"
    return f"{hours:.0f}h"


def ensure_trailing_newline(text: str) -> str:
    """Ensure text ends with exactly one newline.

    Args:
        text: The text to process

    Returns:
        Text with exactly one trailing newline
    """
    return text.rstrip('\n') + '\n'


def is_valid_adw_id(adw_id: str) -> bool:
    """Check if a string is a valid ADW ID.

    Valid ADW IDs are 8-character alphanumeric strings.

    Args:
        adw_id: The ID to validate

    Returns:
        True if valid, False otherwise
    """
    if not adw_id or len(adw_id) != 8:
        return False

    return adw_id.isalnum()
