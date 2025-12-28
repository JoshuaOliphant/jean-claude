# ABOUTME: Task validation module for Beads tasks
# ABOUTME: Validates task quality before agent starts work

"""Task validation for Beads tasks.

This module provides validation capabilities to check task quality before
an agent starts work on it. It checks for common issues like vague descriptions,
missing acceptance criteria, and missing test mentions.
"""

import re
from dataclasses import dataclass, field
from typing import List

from jean_claude.core.beads import BeadsTask


@dataclass
class ValidationResult:
    """Result of task validation.

    Attributes:
        is_valid: Whether the task passes all validation checks
        warnings: List of warning messages about task quality
        errors: List of error messages about critical issues
    """

    is_valid: bool = True
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def get_message(self) -> str:
        """Get a formatted message with all warnings and errors."""
        messages = []

        if self.errors:
            messages.append("ERRORS:")
            for error in self.errors:
                messages.append(f"  - {error}")

        if self.warnings:
            messages.append("WARNINGS:")
            for warning in self.warnings:
                messages.append(f"  - {warning}")

        return "\n".join(messages) if messages else "No issues found."

    def to_strict(self) -> "ValidationResult":
        """Convert warnings to errors for strict mode.

        Creates a new ValidationResult where all warnings are converted to errors.
        The original ValidationResult is not modified.

        Returns:
            A new ValidationResult with warnings converted to errors
        """
        # Combine existing errors with converted warnings
        all_errors = list(self.errors) + list(self.warnings)

        # Create new result with all warnings converted to errors
        return ValidationResult(
            is_valid=len(all_errors) == 0,  # Valid only if no errors after conversion
            warnings=[],  # No warnings in strict mode
            errors=all_errors
        )


