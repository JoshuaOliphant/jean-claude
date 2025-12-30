# ABOUTME: Tests for ResponseParser - extracts user decisions from OUTBOX messages
# ABOUTME: Consolidated test suite for response parsing logic

"""Tests for ResponseParser implementation.

Following the project's testing patterns for comprehensive coverage with
consolidated test cases and proper fixture usage.
"""

import pytest

from jean_claude.core.response_parser import ResponseParser, UserDecision, DecisionType


class TestResponseParser:
    """Test ResponseParser - consolidated response decision extraction."""

    @pytest.fixture
    def parser(self) -> ResponseParser:
        """Create ResponseParser instance."""
        return ResponseParser()

    def test_parser_initialization(self, parser):
        """Test that ResponseParser initializes correctly."""
        assert hasattr(parser, 'parse_response')
        assert callable(parser.parse_response)

    def test_extract_skip_decisions(self, parser):
        """Test detection of skip decision patterns."""
        skip_responses = [
            "Skip this test for now and revisit later",
            "Let's skip the failing tests and proceed",
            "I want to skip this error and move on",
            "Please skip this blocker",
            "SKIP - not important right now",
            "skip this issue",
            "Skip the test failure",
            "Let's skip this and come back later",
            "Skip this test until we have the database ready",
            "I'll skip this for now",
        ]

        for skip_text in skip_responses:
            result = parser.parse_response(skip_text)
            assert result.decision_type == DecisionType.SKIP
            assert "skip" in result.message.lower()
            assert result.context is not None
            assert skip_text in result.context["original_content"]

    def test_extract_fix_decisions(self, parser):
        """Test detection of fix decision patterns."""
        fix_responses = [
            "Please fix the authentication logic in src/auth.py",
            "Fix this error immediately",
            "I need you to fix the test failures",
            "Let's fix this issue",
            "FIX the database connection problem",
            "fix the bug in user registration",
            "Please fix this and try again",
            "Fix the validation errors",
            "I want this fixed before continuing",
            "Fix the API endpoint issues",
            "Go ahead and fix this problem",
            "Fix the failing unit tests",
        ]

        for fix_text in fix_responses:
            result = parser.parse_response(fix_text)
            assert result.decision_type == DecisionType.FIX
            assert "fix" in result.message.lower()
            assert result.context is not None

    def test_extract_abort_decisions(self, parser):
        """Test detection of abort decision patterns."""
        abort_responses = [
            "Abort this workflow",
            "I want to abort and start over",
            "Please abort the current implementation",
            "ABORT - this approach isn't working",
            "abort the task",
            "Let's abort and try a different approach",
            "Abort this feature development",
            "I need to abort this workflow",
            "Abort the current process",
            "Stop and abort this task",
        ]

        for abort_text in abort_responses:
            result = parser.parse_response(abort_text)
            assert result.decision_type == DecisionType.ABORT
            assert "abort" in result.message.lower()
            assert result.context is not None

    def test_extract_continue_decisions(self, parser):
        """Test detection of continue decision patterns."""
        continue_responses = [
            "Continue with the implementation",
            "Please continue working on this",
            "Let's continue despite the warnings",
            "CONTINUE with the current approach",
            "continue the development",
            "Continue implementing the feature",
            "Please continue and ignore the minor issues",
            "Continue with the next step",
            "I want you to continue",
            "Go ahead and continue",
            "Continue the workflow",
            "Keep going and continue",
        ]

        for continue_text in continue_responses:
            result = parser.parse_response(continue_text)
            assert result.decision_type == DecisionType.CONTINUE
            assert "continue" in result.message.lower()
            assert result.context is not None

    def test_ambiguous_or_unclear_responses(self, parser):
        """Test handling of ambiguous responses that don't clearly indicate a decision."""
        ambiguous_responses = [
            "I'm not sure what to do here",
            "This is a complex issue",
            "Let me think about this",
            "What do you recommend?",
            "I need more information",
            "This requires careful consideration",
            "",  # Empty response
            "   ",  # Whitespace only
            "Hello, how are you?",
            "The weather is nice today",
            "I reviewed the code but have questions",
        ]

        for ambiguous_text in ambiguous_responses:
            result = parser.parse_response(ambiguous_text)
            # Should either be UNCLEAR or extract a weak signal if any keywords are present
            assert result.decision_type in [DecisionType.UNCLEAR, DecisionType.CONTINUE, DecisionType.FIX]
            assert result.context is not None

    def test_mixed_content_with_clear_decision(self, parser):
        """Test extraction from mixed content where decision is embedded."""
        mixed_content_responses = [
            """I reviewed the test failures in detail. The authentication module
               has several issues that need to be addressed.

               Please fix the authentication logic in src/auth.py.

               The specific problems are:
               1. Password validation is too weak
               2. Session handling is broken
               3. Error messages are unclear""",

            """Looking at this error, I can see what's happening. The database
               connection is failing because of configuration issues.

               Let's skip this for now and come back later.
               We can address this once the infrastructure is ready.""",

            """This is a complex implementation task. I've analyzed the requirements
               and the current codebase state.

               I want to abort this workflow and restart with a different approach.
               The current strategy isn't working well.""",

            """Thanks for the update on the progress. The implementation looks good
               so far and the tests are mostly passing.

               Please continue with the current implementation plan.
               Just address the minor formatting issues."""
        ]

        expected_decisions = [DecisionType.FIX, DecisionType.SKIP, DecisionType.ABORT, DecisionType.CONTINUE]

        for content, expected in zip(mixed_content_responses, expected_decisions):
            result = parser.parse_response(content)
            assert result.decision_type == expected
            assert result.context["original_content"] == content

    def test_case_insensitive_detection(self, parser):
        """Test that detection works regardless of case."""
        case_variations = [
            ("SKIP this test", DecisionType.SKIP),
            ("skip this test", DecisionType.SKIP),
            ("Skip This Test", DecisionType.SKIP),
            ("FIX the authentication", DecisionType.FIX),
            ("fix the authentication", DecisionType.FIX),
            ("Fix The Authentication", DecisionType.FIX),
            ("ABORT the workflow", DecisionType.ABORT),
            ("abort the workflow", DecisionType.ABORT),
            ("CONTINUE working", DecisionType.CONTINUE),
            ("continue working", DecisionType.CONTINUE),
        ]

        for text, expected_decision in case_variations:
            result = parser.parse_response(text)
            assert result.decision_type == expected_decision

    def test_multiple_decisions_prioritization(self, parser):
        """Test handling when multiple decision keywords are present."""
        conflicting_responses = [
            "Skip this test but fix the main issue",  # Should prefer FIX over SKIP
            "Fix this error or abort if it's too complex",  # Should prefer ABORT over FIX (most decisive)
            "Continue with implementation but skip the broken tests",  # Should prefer CONTINUE over SKIP
            "Abort this approach and fix the core problem instead",  # Should prefer ABORT over FIX
        ]

        # The parser should have a priority order for conflicting decisions
        # Priority: ABORT > FIX > CONTINUE > SKIP (most to least decisive)
        expected_priorities = [DecisionType.FIX, DecisionType.ABORT, DecisionType.CONTINUE, DecisionType.ABORT]

        for response, expected in zip(conflicting_responses, expected_priorities):
            result = parser.parse_response(response)
            assert result.decision_type == expected

    def test_extract_additional_context(self, parser):
        """Test extraction of additional context beyond the decision."""
        detailed_response = """
        I've reviewed the test failure report carefully.

        Please fix the authentication module issues:
        1. Update src/auth/login.py - password validation function
        2. Fix the session management in src/auth/session.py
        3. Add proper error handling in src/auth/errors.py

        Priority: HIGH
        Estimated time: 2 hours
        Dependencies: None

        Once fixed, re-run the test suite to verify everything works.
        """

        result = parser.parse_response(detailed_response)

        assert result.decision_type == DecisionType.FIX
        assert result.context is not None
        context = result.context

        # Check that context contains useful extracted information
        assert "original_content" in context
        assert context["original_content"] == detailed_response.strip()
        assert "decision_confidence" in context
        assert "extracted_keywords" in context

    def test_decision_confidence_levels(self, parser):
        """Test that parser can assess confidence in decision extraction."""
        high_confidence = [
            "Fix this immediately",
            "Skip this test",
            "Abort the workflow",
            "Continue with implementation"
        ]

        low_confidence = [
            "Maybe we should fix this",
            "I think we can skip",
            "Perhaps abort would be better",
            "We could continue I guess"
        ]

        for response in high_confidence:
            result = parser.parse_response(response)
            assert result.context["decision_confidence"] == "high"

        for response in low_confidence:
            result = parser.parse_response(response)
            assert result.context["decision_confidence"] in ["medium", "low"]


