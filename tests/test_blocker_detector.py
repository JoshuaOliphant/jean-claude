# ABOUTME: Tests for BlockerDetector interface and BlockerType enum
# ABOUTME: Consolidated test suite for blocker detection logic

"""Tests for BlockerDetector interface and related components.

Following the project's testing patterns for interface testing with
consolidated test coverage and proper fixture usage.
"""

import pytest
from abc import ABC

from jean_claude.core.blocker_detector import (
    BlockerDetector,
    BlockerType,
    BlockerDetails
)


class TestBlockerType:
    """Test BlockerType enum - consolidated enum behavior testing."""

    def test_blocker_type_enum_values(self):
        """Test that BlockerType enum has correct values."""
        assert BlockerType.TEST_FAILURE == 'test_failure'
        assert BlockerType.ERROR == 'error'
        assert BlockerType.AMBIGUITY == 'ambiguity'
        assert BlockerType.NONE == 'none'

    def test_blocker_type_string_behavior(self):
        """Test that BlockerType behaves as expected string enum."""
        # Test string comparison - use .value for explicit string conversion
        assert BlockerType.TEST_FAILURE.value == 'test_failure'
        assert BlockerType.ERROR.value == 'error'

        # Test equality with strings (str, Enum allows direct comparison)
        assert BlockerType.AMBIGUITY == 'ambiguity'
        assert BlockerType.NONE != 'failure'


class TestBlockerDetails:
    """Test BlockerDetails dataclass functionality."""

    def test_blocker_details_creation_with_defaults(self):
        """Test creating BlockerDetails with default values."""
        details = BlockerDetails(
            blocker_type=BlockerType.TEST_FAILURE,
            message="Test failed"
        )

        assert details.blocker_type == BlockerType.TEST_FAILURE
        assert details.message == "Test failed"
        assert details.context is None
        assert details.suggestions == []

    def test_blocker_details_creation_with_all_fields(self):
        """Test creating BlockerDetails with all fields populated."""
        context = {"test_name": "test_auth", "line": 42}
        suggestions = ["Fix authentication", "Check credentials"]

        details = BlockerDetails(
            blocker_type=BlockerType.ERROR,
            message="Authentication error",
            context=context,
            suggestions=suggestions
        )

        assert details.blocker_type == BlockerType.ERROR
        assert details.message == "Authentication error"
        assert details.context == context
        assert details.suggestions == suggestions

    def test_blocker_details_none_type_behavior(self):
        """Test BlockerDetails when no blocker is detected."""
        details = BlockerDetails(
            blocker_type=BlockerType.NONE,
            message="No blockers detected"
        )

        assert details.blocker_type == BlockerType.NONE
        assert details.message == "No blockers detected"
        assert not details.context
        assert not details.suggestions


class TestBlockerDetectorInterface:
    """Test BlockerDetector abstract interface."""

    def test_blocker_detector_is_abstract_base_class(self):
        """Test that BlockerDetector is an abstract base class."""
        assert issubclass(BlockerDetector, ABC)

        # Should not be able to instantiate directly
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BlockerDetector()

    def test_blocker_detector_has_detect_blocker_method(self):
        """Test that detect_blocker method exists in interface."""
        # Check that the abstract method exists
        assert hasattr(BlockerDetector, 'detect_blocker')
        assert 'detect_blocker' in BlockerDetector.__abstractmethods__

    def test_concrete_implementation_works(self):
        """Test that concrete implementation can be created and used."""

        class TestBlockerDetector(BlockerDetector):
            """Concrete test implementation of BlockerDetector."""

            def detect_blocker(self, agent_response: str) -> BlockerDetails:
                # Simple test implementation
                if "test failed" in agent_response.lower():
                    return BlockerDetails(
                        blocker_type=BlockerType.TEST_FAILURE,
                        message="Test failure detected",
                        context={"response": agent_response}
                    )
                elif "error" in agent_response.lower():
                    return BlockerDetails(
                        blocker_type=BlockerType.ERROR,
                        message="Error detected"
                    )
                elif "unclear" in agent_response.lower():
                    return BlockerDetails(
                        blocker_type=BlockerType.AMBIGUITY,
                        message="Ambiguity detected",
                        suggestions=["Clarify requirements"]
                    )
                else:
                    return BlockerDetails(
                        blocker_type=BlockerType.NONE,
                        message="No blockers detected"
                    )

        # Test instantiation and usage
        detector = TestBlockerDetector()

        # Test different response types
        result1 = detector.detect_blocker("Test failed with assertion error")
        assert result1.blocker_type == BlockerType.TEST_FAILURE
        assert "Test failure detected" in result1.message
        assert result1.context["response"] == "Test failed with assertion error"

        result2 = detector.detect_blocker("Encountered an error in processing")
        assert result2.blocker_type == BlockerType.ERROR
        assert "Error detected" in result2.message

        result3 = detector.detect_blocker("The requirements are unclear")
        assert result3.blocker_type == BlockerType.AMBIGUITY
        assert "Ambiguity detected" in result3.message
        assert "Clarify requirements" in result3.suggestions

        result4 = detector.detect_blocker("Everything looks good")
        assert result4.blocker_type == BlockerType.NONE
        assert "No blockers detected" in result4.message


class TestBlockerDetectorIntegration:
    """Integration tests for the complete blocker detection system."""

    def test_end_to_end_blocker_detection_workflow(self):
        """Test complete workflow from agent response to blocker details."""

        class MockBlockerDetector(BlockerDetector):
            def detect_blocker(self, agent_response: str) -> BlockerDetails:
                # More realistic detection logic
                if any(phrase in agent_response.lower() for phrase in
                       ["test failed", "assertion error", "test failure"]):
                    return BlockerDetails(
                        blocker_type=BlockerType.TEST_FAILURE,
                        message="Test failure detected in agent response",
                        context={"failure_indicators": ["test failed"]},
                        suggestions=["Review test implementation", "Check test data"]
                    )
                return BlockerDetails(
                    blocker_type=BlockerType.NONE,
                    message="No blockers found"
                )

        detector = MockBlockerDetector()

        # Simulate agent response with test failure
        agent_response = """
        I tried to run the tests but encountered issues:

        FAILED tests/test_auth.py::test_login - AssertionError: Expected True but got False
        Test failed with 1 failure out of 5 tests.

        Need to investigate the authentication logic.
        """

        result = detector.detect_blocker(agent_response)

        assert result.blocker_type == BlockerType.TEST_FAILURE
        assert "Test failure detected" in result.message
        assert result.context is not None
        assert len(result.suggestions) > 0
        assert "Review test implementation" in result.suggestions