class TaskValidator:
    """Validates Beads tasks for quality and completeness.

    Checks include:
    - Description length (warns if < 50 chars)
    - Presence of acceptance criteria
    - Mentions of testing/verification
    - Priority field is set (low/medium/high/critical)
    - Type field is set (bug/feature/chore/docs)
    """

    def __init__(self, min_description_length: int = 50):
        """Initialize the task validator.

        Args:
            min_description_length: Minimum character length for description (default: 50)
        """
        self.min_description_length = min_description_length

    def validate(self, task: BeadsTask, strict: bool = False) -> ValidationResult:
        """Validate a Beads task.

        Args:
            task: The BeadsTask to validate
            strict: If True, convert all warnings to errors (default: False)

        Returns:
            ValidationResult with any warnings or errors found.
            In strict mode, warnings are converted to errors.
        """
        result = ValidationResult()

        # Run all validation checks
        self._check_description_length(task, result)
        self._check_acceptance_criteria(task, result)
        self._check_test_mentions(task, result)
        self._check_priority(task, result)
        self._check_task_type(task, result)

        # Mark as invalid if there are errors
        result.is_valid = not result.has_errors()

        # Convert warnings to errors in strict mode
        if strict:
            result = result.to_strict()

        return result

    def _check_description_length(self, task: BeadsTask, result: ValidationResult) -> None:
        """Check if task description is sufficiently detailed.

        Args:
            task: The BeadsTask to check
            result: ValidationResult to add warnings to
        """
        description = task.description.strip()

        if len(description) < self.min_description_length:
            result.warnings.append(
                f"Task description is short ({len(description)} chars). "
                f"Consider adding more detail (recommended: {self.min_description_length}+ chars)."
            )

    def _check_acceptance_criteria(self, task: BeadsTask, result: ValidationResult) -> None:
        """Check if task has acceptance criteria defined.

        Checks both the acceptance_criteria field and searches for common patterns
        in the task description like:
        - ## Acceptance Criteria
        - AC:
        - Success Criteria:
        - Done when:
        - Requirements:
        - ## Checklist

        Args:
            task: The BeadsTask to check
            result: ValidationResult to add warnings to
        """
        # First check if explicit acceptance_criteria field is populated
        has_explicit_criteria = task.acceptance_criteria and len(task.acceptance_criteria) > 0

        # Check for common patterns in description
        has_criteria_in_description = self._has_acceptance_criteria_pattern(task.description)

        # Only warn if neither explicit field nor patterns are found
        if not has_explicit_criteria and not has_criteria_in_description:
            result.warnings.append(
                "No acceptance criteria found. Consider adding clear success criteria."
            )

    def _has_acceptance_criteria_pattern(self, text: str) -> bool:
        """Check if text contains common acceptance criteria patterns.

        Searches for case-insensitive patterns like:
        - ## Acceptance Criteria
        - AC:
        - Acceptance Criteria:
        - Success Criteria:
        - Done when:
        - Requirements:
        - ## Checklist

        Args:
            text: Text to search for patterns

        Returns:
            True if any acceptance criteria pattern is found, False otherwise
        """
        # Normalize text to lowercase for case-insensitive matching
        text_lower = text.lower()

        # Define patterns to search for (all lowercase since we normalized text)
        patterns = [
            r'##\s*acceptance\s+criteria',  # ## Acceptance Criteria
            r'\bac\s*:',  # AC: (word boundary to avoid matching "place:")
            r'acceptance\s+criteria\s*:',  # Acceptance Criteria:
            r'success\s+criteria\s*:',  # Success Criteria:
            r'done\s+when\s*:',  # Done when:
            r'requirements\s*:',  # Requirements:
            r'##\s*checklist',  # ## Checklist
        ]

        # Check if any pattern matches
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    def _check_test_mentions(self, task: BeadsTask, result: ValidationResult) -> None:
        """Check if task mentions testing or verification.

        Uses word boundary detection to avoid false positives from words like
        'contest', 'latest', 'attest', etc.

        Args:
            task: The BeadsTask to check
            result: ValidationResult to add warnings to
        """
        # Combine description and acceptance criteria for searching
        text_to_search = task.description
        if task.acceptance_criteria:
            text_to_search += " " + " ".join(task.acceptance_criteria)

        # Define test-related keywords/patterns with word boundaries to avoid false positives
        # Using \b for word boundaries ensures we match whole words or word stems
        test_patterns = [
            r'\btest\b',           # test (standalone)
            r'\btests\b',          # tests (plural)
            r'\btesting\b',        # testing
            r'\btested\b',         # tested (past tense)
            r'\bverif',            # verify, verifying, verification, verified
            r'\bvalidat',          # validate, validates, validating, validation, validated
            r'\bunit[- ]test',     # unit test, unit-test
            r'\bintegration[- ]test',  # integration test, integration-test
            r'\be2e\b',            # e2e
            r'\bqa\b',             # QA
            r'\bquality assurance\b',  # quality assurance
            r'\bassert\b',         # assert (for assertions)
            r'\bcheck\b',          # check (when used for verification)
            r'\bensure\b',         # ensure (when used for verification)
        ]

        # Check if any pattern matches (case-insensitive)
        has_test_mention = any(
            re.search(pattern, text_to_search, re.IGNORECASE)
            for pattern in test_patterns
        )

        if not has_test_mention:
            result.warnings.append(
                "No mention of testing or verification found. "
                "Consider adding test requirements."
            )

    def _check_priority(self, task: BeadsTask, result: ValidationResult) -> None:
        """Check if task has priority set.

        Args:
            task: The BeadsTask to check
            result: ValidationResult to add warnings to
        """
        if task.priority is None:
            result.warnings.append(
                "Task priority is not set. Consider setting priority (low/medium/high/critical)."
            )

    def _check_task_type(self, task: BeadsTask, result: ValidationResult) -> None:
        """Check if task has type set.

        Args:
            task: The BeadsTask to check
            result: ValidationResult to add warnings to
        """
        if task.task_type is None:
            result.warnings.append(
                "Task type is not set. Consider setting type (bug/feature/chore/docs)."
            )
