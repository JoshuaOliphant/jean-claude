# ABOUTME: Tests for AmbiguityDetector - detects agent requests for clarification
# ABOUTME: Consolidated test suite for ambiguity detection logic

"""Tests for AmbiguityDetector implementation.

Following the project's testing patterns for comprehensive coverage with
consolidated test cases and proper fixture usage.
"""

import pytest

from jean_claude.core.blocker_detector import BlockerType, BlockerDetails
from jean_claude.core.ambiguity_detector import AmbiguityDetector


class TestAmbiguityDetector:
    """Test AmbiguityDetector - consolidated ambiguity and clarification detection."""

    @pytest.fixture
    def detector(self) -> AmbiguityDetector:
        """Create AmbiguityDetector instance."""
        return AmbiguityDetector()

    def test_detector_inherits_from_blocker_detector(self, detector):
        """Test that AmbiguityDetector properly inherits from BlockerDetector."""
        from jean_claude.core.blocker_detector import BlockerDetector
        assert isinstance(detector, BlockerDetector)
        assert hasattr(detector, 'detect_blocker')

    def test_direct_clarification_requests(self, detector):
        """Test detection of direct clarification request patterns."""
        clarification_requests = [
            "Could you clarify the requirements?",
            "I need clarification on the database schema",
            "Can you provide more details about the API structure?",
            "Please clarify what should happen when the user clicks this",
            "I need more information about the expected behavior",
            "Could you explain how the authentication should work?",
            "What exactly should the response format be?",
            "I need clarification about the data validation rules",
            "Can you clarify the business logic for this feature?",
            "Please provide more details on the error handling approach",
            "I need clarification on the user interface layout",
            "Could you specify the exact requirements for this component?",
        ]

        for clarification_text in clarification_requests:
            result = detector.detect_blocker(clarification_text)
            assert result.blocker_type == BlockerType.AMBIGUITY
            assert "ambiguity" in result.message.lower()
            assert result.context is not None
            assert len(result.suggestions) > 0

    def test_question_based_ambiguity_patterns(self, detector):
        """Test detection of question-based ambiguity patterns."""
        question_patterns = [
            "Should I use REST or GraphQL for the API?",
            "What database should I use for this feature?",
            "Which authentication method would be best?",
            "How should I handle error cases in this scenario?",
            "What validation rules should I apply to user input?",
            "Should this be a synchronous or asynchronous operation?",
            "What format should the response data be in?",
            "How should I structure the database tables?",
            "Which libraries should I use for this implementation?",
            "What should happen if the external service is unavailable?",
            "Should I implement caching for this endpoint?",
            "How should I organize the code structure for this feature?",
            "What permissions should be required for this action?",
            "Should this data be stored in the database or cache?",
        ]

        for question_text in question_patterns:
            result = detector.detect_blocker(question_text)
            assert result.blocker_type == BlockerType.AMBIGUITY
            assert "ambiguity" in result.message.lower()

    def test_uncertainty_and_options_patterns(self, detector):
        """Test detection of uncertainty and multiple options patterns."""
        uncertainty_patterns = [
            "I'm not sure which approach to take for this implementation",
            "There are several ways to implement this, which would you prefer?",
            "I'm uncertain about the data model for this feature",
            "Not sure if I should use a library or implement this from scratch",
            "I'm unsure about the best way to handle this edge case",
            "There are multiple options for the user interface - which do you prefer?",
            "I'm not certain about the security requirements for this feature",
            "Unsure whether to use a queue or direct processing for this task",
            "I have doubts about the performance implications of this approach",
            "Not clear on the expected user workflow for this feature",
            "I'm hesitant about the database migration strategy",
            "Uncertain about the testing approach for this component",
        ]

        for uncertainty_text in uncertainty_patterns:
            result = detector.detect_blocker(uncertainty_text)
            assert result.blocker_type == BlockerType.AMBIGUITY
            assert "ambiguity" in result.message.lower()

    def test_requirement_understanding_issues(self, detector):
        """Test detection of requirement understanding issues."""
        understanding_issues = [
            "I don't understand the exact requirements for this feature",
            "The requirements are not clear to me",
            "I'm having trouble understanding what the user needs",
            "The acceptance criteria seem ambiguous",
            "I don't fully grasp the business logic requirements",
            "The specifications are unclear in this section",
            "I'm confused about what the expected output should be",
            "The user story doesn't provide enough detail",
            "I need a better understanding of the use case",
            "The functional requirements are vague",
            "I'm not clear on the data flow for this feature",
            "The technical requirements are incomplete",
        ]

        for understanding_text in understanding_issues:
            result = detector.detect_blocker(understanding_text)
            assert result.blocker_type == BlockerType.AMBIGUITY
            assert "ambiguity" in result.message.lower()

    def test_assumption_validation_patterns(self, detector):
        """Test detection of assumption validation patterns."""
        assumption_patterns = [
            "I'm assuming the API should return JSON - is that correct?",
            "Should I assume users are always authenticated for this endpoint?",
            "I assume we want to validate email formats - correct?",
            "My assumption is that we store passwords hashed - right?",
            "I'm working under the assumption that data is in UTF-8",
            "Assuming we want real-time updates - is that accurate?",
            "I presume this should work on mobile devices too?",
            "My understanding is that this data is public - confirm?",
            "I'm assuming concurrent access needs to be handled - correct?",
            "Should I assume the database supports transactions?",
            "I presume error messages should be user-friendly - right?",
            "Assuming we need audit logging for this feature - confirm?",
        ]

        for assumption_text in assumption_patterns:
            result = detector.detect_blocker(assumption_text)
            assert result.blocker_type == BlockerType.AMBIGUITY
            assert "ambiguity" in result.message.lower()

    def test_no_ambiguity_detected(self, detector):
        """Test that clear statements are not flagged as ambiguous."""
        clear_responses = [
            "I've successfully implemented the authentication feature.",
            "The code has been refactored and is working well.",
            "I'm working on the implementation now.",
            "The feature is complete and ready for review.",
            "All changes have been committed successfully.",
            "I've created the database models and API endpoints.",
            "The tests are passing and the feature works as expected.",
            "",
            "Generating documentation for the API.",
            "The implementation follows the specified requirements.",
            "I've added proper error handling and validation.",
            "The user interface has been updated accordingly.",
            "All dependencies have been installed and configured.",
        ]

        for response in clear_responses:
            result = detector.detect_blocker(response)
            assert result.blocker_type == BlockerType.NONE
            assert "no ambiguity detected" in result.message.lower()

    def test_extract_ambiguity_details(self, detector):
        """Test extraction of specific ambiguity details."""
        complex_ambiguity = """
        I'm implementing the user notification system as requested.

        I've made good progress on the basic structure:
        1. Created the notification models
        2. Set up the database tables
        3. Started work on the API endpoints

        However, I have several questions about the requirements that I need clarification on:

        1. Should notifications be sent via email, SMS, push notifications, or all three?
        2. How long should notifications be stored in the database?
        3. Should users be able to customize their notification preferences?
        4. What should happen if a notification delivery fails?
        5. Should we implement real-time notifications or is batch processing sufficient?

        I'm not sure which approach to take without this clarification.
        The requirements document doesn't specify these details clearly.

        Could you provide guidance on these points so I can complete the implementation correctly?
        """

        result = detector.detect_blocker(complex_ambiguity)

        assert result.blocker_type == BlockerType.AMBIGUITY
        assert "ambiguity" in result.message.lower()

        # Check that context contains useful information
        context = result.context
        assert context is not None
        assert "ambiguity_indicators" in context
        assert len(context["ambiguity_indicators"]) > 0

        # Check suggestions are provided
        assert len(result.suggestions) > 0
        suggestion_text = " ".join(result.suggestions).lower()
        assert any(keyword in suggestion_text for keyword in [
            "clarify", "provide", "specify", "detail", "requirement"
        ])

    def test_case_insensitive_detection(self, detector):
        """Test that detection works regardless of case."""
        case_variations = [
            "COULD YOU CLARIFY the requirements?",
            "could you clarify the requirements?",
            "Could You Clarify the requirements?",
            "I NEED CLARIFICATION on this feature",
            "i need clarification on this feature",
            "I Need Clarification on this feature",
        ]

        for ambiguity_text in case_variations:
            result = detector.detect_blocker(ambiguity_text)
            assert result.blocker_type == BlockerType.AMBIGUITY

    def test_edge_cases_and_false_positives(self, detector):
        """Test edge cases that might cause false positives."""
        edge_cases = [
            "The user can clarify their preferences in the settings.",  # Discussing clarification, not requesting it
            "This feature helps clarify the data structure.",
            "The error message should clarify what went wrong.",
            "I need to clarify the code with better comments.",  # Clarifying code, not requesting clarification
            "Let me clarify my implementation approach.",
            "This clarifies the business logic requirements.",
            "I need to ask the database for user information.",  # "ask" in different context
            "Should I continue with the current implementation?",  # Simple procedural question
        ]

        for text in edge_cases:
            result = detector.detect_blocker(text)
            # These should likely be NONE since they're not requesting clarification
            assert result.blocker_type == BlockerType.NONE

    def test_mixed_content_with_ambiguity(self, detector):
        """Test detection in mixed content where ambiguity is present."""
        mixed_content = """
        I've been working on implementing the payment processing feature.
        The basic structure is in place and the Stripe integration is configured.

        However, I need clarification on a few important details:

        Should we store payment history permanently or just for a limited time?
        What should happen if the payment gateway is temporarily unavailable?

        I'm not sure how to proceed without this information.
        The feature is mostly complete but these details will affect the implementation.
        """

        result = detector.detect_blocker(mixed_content)
        assert result.blocker_type == BlockerType.AMBIGUITY
        assert "ambiguity" in result.message.lower()

    def test_distinguish_from_other_blocker_types(self, detector):
        """Test that ambiguity is distinguished from other blocker types."""
        # These should NOT be AMBIGUITY (they're ERROR or TEST_FAILURE)
        non_ambiguity_responses = [
            "I'm stuck and can't continue with this implementation.",  # ERROR
            "FAILED tests/test_auth.py::test_login - AssertionError",  # TEST_FAILURE
            "RuntimeError: Cannot connect to database",  # ERROR
            "I encountered an unexpected error during processing",  # ERROR
            "Tests are failing due to assertion errors",  # TEST_FAILURE
        ]

        for response in non_ambiguity_responses:
            result = detector.detect_blocker(response)
            # AmbiguityDetector should not flag these as AMBIGUITY
            assert result.blocker_type != BlockerType.AMBIGUITY


