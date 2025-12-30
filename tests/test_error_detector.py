# ABOUTME: Tests for ErrorDetector - detects agent errors and stuck states
# ABOUTME: Consolidated test suite for error detection logic

"""Tests for ErrorDetector implementation.

Following the project's testing patterns for comprehensive coverage with
consolidated test cases and proper fixture usage.
"""

import pytest

from jean_claude.core.blocker_detector import BlockerType, BlockerDetails
from jean_claude.core.error_detector import ErrorDetector


class TestErrorDetector:
    """Test ErrorDetector - consolidated error and stuck state detection."""

    @pytest.fixture
    def detector(self) -> ErrorDetector:
        """Create ErrorDetector instance."""
        return ErrorDetector()

    def test_detector_inherits_from_blocker_detector(self, detector):
        """Test that ErrorDetector properly inherits from BlockerDetector."""
        from jean_claude.core.blocker_detector import BlockerDetector
        assert isinstance(detector, BlockerDetector)
        assert hasattr(detector, 'detect_blocker')

    def test_agent_stuck_patterns(self, detector):
        """Test detection of various agent stuck patterns."""
        stuck_responses = [
            "I'm stuck on this problem and need help",
            "I'm not sure how to proceed with this task",
            "I'm having difficulty understanding what to do next",
            "I can't figure out how to implement this feature",
            "I'm unable to complete this task without more information",
            "I don't know how to solve this issue",
            "I'm at a loss for what to do next",
            "I need help with this implementation",
            "I'm struggling to understand the requirements",
            "I'm blocked and can't continue",
            "This is beyond my capabilities",
            "I'm confused about how to proceed",
        ]

        for stuck_text in stuck_responses:
            result = detector.detect_blocker(stuck_text)
            assert result.blocker_type == BlockerType.ERROR
            assert "error" in result.message.lower()
            assert result.context is not None
            assert len(result.suggestions) > 0

    def test_agent_error_patterns(self, detector):
        """Test detection of agent error reporting patterns."""
        error_responses = [
            "I encountered an error while processing",
            "An error occurred during implementation",
            "There's an issue with the current approach",
            "Something went wrong with the execution",
            "I ran into a problem that I can't resolve",
            "The implementation failed due to an error",
            "I'm getting errors that I cannot fix",
            "An unexpected error has occurred",
            "The process failed with errors",
            "I'm experiencing technical difficulties",
            "There are issues that prevent me from continuing",
            "Critical error encountered during execution",
        ]

        for error_text in error_responses:
            result = detector.detect_blocker(error_text)
            assert result.blocker_type == BlockerType.ERROR
            assert "error" in result.message.lower()

    def test_technical_error_indicators(self, detector):
        """Test detection of technical error indicators."""
        technical_errors = [
            "RuntimeError: Cannot complete operation",
            "ConnectionError: Unable to connect to service",
            "TimeoutError: Operation timed out",
            "ValueError: Invalid parameter provided",
            "KeyError: Required key not found",
            "FileNotFoundError: File does not exist",
            "PermissionError: Access denied",
            "ConfigurationError: Invalid configuration",
            "ServiceUnavailableError: Service is down",
            "DatabaseError: Database connection failed",
        ]

        for error_text in technical_errors:
            result = detector.detect_blocker(error_text)
            assert result.blocker_type == BlockerType.ERROR
            assert "error" in result.message.lower()

    def test_workflow_blocking_errors(self, detector):
        """Test detection of workflow-blocking error scenarios."""
        blocking_errors = [
            "The API endpoint is not responding",
            "Cannot access the required database",
            "Missing dependencies prevent execution",
            "Configuration file is corrupted",
            "Network connectivity issues detected",
            "Authentication credentials are invalid",
            "Required services are unavailable",
            "File system permissions are insufficient",
            "Resource limits have been exceeded",
            "System compatibility issues found",
        ]

        for error_text in blocking_errors:
            result = detector.detect_blocker(error_text)
            assert result.blocker_type == BlockerType.ERROR
            assert "error" in result.message.lower()

    def test_no_errors_detected(self, detector):
        """Test that normal responses are not flagged as errors."""
        normal_responses = [
            "I've successfully implemented the authentication feature.",
            "The code has been refactored and is working well.",
            "Let me analyze the requirements first.",
            "I need clarification on the database schema.",  # This should be AMBIGUITY, not ERROR
            "The feature is complete and ready for review.",
            "All changes have been committed successfully.",
            "I'm working on the implementation now.",
            "",
            "Generating documentation for the API.",
            "The implementation is progressing smoothly.",
            "I've made good progress on this task.",
            "Everything is working as expected.",
        ]

        for response in normal_responses:
            result = detector.detect_blocker(response)
            # Note: Some responses might be AMBIGUITY instead of NONE
            assert result.blocker_type in [BlockerType.NONE, BlockerType.AMBIGUITY]

    def test_extract_error_details(self, detector):
        """Test extraction of specific error details."""
        complex_error = """
        I've been working on implementing the database connection feature.
        The basic structure is in place and the models have been created.

        However, I'm encountering several critical issues that prevent me from continuing:

        1. RuntimeError: Cannot establish connection to the database server
        2. ConfigurationError: Missing required environment variables
        3. PermissionError: Insufficient privileges to access database

        I'm stuck and unable to proceed without resolving these errors.
        The authentication service is also failing with timeout errors.

        I need assistance to resolve these blocking issues.
        """

        result = detector.detect_blocker(complex_error)

        assert result.blocker_type == BlockerType.ERROR
        assert "error" in result.message.lower()

        # Check that context contains useful information
        context = result.context
        assert context is not None
        assert "error_indicators" in context
        assert len(context["error_indicators"]) > 0

        # Check suggestions are provided
        assert len(result.suggestions) > 0
        suggestion_text = " ".join(result.suggestions).lower()
        assert any(keyword in suggestion_text for keyword in [
            "review", "check", "fix", "investigate", "resolve", "debug"
        ])

    def test_case_insensitive_detection(self, detector):
        """Test that detection works regardless of case."""
        case_variations = [
            "I'M STUCK on this implementation",
            "i'm stuck on this implementation",
            "I'm Stuck on this implementation",
            "AN ERROR OCCURRED during processing",
            "an error occurred during processing",
            "An Error Occurred during processing",
        ]

        for error_text in case_variations:
            result = detector.detect_blocker(error_text)
            assert result.blocker_type == BlockerType.ERROR

    def test_edge_cases_and_false_positives(self, detector):
        """Test edge cases that might cause false positives."""
        edge_cases = [
            "The error handling in this code needs improvement.",  # Discussing errors, not reporting them
            "I need to add error checking to the function.",
            "The user might encounter an error if they...",
            "Let me implement better error messages.",
            "This prevents errors from occurring.",
            "Error logs should be written to file.",
            "The previous version had errors, but this fixes them.",
        ]

        for text in edge_cases:
            result = detector.detect_blocker(text)
            # These should likely be NONE since they're discussing errors, not reporting them
            assert result.blocker_type == BlockerType.NONE

    def test_mixed_content_with_errors(self, detector):
        """Test detection in mixed content where errors are present."""
        mixed_content = """
        I've been working on implementing the user authentication feature.
        The basic structure is in place and the models have been created.

        However, I'm encountering a critical issue that's blocking progress:

        RuntimeError: Cannot establish secure connection to authentication service

        I'm stuck and cannot continue until this is resolved.
        The error appears to be related to SSL certificate validation.
        """

        result = detector.detect_blocker(mixed_content)
        assert result.blocker_type == BlockerType.ERROR
        assert "error" in result.message.lower()

    def test_ambiguous_vs_error_distinction(self, detector):
        """Test that ambiguous requests are distinguished from error states."""
        # These should be AMBIGUITY, not ERROR (assuming AmbiguityDetector handles them)
        ambiguous_responses = [
            "Could you clarify the requirements?",
            "I need more information about the database schema.",
            "What should happen when the user clicks this button?",
            "Should I use REST or GraphQL for the API?",
        ]

        for response in ambiguous_responses:
            result = detector.detect_blocker(response)
            # ErrorDetector should not flag these as ERROR
            # (they might be AMBIGUITY if processed by AmbiguityDetector, or NONE)
            assert result.blocker_type != BlockerType.ERROR


