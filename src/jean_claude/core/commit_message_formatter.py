"""CommitMessageFormatter for generating conventional commit messages.

This module provides functionality to generate properly formatted conventional
commit messages from feature metadata.
"""

from typing import Optional


class CommitMessageFormatter:
    """Generates conventional commit messages from feature metadata.

    Conventional Commits specification: https://www.conventionalcommits.org/

    The formatter creates commit messages with the following structure:
    - Header: <type>(<scope>): <summary>
    - Body: Bulleted list of changes (optional)
    - Trailers: Beads-Task-Id and Feature-Number

    Attributes:
        commit_type: Type of commit (feat, fix, refactor, test, docs)
        scope: Optional scope of the change (e.g., 'auth', 'api', 'ui')
        summary: Short description of the change
        body_items: List of detailed changes (optional)
        beads_task_id: Identifier for the Beads task
        feature_number: Feature number in the workflow
    """

    VALID_COMMIT_TYPES = {"feat", "fix", "refactor", "test", "docs"}

    def __init__(
        self,
        commit_type: str,
        scope: Optional[str],
        summary: str,
        body_items: list[str],
        beads_task_id: str,
        feature_number: int,
    ):
        """Initialize the CommitMessageFormatter.

        Args:
            commit_type: Type of commit (feat, fix, refactor, test, docs)
            scope: Optional scope of the change
            summary: Short description of the change
            body_items: List of detailed changes
            beads_task_id: Identifier for the Beads task
            feature_number: Feature number in the workflow

        Raises:
            ValueError: If commit_type is invalid, summary is empty, or feature_number is not positive
        """
        if commit_type not in self.VALID_COMMIT_TYPES:
            raise ValueError(
                f"Invalid commit_type: {commit_type}. "
                f"Must be one of: {', '.join(sorted(self.VALID_COMMIT_TYPES))}"
            )

        if not summary or not summary.strip():
            raise ValueError("summary cannot be empty")

        if feature_number <= 0:
            raise ValueError("feature_number must be positive")

        self.commit_type = commit_type
        self.scope = scope
        self.summary = summary.strip()
        self.body_items = body_items
        self.beads_task_id = beads_task_id
        self.feature_number = feature_number

    def format(self) -> str:
        """Generate the formatted commit message.

        Returns:
            A properly formatted conventional commit message string.

        Example:
            >>> formatter = CommitMessageFormatter(
            ...     commit_type="feat",
            ...     scope="auth",
            ...     summary="add login functionality",
            ...     body_items=["Implement JWT authentication", "Add password hashing"],
            ...     beads_task_id="task-123.1",
            ...     feature_number=1
            ... )
            >>> message = formatter.format()
            >>> print(message)
            feat(auth): add login functionality

            - Implement JWT authentication
            - Add password hashing

            Beads-Task-Id: task-123.1
            Feature-Number: 1
        """
        parts = []

        # Header: type(scope): summary or type: summary
        if self.scope:
            header = f"{self.commit_type}({self.scope}): {self.summary}"
        else:
            header = f"{self.commit_type}: {self.summary}"

        parts.append(header)

        # Body: bulleted list of changes (if any)
        if self.body_items:
            parts.append("")  # Blank line after header
            for item in self.body_items:
                parts.append(f"- {item}")

        # Trailers: Beads-Task-Id and Feature-Number
        if self.body_items:
            parts.append("")  # Blank line before trailers if we have body
        else:
            parts.append("")  # Blank line after header

        parts.append(f"Beads-Task-Id: {self.beads_task_id}")
        parts.append(f"Feature-Number: {self.feature_number}")

        return "\n".join(parts)
