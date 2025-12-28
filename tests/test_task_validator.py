# ABOUTME: Tests for TaskValidator and ValidationResult
# ABOUTME: Consolidated test suite for task validation logic

"""Tests for TaskValidator and ValidationResult.

Consolidated from 31 separate tests to focused tests covering
essential behaviors without per-keyword redundancy.
"""

import pytest

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus
from jean_claude.core.task_validator import TaskValidator, ValidationResult


class TestValidationResult:
    """Test ValidationResult dataclass - consolidated from 10 tests to 2."""

    def test_validation_result_defaults_and_methods(self):
        """Test ValidationResult initialization and helper methods."""
        # Default initialization
        result1 = ValidationResult()
        assert result1.is_valid is True
        assert result1.warnings == []
        assert result1.errors == []
        assert result1.has_warnings() is False
        assert result1.has_errors() is False
        assert result1.get_message() == "No issues found."

        # With values
        result2 = ValidationResult(
            is_valid=False,
            warnings=["Warning 1", "Warning 2"],
            errors=["Error 1"]
        )
        assert result2.is_valid is False
        assert len(result2.warnings) == 2
        assert len(result2.errors) == 1
        assert result2.has_warnings() is True
        assert result2.has_errors() is True

    def test_validation_result_message_formatting(self):
        """Test that get_message formats warnings and errors correctly."""
        # Warnings only
        result1 = ValidationResult(warnings=["Warning 1", "Warning 2"])
        message1 = result1.get_message()
        assert "WARNINGS:" in message1
        assert "Warning 1" in message1
        assert "Warning 2" in message1

        # Errors only
        result2 = ValidationResult(errors=["Error 1", "Error 2"])
        message2 = result2.get_message()
        assert "ERRORS:" in message2
        assert "Error 1" in message2

        # Both
        result3 = ValidationResult(warnings=["Warning 1"], errors=["Error 1"])
        message3 = result3.get_message()
        assert "WARNINGS:" in message3
        assert "ERRORS:" in message3


class TestTaskValidatorInit:
    """Test TaskValidator initialization - consolidated from 2 tests to 1."""

    def test_init_with_defaults_and_custom(self):
        """Test initialization with default and custom values."""
        validator1 = TaskValidator()
        assert validator1.min_description_length == 50

        validator2 = TaskValidator(min_description_length=100)
        assert validator2.min_description_length == 100


class TestTaskValidatorDescriptionLength:
    """Test description length validation - consolidated from 4 tests to 1."""

    def test_description_length_validation(self, mock_beads_task_factory):
        """Test short, long, and edge case descriptions."""
        validator = TaskValidator(min_description_length=50)

        # Short description triggers warning
        short_task = mock_beads_task_factory(description="Short")
        result1 = validator.validate(short_task)
        assert result1.is_valid is True
        assert result1.has_warnings() is True
        desc_warnings = [w for w in result1.warnings if "description is short" in w.lower()]
        assert len(desc_warnings) == 1
        assert "5 chars" in desc_warnings[0]

        # Long description - no description warning
        long_task = mock_beads_task_factory(
            description="This is a very detailed description with enough information to be clear about what needs to be done.",
            acceptance_criteria=["Criterion 1"]
        )
        result2 = validator.validate(long_task)
        desc_warnings2 = [w for w in result2.warnings if "description is short" in w.lower()]
        assert len(desc_warnings2) == 0

        # Empty/whitespace descriptions caught by Pydantic - must stay inline
        with pytest.raises(ValueError, match="description cannot be empty"):
            BeadsTask(id="test-3", title="Test", description="", status=BeadsTaskStatus.OPEN)

        with pytest.raises(ValueError, match="description cannot be empty"):
            BeadsTask(id="test-4", title="Test", description="   ", status=BeadsTaskStatus.OPEN)