class TestErrorDetectorIntegration:
    """Integration tests for ErrorDetector."""

    def test_realistic_agent_error_scenarios(self):
        """Test realistic scenarios from actual agent responses."""
        detector = ErrorDetector()

        # Scenario 1: Agent encounters technical error during implementation
        scenario1 = """
        I'm implementing the file upload feature as requested.

        Here's what I've done:
        1. Created the upload endpoint
        2. Set up file validation
        3. Configured storage backend

        However, I've encountered a critical error that's blocking progress:

        PermissionError: [Errno 13] Permission denied: '/uploads/temp'

        I'm unable to proceed with testing the upload functionality.
        The application doesn't have write permissions to the upload directory.
        """

        result = detector.detect_blocker(scenario1)
        assert result.blocker_type == BlockerType.ERROR
        assert result.context["error_indicators"]
        assert len(result.suggestions) > 0

        # Scenario 2: Agent is stuck on implementation approach
        scenario2 = """
        I'm working on the real-time notification system. I've researched
        the requirements and understand what needs to be built.

        However, I'm stuck on choosing the right approach. I'm not sure whether
        to use WebSockets, Server-Sent Events, or polling. Each has trade-offs
        and I can't determine which is best for this use case.

        I need guidance on the technical approach before I can continue.
        """

        result = detector.detect_blocker(scenario2)
        assert result.blocker_type == BlockerType.ERROR
        assert "stuck" in " ".join(result.context["error_indicators"]).lower()

    def test_end_to_end_error_workflow(self):
        """Test complete workflow from agent response to blocker details."""
        detector = ErrorDetector()

        # Simulate agent response with critical error
        agent_response = """
        I've been implementing the payment processing integration with Stripe.

        Progress so far:
        1. Set up Stripe SDK and configuration
        2. Created payment models and database schema
        3. Implemented basic payment flow
        4. Added webhook handling for payment events

        Critical Issue Encountered:

        I'm getting a RuntimeError when trying to process payments:

        RuntimeError: stripe.error.AuthenticationError: No API key provided

        Even though I've set the API key in the environment variables,
        the Stripe SDK can't access it. I've double-checked the configuration
        and the environment variables are properly set.

        I'm stuck and unable to complete the payment processing feature.
        This is a blocking issue that prevents any payment functionality.

        The application works fine for all other features, but payment
        processing is completely broken due to this authentication error.
        """

        result = detector.detect_blocker(agent_response)

        # Verify detection worked correctly
        assert result.blocker_type == BlockerType.ERROR
        assert "error" in result.message.lower()

        # Verify context extraction
        assert result.context is not None
        assert "error_indicators" in result.context
        assert len(result.context["error_indicators"]) > 0

        # Verify useful suggestions are provided
        assert len(result.suggestions) > 0
        suggestions_text = " ".join(result.suggestions).lower()
        assert any(keyword in suggestions_text for keyword in [
            "review", "check", "debug", "fix", "investigate", "resolve"
        ])