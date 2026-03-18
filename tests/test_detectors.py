# ABOUTME: Consolidated tests for all blocker detectors (ambiguity, error, failure)
# ABOUTME: Merges 3 near-identical detector test files into 1 with shared patterns

"""Consolidated tests for AmbiguityDetector, ErrorDetector, and FailureDetector.

Each detector inherits from BlockerDetector and follows the same interface:
detect_blocker(text) -> BlockerDetails. Tests are organized by shared patterns
(inheritance, case insensitivity, false positives) and detector-specific logic.
"""

import pytest

from jean_claude.core.blocker_detector import BlockerDetector, BlockerType, BlockerDetails
from jean_claude.core.ambiguity_detector import AmbiguityDetector
from jean_claude.core.error_detector import ErrorDetector
from jean_claude.core.test_failure_detector import FailureDetector


# ── Shared structural tests (parametrized over all 3 detectors) ──────────


ALL_DETECTORS = [AmbiguityDetector, ErrorDetector, FailureDetector]


@pytest.mark.parametrize("detector_cls", ALL_DETECTORS)
class TestDetectorSharedBehavior:
    """Tests that apply identically to all 3 detectors."""

    def test_inherits_from_blocker_detector(self, detector_cls):
        detector = detector_cls()
        assert isinstance(detector, BlockerDetector)
        assert hasattr(detector, "detect_blocker")

    def test_case_insensitive_detection(self, detector_cls):
        """All detectors work regardless of input case."""
        detector = detector_cls()
        if detector_cls is AmbiguityDetector:
            pairs = [
                ("COULD YOU CLARIFY the requirements?", BlockerType.AMBIGUITY),
                ("could you clarify the requirements?", BlockerType.AMBIGUITY),
                ("I NEED CLARIFICATION on this feature", BlockerType.AMBIGUITY),
            ]
        elif detector_cls is ErrorDetector:
            pairs = [
                ("I'M STUCK on this implementation", BlockerType.ERROR),
                ("i'm stuck on this implementation", BlockerType.ERROR),
                ("AN ERROR OCCURRED during processing", BlockerType.ERROR),
            ]
        else:  # FailureDetector
            pairs = [
                ("FAILED tests/test_auth.py::test_login", BlockerType.TEST_FAILURE),
                ("failed tests/test_auth.py::test_login", BlockerType.TEST_FAILURE),
                ("TEST FAILED with assertion error", BlockerType.TEST_FAILURE),
            ]

        for text, expected_type in pairs:
            result = detector.detect_blocker(text)
            assert result.blocker_type == expected_type


# ── AmbiguityDetector tests ─────────────────────────────────────────────