class TestTaskValidatorAcceptanceCriteria:
    """Test acceptance criteria validation - consolidated from 3 tests to 1."""

    def test_acceptance_criteria_validation(self, mock_beads_task_factory):
        """Test missing, empty, and present acceptance criteria."""
        validator = TaskValidator(min_description_length=10)

        # Missing AC triggers warning (factory default is empty list)
        no_ac_task = mock_beads_task_factory(description="A task description")
        result1 = validator.validate(no_ac_task)
        ac_warnings1 = [w for w in result1.warnings if "acceptance criteria" in w.lower()]
        assert len(ac_warnings1) == 1

        # Empty AC list triggers warning
        empty_ac_task = mock_beads_task_factory(
            description="A task description",
            acceptance_criteria=[]
        )
        result2 = validator.validate(empty_ac_task)
        ac_warnings2 = [w for w in result2.warnings if "acceptance criteria" in w.lower()]
        assert len(ac_warnings2) == 1

        # Present AC - no warning
        with_ac_task = mock_beads_task_factory(
            description="A task description with test mention",
            acceptance_criteria=["Criterion 1"]
        )
        result3 = validator.validate(with_ac_task)
        ac_warnings3 = [w for w in result3.warnings if "acceptance criteria" in w.lower()]
        assert len(ac_warnings3) == 0


class TestTaskValidatorTestMentions:
    """Test test mention validation - consolidated from 8 tests to 1."""

    @pytest.mark.parametrize("description,should_warn", [
        ("A task description about adding a new feature only", True),
        ("A task that mentions we need to test the feature", False),
        ("A task requiring thorough testing of the implementation", False),
        ("Verify that the implementation works correctly", False),
        ("Include verification steps in the process", False),
        ("Ensure the feature is validated before deployment", False),
        ("Must TEST the functionality thoroughly", False),  # Case insensitive
    ])
    def test_test_mention_detection_in_description(self, mock_beads_task_factory, description, should_warn):
        """Test that various test/verification keywords are detected."""
        validator = TaskValidator(min_description_length=10)
        task = mock_beads_task_factory(
            description=description,
            acceptance_criteria=["Criterion 1"]
        )

        result = validator.validate(task)
        test_warnings = [w for w in result.warnings if "testing or verification" in w.lower()]
        assert (len(test_warnings) > 0) == should_warn

    def test_test_keyword_in_acceptance_criteria(self, mock_beads_task_factory):
        """Test that test keywords in acceptance criteria are detected."""
        validator = TaskValidator(min_description_length=10)
        task = mock_beads_task_factory(
            description="A task description",
            acceptance_criteria=["All tests pass", "Feature works correctly"]
        )

        result = validator.validate(task)
        test_warnings = [w for w in result.warnings if "testing or verification" in w.lower()]
        assert len(test_warnings) == 0


class TestTaskValidatorIntegration:
    """Integration tests - consolidated from 4 tests to 2."""

    def test_perfect_task_no_warnings(self):
        """Test that a well-formed task passes without warnings."""
        validator = TaskValidator(min_description_length=50)
        # This test needs all fields set including priority/task_type
        # which the factory doesn't support, so use inline creation
        task = BeadsTask(
            id="test-1",
            title="Test Task",
            description="This is a detailed task description that contains enough information and mentions that we need to test the implementation thoroughly.",
            acceptance_criteria=["Feature works", "All tests pass"],
            status=BeadsTaskStatus.OPEN,
            priority="medium",
            task_type="feature"
        )

        result = validator.validate(task)
        assert result.is_valid is True
        assert result.has_warnings() is False
        assert result.has_errors() is False
        assert isinstance(result, ValidationResult)

    def test_poor_task_multiple_warnings(self, mock_beads_task_factory):
        """Test that a poorly-formed task generates multiple warnings."""
        validator = TaskValidator(min_description_length=50)
        task = mock_beads_task_factory(
            title="Test Task",
            description="Short"  # Too short, no test mention, no AC
        )

        result = validator.validate(task)
        assert result.is_valid is True  # Warnings don't invalidate
        assert result.has_warnings() is True
        assert len(result.warnings) >= 3  # Short, no AC, no tests (minimum)
