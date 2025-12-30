# ABOUTME: Tests for TestFailureDetector - detects test failures in agent responses
# ABOUTME: Consolidated test suite for test failure detection logic

"""Tests for TestFailureDetector implementation.

Following the project's testing patterns for comprehensive coverage with
consolidated test cases and proper fixture usage.
"""

import pytest

from jean_claude.core.blocker_detector import BlockerType, BlockerDetails
from jean_claude.core.test_failure_detector import FailureDetector


class TestTestFailureDetector:
    """Test TestFailureDetector - consolidated test failure detection."""

    @pytest.fixture
    def detector(self) -> FailureDetector:
        """Create FailureDetector instance."""
        return FailureDetector()

    def test_detector_inherits_from_blocker_detector(self, detector):
        """Test that TestFailureDetector properly inherits from BlockerDetector."""
        from jean_claude.core.blocker_detector import BlockerDetector
        assert isinstance(detector, BlockerDetector)
        assert hasattr(detector, 'detect_blocker')

    def test_pytest_test_failure_patterns(self, detector):
        """Test detection of various pytest test failure patterns."""
        # Test classic pytest failures
        pytest_failures = [
            "FAILED tests/test_auth.py::test_login - AssertionError: Expected True but got False",
            "FAILED tests/core/test_message.py::test_save - KeyError: 'missing_field'",
            "FAILED tests/test_workflow.py::test_complete - ValueError: invalid state",
            "Test session starts (platform: linux, Python 3.11.0)\n\nFAILED tests/test_auth.py::test_user_creation",
            "========================== FAILURES ==========================",
            "======================== short test summary info =========================\nFAILED tests/test_basic.py::test_something",
            "E   AssertionError: assert False",
            "E   assert 1 == 2",
            "pytest failed with 3 failures",
            "3 failed, 2 passed in 0.12s",
            "Test failed: AssertionError",
        ]

        for failure_text in pytest_failures:
            result = detector.detect_blocker(failure_text)
            assert result.blocker_type == BlockerType.TEST_FAILURE
            assert "test failure" in result.message.lower()
            assert result.context is not None
            assert len(result.suggestions) > 0

    def test_unittest_failure_patterns(self, detector):
        """Test detection of unittest failure patterns."""
        unittest_failures = [
            "FAIL: test_login (tests.test_auth.TestAuth)",
            "AssertionError: Lists differ: ['a', 'b'] != ['a', 'c']",
            "Ran 5 tests in 0.002s\n\nFAILED (failures=1)",
            "ERROR: test_connection (tests.test_db.TestDatabase)",
            # Note: "unittest.mock.MagicMock object at 0x123" removed - it's just a repr, not a failure
        ]

        for failure_text in unittest_failures:
            result = detector.detect_blocker(failure_text)
            assert result.blocker_type == BlockerType.TEST_FAILURE
            assert "test failure" in result.message.lower()

    def test_compilation_and_import_errors(self, detector):
        """Test detection of compilation and import errors in test context."""
        error_patterns = [
            "ImportError: No module named 'nonexistent'",
            "SyntaxError: invalid syntax (test_file.py, line 10)",
            "ModuleNotFoundError: No module named 'missing_module'",
            "IndentationError: expected an indented block (test_auth.py, line 15)",
            "NameError: name 'undefined_var' is not defined",
            "AttributeError: 'NoneType' object has no attribute 'method'",
        ]

        for error_text in error_patterns:
            result = detector.detect_blocker(error_text)
            assert result.blocker_type == BlockerType.TEST_FAILURE
            assert "test failure" in result.message.lower()

    def test_test_specific_error_indicators(self, detector):
        """Test detection of test-specific error indicators."""
        test_errors = [
            "Tests are failing due to assertion errors",
            "The test suite is broken",
            "Test coverage dropped below threshold",
            "Fixtures are not working correctly",
            "Mock setup is incorrect",
            "Test database connection failed",
            "Test environment is not properly configured",
        ]

        for error_text in test_errors:
            result = detector.detect_blocker(error_text)
            assert result.blocker_type == BlockerType.TEST_FAILURE
            assert "test failure" in result.message.lower()

    def test_no_test_failures_detected(self, detector):
        """Test that non-test-related responses are not flagged."""
        normal_responses = [
            "I've successfully implemented the authentication feature.",
            "The code has been refactored and is working well.",
            "Let me analyze the requirements first.",
            "I need clarification on the database schema.",
            "The feature is complete and ready for review.",
            "All changes have been committed successfully.",
            "I'm working on the implementation now.",
            "",
            "Generating documentation for the API.",
        ]

        for response in normal_responses:
            result = detector.detect_blocker(response)
            assert result.blocker_type == BlockerType.NONE
            assert "no test failures detected" in result.message.lower()

    def test_extract_test_failure_details(self, detector):
        """Test extraction of specific test failure details."""
        complex_failure = """
        I tried to run the test suite but encountered several issues:

        ========================== FAILURES ==========================
        ______________ TestAuth.test_user_login ______________

        def test_user_login():
        >       assert user.is_authenticated() == True
        E       AssertionError: assert False == True
        E        +  where False = <bound method User.is_authenticated of <User: testuser>>()

        tests/test_auth.py:42: AssertionError

        ______________ TestDatabase.test_connection ______________

        def test_connection():
        >       assert db.connect()
        E       ConnectionError: Unable to connect to database

        tests/test_db.py:15: ConnectionError

        =========================== FAILURES ===========================
        2 failed, 3 passed in 0.50s

        The authentication logic needs to be fixed.
        """

        result = detector.detect_blocker(complex_failure)

        assert result.blocker_type == BlockerType.TEST_FAILURE
        assert "test failure" in result.message.lower()

        # Check that context contains useful information
        context = result.context
        assert context is not None
        assert "failure_indicators" in context
        assert len(context["failure_indicators"]) > 0

        # Check suggestions are provided
        assert len(result.suggestions) > 0
        suggestion_text = " ".join(result.suggestions).lower()
        assert any(keyword in suggestion_text for keyword in [
            "review", "check", "fix", "investigate", "test", "debug"
        ])

    def test_case_insensitive_detection(self, detector):
        """Test that detection works regardless of case."""
        case_variations = [
            "FAILED tests/test_auth.py::test_login",
            "failed tests/test_auth.py::test_login",
            "Failed tests/test_auth.py::test_login",
            "TEST FAILED with assertion error",
            "test failed with assertion error",
            "Test Failed with assertion error",
        ]

        for failure_text in case_variations:
            result = detector.detect_blocker(failure_text)
            assert result.blocker_type == BlockerType.TEST_FAILURE

    def test_edge_cases_and_false_positives(self, detector):
        """Test edge cases that might cause false positives."""
        edge_cases = [
            "The word 'failed' appears in this sentence but not about tests.",
            "I failed to understand the requirements.", # This should still be NONE since not test-related
            "The previous attempt failed, so I'm trying a different approach.",
            "This email failed to send.",
            "The user failed to authenticate.", # Not a test failure
        ]

        for text in edge_cases:
            result = detector.detect_blocker(text)
            # These should be NONE since they're not test-specific failures
            assert result.blocker_type == BlockerType.NONE

    def test_mixed_content_with_test_failures(self, detector):
        """Test detection in mixed content where test failures are present."""
        mixed_content = """
        I've been working on implementing the user authentication feature.
        The basic structure is in place and the models have been created.

        However, when I ran the tests, I encountered some issues:

        FAILED tests/test_auth.py::test_password_validation - AssertionError

        The password validation logic needs to be reviewed.
        Let me fix this and re-run the tests.
        """

        result = detector.detect_blocker(mixed_content)
        assert result.blocker_type == BlockerType.TEST_FAILURE
        assert "test failure" in result.message.lower()