class TestAmbiguityDetector:
    """Tests specific to AmbiguityDetector."""

    @pytest.fixture
    def detector(self) -> AmbiguityDetector:
        return AmbiguityDetector()

    def test_detects_all_ambiguity_patterns(self, detector):
        """Consolidated test for clarification, question, uncertainty, requirement, and assumption patterns."""
        ambiguity_inputs = [
            # Direct clarification requests
            "Could you clarify the requirements?",
            "I need clarification on the database schema",
            "Can you provide more details about the API structure?",
            "Please clarify what should happen when the user clicks this",
            "I need more information about the expected behavior",
            "Could you explain how the authentication should work?",
            # Question-based ambiguity
            "Should I use REST or GraphQL for the API?",
            "What database should I use for this feature?",
            "Which authentication method would be best?",
            "How should I handle error cases in this scenario?",
            "What validation rules should I apply to user input?",
            "Should this be a synchronous or asynchronous operation?",
            # Uncertainty and options
            "I'm not sure which approach to take for this implementation",
            "There are several ways to implement this, which would you prefer?",
            "I'm uncertain about the data model for this feature",
            "Not sure if I should use a library or implement this from scratch",
            "I'm unsure about the best way to handle this edge case",
            # Requirement understanding issues
            "I don't understand the exact requirements for this feature",
            "The requirements are not clear to me",
            "I'm having trouble understanding what the user needs",
            "The acceptance criteria seem ambiguous",
            "The specifications are unclear in this section",
            # Assumption validation
            "I'm assuming the API should return JSON - is that correct?",
            "Should I assume users are always authenticated for this endpoint?",
            "I assume we want to validate email formats - correct?",
            "My assumption is that we store passwords hashed - right?",
        ]

        for text in ambiguity_inputs:
            result = detector.detect_blocker(text)
            assert result.blocker_type == BlockerType.AMBIGUITY, f"Failed for: {text}"
            assert "ambiguity" in result.message.lower()

    def test_no_ambiguity_detected(self, detector):
        """Clear statements are not flagged as ambiguous."""
        clear_responses = [
            "I've successfully implemented the authentication feature.",
            "The code has been refactored and is working well.",
            "I'm working on the implementation now.",
            "The feature is complete and ready for review.",
            "All changes have been committed successfully.",
            "",
            "The implementation follows the specified requirements.",
        ]

        for response in clear_responses:
            result = detector.detect_blocker(response)
            assert result.blocker_type == BlockerType.NONE

    def test_extract_ambiguity_details(self, detector):
        """Ambiguity context and suggestions are properly extracted."""
        complex_ambiguity = """
        I have several questions about the requirements that I need clarification on:
        1. Should notifications be sent via email, SMS, push notifications, or all three?
        2. How long should notifications be stored in the database?
        I'm not sure which approach to take without this clarification.
        Could you provide guidance on these points?
        """

        result = detector.detect_blocker(complex_ambiguity)
        assert result.blocker_type == BlockerType.AMBIGUITY
        assert result.context is not None
        assert "ambiguity_indicators" in result.context
        assert len(result.context["ambiguity_indicators"]) > 0
        assert len(result.suggestions) > 0
        suggestion_text = " ".join(result.suggestions).lower()
        assert any(kw in suggestion_text for kw in ["clarify", "provide", "specify", "detail", "requirement"])

    def test_edge_cases_and_false_positives(self, detector):
        """Discussing clarification (not requesting it) should not trigger."""
        edge_cases = [
            "The user can clarify their preferences in the settings.",
            "This feature helps clarify the data structure.",
            "The error message should clarify what went wrong.",
            "I need to clarify the code with better comments.",
            "Let me clarify my implementation approach.",
            "This clarifies the business logic requirements.",
            "I need to ask the database for user information.",
            "Should I continue with the current implementation?",
        ]

        for text in edge_cases:
            result = detector.detect_blocker(text)
            assert result.blocker_type == BlockerType.NONE

    def test_mixed_content_with_ambiguity(self, detector):
        """Ambiguity in longer mixed content is still detected."""
        mixed_content = """
        I've been working on implementing the payment processing feature.
        The basic structure is in place and the Stripe integration is configured.

        However, I need clarification on a few important details:
        Should we store payment history permanently or just for a limited time?
        I'm not sure how to proceed without this information.
        """

        result = detector.detect_blocker(mixed_content)
        assert result.blocker_type == BlockerType.AMBIGUITY

    def test_distinguish_from_other_blocker_types(self, detector):
        """Non-ambiguity blockers should not be flagged as AMBIGUITY."""
        non_ambiguity = [
            "I'm stuck and can't continue with this implementation.",
            "FAILED tests/test_auth.py::test_login - AssertionError",
            "RuntimeError: Cannot connect to database",
        ]

        for response in non_ambiguity:
            result = detector.detect_blocker(response)
            assert result.blocker_type != BlockerType.AMBIGUITY

    def test_realistic_agent_ambiguity_scenario(self):
        """End-to-end realistic ambiguity scenario."""
        detector = AmbiguityDetector()

        scenario = """
        I'm implementing the user dashboard feature as requested.
        I have a question about the requirements:
        Should the dashboard display real-time data or cached data?
        Could you clarify your preference so I can complete the implementation?
        """

        result = detector.detect_blocker(scenario)
        assert result.blocker_type == BlockerType.AMBIGUITY
        assert result.context["ambiguity_indicators"]
        assert len(result.suggestions) > 0


# ── ErrorDetector tests ─────────────────────────────────────────────────


