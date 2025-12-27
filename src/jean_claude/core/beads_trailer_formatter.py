"""BeadsTrailerFormatter for formatting Beads task metadata as git trailers.

This module provides functionality to format Beads task IDs and feature numbers
as git commit trailers for traceability.
"""

import re
from typing import Any, Dict


class BeadsTrailerFormatter:
    """Formats Beads task metadata as git commit trailers.

    Git trailers are key-value pairs at the end of commit messages that provide
    structured metadata. This class formats Beads task IDs and feature progress
    information as standard git trailers.

    The formatted output includes:
    - Beads: The unique identifier for the Beads task
    - Feature: Progress indicator in "X/Y" format

    Attributes:
        task_id: The Beads task identifier (e.g., 'jean_claude-2sz.8')
        feature_number: Current feature number (must be positive)
        total_features: Total number of features (must be positive)
    """

    # Task ID format: at least one character, followed by a period, followed by at least one digit
    TASK_ID_PATTERN = re.compile(r'^.+\.\d+$')

    def __init__(
        self,
        task_id: str,
        feature_number: int,
        total_features: int,
    ):
        """Initialize the BeadsTrailerFormatter.

        Args:
            task_id: The Beads task identifier (format: 'name.number')
            feature_number: Current feature number (1-indexed)
            total_features: Total number of features in the workflow

        Raises:
            ValueError: If validation fails for any parameter
        """
        # Validate task_id format
        if not task_id or not task_id.strip():
            raise ValueError("Invalid task_id format: task_id cannot be empty")

        if not self.TASK_ID_PATTERN.match(task_id.strip()):
            raise ValueError(
                f"Invalid task_id format: '{task_id}'. "
                "Expected format: 'name.number' (e.g., 'project-123.1')"
            )

        # Validate feature_number
        if feature_number <= 0:
            raise ValueError("feature_number must be positive")

        # Validate total_features
        if total_features <= 0:
            raise ValueError("total_features must be positive")

        # Validate feature_number <= total_features
        if feature_number > total_features:
            raise ValueError(
                f"feature_number ({feature_number}) cannot exceed "
                f"total_features ({total_features})"
            )

        self.task_id = task_id
        self.feature_number = feature_number
        self.total_features = total_features

    @classmethod
    def from_task_metadata(cls, metadata: Dict[str, Any]) -> "BeadsTrailerFormatter":
        """Create a BeadsTrailerFormatter from task metadata.

        Extracts the Beads task ID, current feature index, and total features
        from the task metadata dictionary.

        Args:
            metadata: Dictionary containing task metadata with keys:
                - beads_task_id: The Beads task identifier
                - current_feature_index: The 0-indexed current feature index
                - features: List of features (used to determine total count)

        Returns:
            A BeadsTrailerFormatter instance configured from the metadata

        Raises:
            ValueError: If required metadata is missing or invalid
        """
        # Validate required fields
        if "beads_task_id" not in metadata:
            raise ValueError("beads_task_id is required in task metadata")

        if "current_feature_index" not in metadata:
            raise ValueError("current_feature_index is required in task metadata")

        if "features" not in metadata:
            raise ValueError("features is required in task metadata")

        # Validate features is a list
        features = metadata["features"]
        if not isinstance(features, list):
            raise ValueError("features must be a list")

        # Validate features is not empty
        if len(features) == 0:
            raise ValueError("features cannot be empty")

        # Extract values
        task_id = metadata["beads_task_id"]
        current_feature_index = metadata["current_feature_index"]
        total_features = len(features)

        # Convert 0-indexed feature index to 1-indexed feature number
        feature_number = current_feature_index + 1

        return cls(
            task_id=task_id,
            feature_number=feature_number,
            total_features=total_features
        )

    def format(self) -> str:
        """Generate the formatted git trailers.

        Returns:
            A string containing the formatted trailers, with one trailer per line.

        Example:
            >>> formatter = BeadsTrailerFormatter(
            ...     task_id="jean_claude-2sz.8",
            ...     feature_number=2,
            ...     total_features=9
            ... )
            >>> print(formatter.format())
            Beads: jean_claude-2sz.8
            Feature: 2/9
        """
        lines = [
            f"Beads: {self.task_id}",
            f"Feature: {self.feature_number}/{self.total_features}"
        ]

        return "\n".join(lines)