class TestAmbiguityDetectorIntegration:
    """Integration tests for AmbiguityDetector."""

    def test_realistic_agent_ambiguity_scenarios(self):
        """Test realistic scenarios from actual agent responses."""
        detector = AmbiguityDetector()

        # Scenario 1: Agent needs clarification during feature implementation
        scenario1 = """
        I'm implementing the user dashboard feature as requested.

        Here's what I've completed so far:
        1. Created the dashboard layout and navigation
        2. Set up the data fetching mechanisms
        3. Implemented basic user statistics display

        I have a question about the requirements:

        Should the dashboard display real-time data or is it acceptable to show
        cached data that's updated periodically? The performance implications
        are quite different for each approach.

        Could you clarify your preference so I can complete the implementation appropriately?
        """

        result = detector.detect_blocker(scenario1)
        assert result.blocker_type == BlockerType.AMBIGUITY
        assert result.context["ambiguity_indicators"]
        assert len(result.suggestions) > 0

        # Scenario 2: Agent uncertain about implementation approach
        scenario2 = """
        I'm working on the file upload functionality. I understand the basic
        requirement but I'm uncertain about a few implementation details.

        The requirements mention supporting "large files" but don't specify:
        - What constitutes a "large file" (size threshold?)
        - Should we implement chunked uploads for better reliability?
        - What's the maximum file size we should support?
        - Should we validate file types, and if so, which types are allowed?

        I don't want to make assumptions that might not align with your needs.
        Could you provide guidance on these points?
        """

        result = detector.detect_blocker(scenario2)
        assert result.blocker_type == BlockerType.AMBIGUITY
        assert "uncertain" in " ".join(result.context["ambiguity_indicators"]).lower()

    def test_end_to_end_ambiguity_workflow(self):
        """Test complete workflow from agent response to blocker details."""
        detector = AmbiguityDetector()

        # Simulate agent response with multiple ambiguity indicators
        agent_response = """
        I've been working on the notification system integration with the existing user management.

        Progress made:
        1. Set up notification models and database tables
        2. Created basic API endpoints for sending notifications
        3. Implemented email notification sending via SMTP
        4. Added notification preferences to user profiles

        Areas where I need clarification:

        The requirements mention "priority levels" for notifications but don't specify:
        1. How many priority levels should there be? (e.g., Low, Medium, High, Critical?)
        2. Should high-priority notifications bypass user preferences and always be sent?
        3. Should we implement notification rate limiting to prevent spam?
        4. What should be the default notification preferences for new users?

        I'm also uncertain about the notification delivery guarantees:
        - Should we retry failed notification deliveries?
        - How should we handle notifications to deleted or deactivated user accounts?
        - Should notifications have an expiration time?

        I don't want to make architectural decisions that might not align with your vision.
        Could you provide guidance on these design questions so I can complete the
        implementation according to your specifications?
        """

        result = detector.detect_blocker(agent_response)

        # Verify detection worked correctly
        assert result.blocker_type == BlockerType.AMBIGUITY
        assert "ambiguity" in result.message.lower()

        # Verify context extraction
        assert result.context is not None
        assert "ambiguity_indicators" in result.context
        assert len(result.context["ambiguity_indicators"]) > 0

        # Verify useful suggestions are provided
        assert len(result.suggestions) > 0
        suggestions_text = " ".join(result.suggestions).lower()
        assert any(keyword in suggestions_text for keyword in [
            "clarify", "provide", "specify", "detail", "requirement", "guidance"
        ])