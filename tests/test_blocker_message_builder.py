# ABOUTME: Tests for BlockerMessageBuilder that constructs Message objects from blocker details
# ABOUTME: Consolidated test suite covering all blocker types with appropriate priority and awaiting_response

"""Tests for BlockerMessageBuilder.

Following the project's testing patterns with consolidated test coverage,
proper fixture usage, and comprehensive testing of message construction from blocker details.
"""

import pytest

from jean_claude.core.blocker_detector import BlockerType, BlockerDetails
from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.blocker_message_builder import BlockerMessageBuilder


class TestBlockerMessageBuilderCreation:
    """Test BlockerMessageBuilder instantiation and basic functionality."""

    def test_blocker_message_builder_creation(self):
        """Test creating a BlockerMessageBuilder instance."""
        builder = BlockerMessageBuilder()
        assert isinstance(builder, BlockerMessageBuilder)

    def test_builder_has_build_message_method(self):
        """Test that builder has the required build_message method."""
        builder = BlockerMessageBuilder()
        assert hasattr(builder, 'build_message')
        assert callable(getattr(builder, 'build_message'))


class TestBlockerMessageConstruction:
    """Test message construction from different blocker types."""

    def test_build_message_for_test_failure_blocker(self):
        """Test building message for TEST_FAILURE blocker type."""
        builder = BlockerMessageBuilder()

        blocker_details = BlockerDetails(
            blocker_type=BlockerType.TEST_FAILURE,
            message="Tests failed in test_auth.py",
            context={"test_file": "test_auth.py", "failures": 3},
            suggestions=["Fix authentication logic", "Check test data"]
        )

        message = builder.build_message(
            blocker_details=blocker_details,
            from_agent="agent-1",
            to_agent="coordinator"
        )

        # Verify message structure
        assert isinstance(message, Message)
        assert message.from_agent == "agent-1"
        assert message.to_agent == "coordinator"
        assert message.type == "blocker_detected"
        assert "Test Failure" in message.subject
        assert message.priority == MessagePriority.URGENT
        assert message.awaiting_response is True

        # Verify message body contains blocker details
        assert "Tests failed in test_auth.py" in message.body
        assert "Fix authentication logic" in message.body
        assert "Check test data" in message.body

    def test_build_message_for_error_blocker(self):
        """Test building message for ERROR blocker type."""
        builder = BlockerMessageBuilder()

        blocker_details = BlockerDetails(
            blocker_type=BlockerType.ERROR,
            message="Agent encountered an unexpected error",
            context={"error_type": "FileNotFoundError", "location": "line 42"},
            suggestions=["Check file path", "Verify permissions"]
        )

        message = builder.build_message(
            blocker_details=blocker_details,
            from_agent="implementation-agent",
            to_agent="coordinator"
        )

        # Verify message structure
        assert message.from_agent == "implementation-agent"
        assert message.to_agent == "coordinator"
        assert message.type == "blocker_detected"
        assert "Error" in message.subject
        assert message.priority == MessagePriority.URGENT
        assert message.awaiting_response is True

        # Verify message body
        assert "Agent encountered an unexpected error" in message.body
        assert "Check file path" in message.body

    def test_build_message_for_ambiguity_blocker(self):
        """Test building message for AMBIGUITY blocker type."""
        builder = BlockerMessageBuilder()

        blocker_details = BlockerDetails(
            blocker_type=BlockerType.AMBIGUITY,
            message="Requirements are unclear for user authentication",
            context={"requirement_section": "auth", "ambiguous_parts": ["login flow"]},
            suggestions=["Clarify login requirements", "Define user roles"]
        )

        message = builder.build_message(
            blocker_details=blocker_details,
            from_agent="planning-agent",
            to_agent="product-owner"
        )

        # Verify message structure
        assert message.from_agent == "planning-agent"
        assert message.to_agent == "product-owner"
        assert message.type == "blocker_detected"
        assert "Clarification" in message.subject
        assert message.priority == MessagePriority.URGENT
        assert message.awaiting_response is True

        # Verify message body
        assert "Requirements are unclear" in message.body
        assert "Clarify login requirements" in message.body

    def test_build_message_for_none_blocker_type(self):
        """Test that NONE blocker type raises ValueError."""
        builder = BlockerMessageBuilder()

        blocker_details = BlockerDetails(
            blocker_type=BlockerType.NONE,
            message="No blockers detected"
        )

        with pytest.raises(ValueError, match="Cannot build message for NONE blocker type"):
            builder.build_message(
                blocker_details=blocker_details,
                from_agent="agent-1",
                to_agent="coordinator"
            )