class TestTestFailureDetectorIntegration:
    """Integration tests for FailureDetector."""

    def test_realistic_agent_response_scenarios(self):
        """Test realistic scenarios from actual agent responses."""
        detector = FailureDetector()

        # Scenario 1: Agent reports test failure during implementation
        scenario1 = """
        I've implemented the email validation feature as requested.

        Here's what I've done:
        1. Added email validation to the User model
        2. Created test cases for valid and invalid emails
        3. Updated the registration form

        However, when I ran the test suite to verify the implementation:

        FAILED tests/test_user.py::test_email_validation_valid - AssertionError: Expected True but got False
        FAILED tests/test_user.py::test_email_validation_invalid - AssertionError: Expected False but got True

        It looks like my email regex pattern needs adjustment. Let me fix this.
        """

        result = detector.detect_blocker(scenario1)
        assert result.blocker_type == BlockerType.TEST_FAILURE
        assert result.context["failure_indicators"]
        assert len(result.suggestions) > 0

        # Scenario 2: Agent encounters import error during testing
        scenario2 = """
        I'm working on the database migration feature. I've created the migration files
        and updated the models accordingly.

        When testing the changes:
        ImportError: No module named 'django.contrib.auth.migrations'

        There seems to be an issue with the import path. Let me investigate.
        """

        result = detector.detect_blocker(scenario2)
        assert result.blocker_type == BlockerType.TEST_FAILURE

    def test_end_to_end_test_failure_workflow(self):
        """Test complete workflow from agent response to blocker details."""
        detector = FailureDetector()

        # Simulate agent response with test failures
        agent_response = """
        I've completed the implementation of the shopping cart feature with the following components:

        1. Cart model with add/remove item functionality
        2. Cart serializers for API responses
        3. Cart views with CRUD operations
        4. URL routing for cart endpoints

        I ran the test suite to verify everything works correctly:

        python manage.py test

        ========================== FAILURES ==========================
        ______________ TestShoppingCart.test_add_item ______________

        def test_add_item():
        >       assert cart.total_items == 1
        E       AssertionError: assert 0 == 1

        tests/test_cart.py:25: AssertionError
        ______________ TestShoppingCart.test_calculate_total ______________

        def test_calculate_total():
        >       assert cart.total_price == Decimal('19.99')
        E       AssertionError: assert Decimal('0.00') == Decimal('19.99')

        tests/test_cart.py:35: AssertionError
        =========================== FAILURES ===========================
        2 failed, 8 passed in 0.75s

        There appear to be issues with my cart calculation logic. I need to review
        the add_item method and price calculation algorithms.
        """

        result = detector.detect_blocker(agent_response)

        # Verify detection worked correctly
        assert result.blocker_type == BlockerType.TEST_FAILURE
        assert "test failure detected" in result.message.lower()

        # Verify context extraction
        assert result.context is not None
        assert "failure_indicators" in result.context
        assert len(result.context["failure_indicators"]) > 0

        # Verify useful suggestions are provided
        assert len(result.suggestions) > 0
        suggestions_text = " ".join(result.suggestions).lower()
        assert any(keyword in suggestions_text for keyword in [
            "review", "check", "debug", "fix", "investigate", "test"
        ])