class TestErrorDetector:
    """Tests specific to ErrorDetector."""

    @pytest.fixture
    def detector(self) -> ErrorDetector:
        return ErrorDetector()

    def test_detects_all_error_patterns(self, detector):
        """Consolidated test for stuck, error reporting, technical, and workflow-blocking patterns."""
        error_inputs = [
            # Agent stuck
            "I'm stuck on this problem and need help",
            "I can't figure out how to implement this feature",
            "I'm unable to complete this task without more information",
            "I'm blocked and can't continue",
            "This is beyond my capabilities",
            # Agent error reporting
            "I encountered an error while processing",
            "An error occurred during implementation",
            "Something went wrong with the execution",
            "The implementation failed due to an error",
            "An unexpected error has occurred",
            "Critical error encountered during execution",
            # Technical errors
            "RuntimeError: Cannot complete operation",
            "ConnectionError: Unable to connect to service",
            "TimeoutError: Operation timed out",
            "ValueError: Invalid parameter provided",
            "KeyError: Required key not found",
            "FileNotFoundError: File does not exist",
            # Workflow-blocking
            "The API endpoint is not responding",
            "Cannot access the required database",
            "Missing dependencies prevent execution",
            "Authentication credentials are invalid",
        ]

        for text in error_inputs:
            result = detector.detect_blocker(text)
            assert result.blocker_type == BlockerType.ERROR, f"Failed for: {text}"
            assert "error" in result.message.lower()

    def test_no_errors_detected(self, detector):
        """Normal responses are not flagged as errors."""
        normal_responses = [
            "I've successfully implemented the authentication feature.",
            "The code has been refactored and is working well.",
            "Let me analyze the requirements first.",
            "The feature is complete and ready for review.",
            "",
            "The implementation is progressing smoothly.",
        ]

        for response in normal_responses:
            result = detector.detect_blocker(response)
            assert result.blocker_type in [BlockerType.NONE, BlockerType.AMBIGUITY]

    def test_extract_error_details(self, detector):
        """Error context and suggestions are properly extracted."""
        complex_error = """
        I'm encountering several critical issues that prevent me from continuing:
        1. RuntimeError: Cannot establish connection to the database server
        2. ConfigurationError: Missing required environment variables
        I'm stuck and unable to proceed without resolving these errors.
        """

        result = detector.detect_blocker(complex_error)
        assert result.blocker_type == BlockerType.ERROR
        assert result.context is not None
        assert "error_indicators" in result.context
        assert len(result.context["error_indicators"]) > 0
        assert len(result.suggestions) > 0
        suggestion_text = " ".join(result.suggestions).lower()
        assert any(kw in suggestion_text for kw in ["review", "check", "fix", "investigate", "resolve", "debug"])

    def test_edge_cases_and_false_positives(self, detector):
        """Discussing errors (not reporting them) should not trigger."""
        edge_cases = [
            "The error handling in this code needs improvement.",
            "I need to add error checking to the function.",
            "The user might encounter an error if they...",
            "Let me implement better error messages.",
            "This prevents errors from occurring.",
            "Error logs should be written to file.",
            "The previous version had errors, but this fixes them.",
        ]

        for text in edge_cases:
            result = detector.detect_blocker(text)
            assert result.blocker_type == BlockerType.NONE

    def test_mixed_content_with_errors(self, detector):
        """Errors in longer mixed content are still detected."""
        mixed_content = """
        I've been working on implementing the user authentication feature.
        However, I'm encountering a critical issue that's blocking progress:
        RuntimeError: Cannot establish secure connection to authentication service
        I'm stuck and cannot continue until this is resolved.
        """

        result = detector.detect_blocker(mixed_content)
        assert result.blocker_type == BlockerType.ERROR

    def test_ambiguous_vs_error_distinction(self, detector):
        """Ambiguous requests should not be flagged as ERROR."""
        ambiguous_responses = [
            "Could you clarify the requirements?",
            "I need more information about the database schema.",
            "Should I use REST or GraphQL for the API?",
        ]

        for response in ambiguous_responses:
            result = detector.detect_blocker(response)
            assert result.blocker_type != BlockerType.ERROR

    def test_realistic_agent_error_scenario(self):
        """End-to-end realistic error scenario."""
        detector = ErrorDetector()

        scenario = """
        I've implemented the file upload feature.
        However, I've encountered a critical error:
        PermissionError: [Errno 13] Permission denied: '/uploads/temp'
        I'm unable to proceed with testing the upload functionality.
        """

        result = detector.detect_blocker(scenario)
        assert result.blocker_type == BlockerType.ERROR
        assert result.context["error_indicators"]
        assert len(result.suggestions) > 0


# ── FailureDetector tests ───────────────────────────────────────────────