class TestBlockerMessageBodyFormatting:
    """Test message body formatting and content organization."""

    def test_message_body_includes_all_blocker_information(self):
        """Test that message body includes all relevant blocker information."""
        builder = BlockerMessageBuilder()

        blocker_details = BlockerDetails(
            blocker_type=BlockerType.TEST_FAILURE,
            message="Multiple test failures detected",
            context={
                "failed_tests": ["test_auth", "test_login"],
                "total_failures": 2,
                "file": "auth_tests.py"
            },
            suggestions=[
                "Review authentication logic",
                "Check test database setup",
                "Verify mock configurations"
            ]
        )

        message = builder.build_message(
            blocker_details=blocker_details,
            from_agent="test-agent",
            to_agent="coordinator"
        )

        # Check that body is well-formatted
        body_lines = message.body.split('\n')
        assert len(body_lines) > 5  # Should have multiple sections

        # Check for expected content sections
        assert "Multiple test failures detected" in message.body
        assert "Context:" in message.body or "Additional Context:" in message.body
        assert "Suggestions:" in message.body or "Suggested Actions:" in message.body

        # Verify all suggestions are included
        for suggestion in blocker_details.suggestions:
            assert suggestion in message.body

    def test_message_body_handles_missing_context_and_suggestions(self):
        """Test message body formatting when context or suggestions are missing."""
        builder = BlockerMessageBuilder()

        # Test with no context or suggestions
        blocker_details = BlockerDetails(
            blocker_type=BlockerType.ERROR,
            message="Simple error occurred"
        )

        message = builder.build_message(
            blocker_details=blocker_details,
            from_agent="agent-1",
            to_agent="coordinator"
        )

        # Should still have a well-formed body with just the message
        assert "Simple error occurred" in message.body
        assert len(message.body.strip()) > 0


class TestBlockerMessageBuilderValidation:
    """Test input validation for BlockerMessageBuilder."""

    def test_build_message_validates_required_parameters(self):
        """Test that build_message validates all required parameters."""
        builder = BlockerMessageBuilder()

        valid_blocker = BlockerDetails(
            blocker_type=BlockerType.ERROR,
            message="Test error"
        )

        # Test missing blocker_details
        with pytest.raises((TypeError, ValueError)):
            builder.build_message(
                blocker_details=None,
                from_agent="agent-1",
                to_agent="coordinator"
            )

        # Test empty from_agent
        with pytest.raises(ValueError):
            builder.build_message(
                blocker_details=valid_blocker,
                from_agent="",
                to_agent="coordinator"
            )

        # Test empty to_agent
        with pytest.raises(ValueError):
            builder.build_message(
                blocker_details=valid_blocker,
                from_agent="agent-1",
                to_agent=""
            )

    def test_build_message_handles_all_blocker_types(self):
        """Test that builder can handle all valid blocker types except NONE."""
        builder = BlockerMessageBuilder()

        valid_blocker_types = [
            BlockerType.TEST_FAILURE,
            BlockerType.ERROR,
            BlockerType.AMBIGUITY
        ]

        for blocker_type in valid_blocker_types:
            blocker_details = BlockerDetails(
                blocker_type=blocker_type,
                message=f"Test {blocker_type.value} message"
            )

            message = builder.build_message(
                blocker_details=blocker_details,
                from_agent="test-agent",
                to_agent="coordinator"
            )

            # All non-NONE blockers should create urgent, awaiting_response messages
            assert message.priority == MessagePriority.URGENT
            assert message.awaiting_response is True
            assert message.type == "blocker_detected"


class TestBlockerMessageBuilderIntegration:
    """Integration tests for BlockerMessageBuilder with real blocker scenarios."""

    def test_end_to_end_workflow_blocker_message_creation(self):
        """Test complete workflow from blocker detection to message creation."""
        builder = BlockerMessageBuilder()

        # Simulate realistic test failure scenario
        blocker_details = BlockerDetails(
            blocker_type=BlockerType.TEST_FAILURE,
            message="Tests failed during authentication module implementation",
            context={
                "test_file": "tests/test_auth.py",
                "failed_test_count": 3,
                "total_test_count": 10,
                "error_summary": "AssertionError: Expected True but got False"
            },
            suggestions=[
                "Review authentication logic in src/auth.py",
                "Check test data setup in conftest.py",
                "Verify database connection in test environment"
            ]
        )

        message = builder.build_message(
            blocker_details=blocker_details,
            from_agent="implementation-agent",
            to_agent="coordinator"
        )

        # Verify this creates a complete, actionable message
        assert message.from_agent == "implementation-agent"
        assert message.to_agent == "coordinator"
        assert message.type == "blocker_detected"
        assert "Test Failure" in message.subject
        assert message.priority == MessagePriority.URGENT
        assert message.awaiting_response is True

        # Verify message is comprehensive
        assert "authentication module" in message.body.lower()
        assert "3" in message.body  # failed test count
        assert "AssertionError" in message.body
        assert "Review authentication logic" in message.body

        # Verify message has proper structure for human consumption
        assert len(message.body.split('\n')) > 5  # Multi-line formatted body
        assert message.subject.strip() != ""
        assert len(message.subject) < 100  # Reasonable subject length