class TestUserDecision:
    """Test UserDecision data model."""

    def test_user_decision_creation(self):
        """Test UserDecision model creation and validation."""
        decision = UserDecision(
            decision_type=DecisionType.FIX,
            message="Fix the authentication issue",
            context={"confidence": "high"}
        )

        assert decision.decision_type == DecisionType.FIX
        assert decision.message == "Fix the authentication issue"
        assert decision.context["confidence"] == "high"

    def test_user_decision_with_empty_context(self):
        """Test UserDecision with minimal required fields."""
        decision = UserDecision(
            decision_type=DecisionType.SKIP,
            message="Skip this test"
        )

        assert decision.decision_type == DecisionType.SKIP
        assert decision.message == "Skip this test"
        assert decision.context == {}


class TestResponseParserIntegration:
    """Integration tests for ResponseParser with realistic scenarios."""

    def test_realistic_user_response_scenarios(self):
        """Test realistic scenarios from actual user responses."""
        parser = ResponseParser()

        # Scenario 1: User reviewing test failure and providing fix instructions
        scenario1 = """
        I've looked at the test failures in the authentication module.

        The issue is in the password validation - it's not properly handling
        edge cases like empty strings and special characters.

        Please fix the following:
        1. src/auth/validators.py - strengthen password validation
        2. Add tests for edge cases in test_auth.py
        3. Update the error messages to be more user-friendly

        This is blocking the release, so high priority.
        """

        result = parser.parse_response(scenario1)
        assert result.decision_type == DecisionType.FIX
        assert result.context["original_content"] == scenario1.strip()

        # Scenario 2: User deciding to skip a non-critical issue
        scenario2 = """
        I see there's a failing test for the email notification feature.

        This isn't critical for the current release. Let's skip this test
        for now and move forward with the core functionality.

        We can address the email notifications in the next sprint.
        """

        result = parser.parse_response(scenario2)
        assert result.decision_type == DecisionType.SKIP

        # Scenario 3: User deciding to abort due to approach issues
        scenario3 = """
        After reviewing the implementation approach, I don't think this
        is the right direction for the project.

        Please abort this workflow. We need to go back to the drawing
        board and redesign the architecture first.

        The current approach will create technical debt.
        """

        result = parser.parse_response(scenario3)
        assert result.decision_type == DecisionType.ABORT

    def test_end_to_end_message_body_parsing(self, message_factory):
        """Test complete workflow from Message body to UserDecision."""
        parser = ResponseParser()

        # Create a message with user decision in body
        user_message = message_factory(
            from_agent="user",
            to_agent="implementation-agent",
            type="blocker_response",
            subject="Re: Test Failure in Auth Module",
            body="I reviewed the failures. Please fix the authentication logic in src/auth.py. The password validation needs to handle null values properly.",
            awaiting_response=False
        )

        result = parser.parse_response(user_message.body)

        assert result.decision_type == DecisionType.FIX
        assert "fix" in result.message.lower()
        assert "authentication" in result.context["original_content"]
        assert "password validation" in result.context["original_content"]