class TestFailureDetector:
    """Tests specific to FailureDetector (test failures)."""

    @pytest.fixture
    def detector(self) -> FailureDetector:
        return FailureDetector()

    def test_detects_all_failure_patterns(self, detector):
        """Consolidated test for pytest, unittest, compilation, and test-specific error patterns."""
        failure_inputs = [
            # pytest failures
            "FAILED tests/test_auth.py::test_login - AssertionError: Expected True but got False",
            "FAILED tests/core/test_message.py::test_save - KeyError: 'missing_field'",
            "========================== FAILURES ==========================",
            "E   AssertionError: assert False",
            "3 failed, 2 passed in 0.12s",
            "pytest failed with 3 failures",
            # unittest failures
            "FAIL: test_login (tests.test_auth.TestAuth)",
            "AssertionError: Lists differ: ['a', 'b'] != ['a', 'c']",
            "Ran 5 tests in 0.002s\n\nFAILED (failures=1)",
            "ERROR: test_connection (tests.test_db.TestDatabase)",
            # Compilation and import errors
            "ImportError: No module named 'nonexistent'",
            "SyntaxError: invalid syntax (test_file.py, line 10)",
            "ModuleNotFoundError: No module named 'missing_module'",
            "NameError: name 'undefined_var' is not defined",
            "AttributeError: 'NoneType' object has no attribute 'method'",
            # Test-specific indicators
            "Tests are failing due to assertion errors",
            "The test suite is broken",
            "Test coverage dropped below threshold",
            "Fixtures are not working correctly",
            "Mock setup is incorrect",
        ]

        for text in failure_inputs:
            result = detector.detect_blocker(text)
            assert result.blocker_type == BlockerType.TEST_FAILURE, f"Failed for: {text}"
            assert "test failure" in result.message.lower()

    def test_no_test_failures_detected(self, detector):
        """Non-test-related responses are not flagged."""
        normal_responses = [
            "I've successfully implemented the authentication feature.",
            "The code has been refactored and is working well.",
            "Let me analyze the requirements first.",
            "The feature is complete and ready for review.",
            "",
            "Generating documentation for the API.",
        ]

        for response in normal_responses:
            result = detector.detect_blocker(response)
            assert result.blocker_type == BlockerType.NONE
            assert "no test failures detected" in result.message.lower()

    def test_extract_test_failure_details(self, detector):
        """Failure context and suggestions are properly extracted."""
        complex_failure = """
        ========================== FAILURES ==========================
        ______________ TestAuth.test_user_login ______________
        >       assert user.is_authenticated() == True
        E       AssertionError: assert False == True
        tests/test_auth.py:42: AssertionError
        2 failed, 3 passed in 0.50s
        """

        result = detector.detect_blocker(complex_failure)
        assert result.blocker_type == BlockerType.TEST_FAILURE
        assert result.context is not None
        assert "failure_indicators" in result.context
        assert len(result.context["failure_indicators"]) > 0
        assert len(result.suggestions) > 0
        suggestion_text = " ".join(result.suggestions).lower()
        assert any(kw in suggestion_text for kw in ["review", "check", "fix", "investigate", "test", "debug"])

    def test_edge_cases_and_false_positives(self, detector):
        """Non-test-related uses of 'failed' should not trigger."""
        edge_cases = [
            "The word 'failed' appears in this sentence but not about tests.",
            "I failed to understand the requirements.",
            "The previous attempt failed, so I'm trying a different approach.",
            "This email failed to send.",
            "The user failed to authenticate.",
        ]

        for text in edge_cases:
            result = detector.detect_blocker(text)
            assert result.blocker_type == BlockerType.NONE

    def test_mixed_content_with_test_failures(self, detector):
        """Test failures in longer mixed content are still detected."""
        mixed_content = """
        I've been working on implementing the user authentication feature.
        However, when I ran the tests:
        FAILED tests/test_auth.py::test_password_validation - AssertionError
        The password validation logic needs to be reviewed.
        """

        result = detector.detect_blocker(mixed_content)
        assert result.blocker_type == BlockerType.TEST_FAILURE

    def test_realistic_agent_failure_scenario(self):
        """End-to-end realistic test failure scenario."""
        detector = FailureDetector()

        scenario = """
        I've implemented the email validation feature.
        When I ran the test suite:
        FAILED tests/test_user.py::test_email_validation_valid - AssertionError: Expected True but got False
        FAILED tests/test_user.py::test_email_validation_invalid - AssertionError: Expected False but got True
        It looks like my email regex pattern needs adjustment.
        """

        result = detector.detect_blocker(scenario)
        assert result.blocker_type == BlockerType.TEST_FAILURE
        assert result.context["failure_indicators"]
        assert len(result.suggestions) > 0
