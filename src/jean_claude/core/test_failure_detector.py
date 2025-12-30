# ABOUTME: TestFailureDetector implementation - detects test failures in agent responses
# ABOUTME: Concrete implementation of BlockerDetector interface for test failure detection

"""TestFailureDetector - Detects test failures in agent responses.

This module provides a concrete implementation of the BlockerDetector interface
that specifically looks for test failure patterns in agent responses and returns
TEST_FAILURE blocker type with detailed failure information.
"""

import re
from typing import List, Dict, Any

from .blocker_detector import BlockerDetector, BlockerDetails, BlockerType


class FailureDetector(BlockerDetector):
    """Detects test failures in agent responses.

    This detector analyzes agent responses for various test failure patterns including:
    - pytest failures (FAILED tests/...)
    - unittest failures (FAIL: test_name)
    - Assertion errors
    - Import/compilation errors in test context
    - Test-specific error messages

    When test failures are detected, it extracts relevant details and provides
    helpful suggestions for resolving the issues.
    """

    def __init__(self):
        """Initialize the TestFailureDetector with compiled patterns for efficiency."""
        # Compile regex patterns for better performance
        self._failure_patterns = [
            # pytest patterns
            re.compile(r'FAILED\s+tests?[/\\].*?::', re.IGNORECASE),
            re.compile(r'=+\s*FAILURES\s*=+', re.IGNORECASE),
            re.compile(r'=+\s*short\s+test\s+summary\s+info\s*=+', re.IGNORECASE),
            re.compile(r'pytest\s+failed', re.IGNORECASE),
            re.compile(r'\d+\s+failed.*?\d+\s+passed', re.IGNORECASE),
            re.compile(r'E\s+(AssertionError|assert)', re.IGNORECASE),

            # unittest patterns
            re.compile(r'FAIL:\s+\w+.*?\(.*?\)', re.IGNORECASE),
            re.compile(r'ERROR:\s+\w+.*?\(.*?\)', re.IGNORECASE),
            re.compile(r'FAILED\s*\(failures=\d+\)', re.IGNORECASE),

            # General test failure indicators
            re.compile(r'test\s+failed', re.IGNORECASE),
            re.compile(r'tests?\s+(are\s+)?failing', re.IGNORECASE),
            re.compile(r'test\s+suite\s+(is\s+)?broken', re.IGNORECASE),

            # Error patterns that commonly occur during testing
            re.compile(r'AssertionError:', re.IGNORECASE),
            re.compile(r'ImportError:', re.IGNORECASE),
            re.compile(r'ModuleNotFoundError:', re.IGNORECASE),
            re.compile(r'SyntaxError:', re.IGNORECASE),
            re.compile(r'IndentationError:', re.IGNORECASE),
            re.compile(r'NameError:', re.IGNORECASE),
            re.compile(r'AttributeError:', re.IGNORECASE),

            # Test-specific error contexts
            re.compile(r'fixture.*?(not|fail|error)', re.IGNORECASE),
            re.compile(r'mock.*?(not|fail|error|incorrect|wrong)', re.IGNORECASE),
            re.compile(r'test\s+(database|db).*?(fail|error|connection)', re.IGNORECASE),
            re.compile(r'test\s+coverage.*?(drop|below|fail)', re.IGNORECASE),
            re.compile(r'test\s+environment.*?(not|fail|error)', re.IGNORECASE),
        ]

        # Patterns that should NOT be considered test failures (to avoid false positives)
        self._exclusion_patterns = [
            re.compile(r'failed\s+to\s+(understand|parse|send|connect)', re.IGNORECASE),
            re.compile(r'(user|email|login|authentication)\s+failed', re.IGNORECASE),
            re.compile(r'failed\s+(attempt|approach|strategy)', re.IGNORECASE),
        ]

    def detect_blocker(self, agent_response: str) -> BlockerDetails:
        """Analyze agent response for test failures.

        Args:
            agent_response: The full response text from an agent

        Returns:
            BlockerDetails with TEST_FAILURE type if test failures are detected,
            otherwise returns BlockerType.NONE
        """
        if not agent_response or not agent_response.strip():
            return self._create_no_blocker_result()

        # Check for exclusion patterns first to avoid false positives
        if self._has_exclusion_patterns(agent_response):
            return self._create_no_blocker_result()

        # Look for test failure indicators
        failure_indicators = self._extract_failure_indicators(agent_response)

        if not failure_indicators:
            return self._create_no_blocker_result()

        # Extract additional context and create suggestions
        context = self._extract_context(agent_response, failure_indicators)
        suggestions = self._generate_suggestions(failure_indicators, context)

        return BlockerDetails(
            blocker_type=BlockerType.TEST_FAILURE,
            message="Test failure detected in agent response",
            context=context,
            suggestions=suggestions
        )

    def _has_exclusion_patterns(self, text: str) -> bool:
        """Check if text matches exclusion patterns that should not be flagged."""
        return any(pattern.search(text) for pattern in self._exclusion_patterns)

    def _extract_failure_indicators(self, text: str) -> List[str]:
        """Extract specific failure indicators from the text."""
        indicators = []

        for pattern in self._failure_patterns:
            matches = pattern.findall(text)
            if matches:
                # Add the pattern description and matches
                indicators.extend(matches if isinstance(matches[0], str) else [str(m) for m in matches])

        # Also look for specific failure lines
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            for pattern in self._failure_patterns:
                if pattern.search(line):
                    indicators.append(line)
                    break

        # Remove duplicates while preserving order
        seen = set()
        unique_indicators = []
        for indicator in indicators:
            indicator_clean = indicator.strip()
            if indicator_clean and indicator_clean not in seen:
                seen.add(indicator_clean)
                unique_indicators.append(indicator_clean)

        return unique_indicators

    def _extract_context(self, text: str, failure_indicators: List[str]) -> Dict[str, Any]:
        """Extract additional context about the test failures."""
        context = {
            "failure_indicators": failure_indicators,
            "response_length": len(text),
            "has_stack_trace": False,
            "test_files": [],
            "error_types": []
        }

        # Look for stack trace patterns
        if re.search(r'Traceback|File ".*?", line \d+', text, re.IGNORECASE):
            context["has_stack_trace"] = True

        # Extract test file names
        test_file_pattern = re.compile(r'tests?[/\\][^:\s]+\.py', re.IGNORECASE)
        test_files = test_file_pattern.findall(text)
        if test_files:
            context["test_files"] = list(set(test_files))  # Remove duplicates

        # Extract error types
        error_types = re.findall(r'(\w*Error):', text)
        if error_types:
            context["error_types"] = list(set(error_types))

        return context

    def _generate_suggestions(self, failure_indicators: List[str], context: Dict[str, Any]) -> List[str]:
        """Generate helpful suggestions for resolving test failures."""
        suggestions = []

        # Always include basic suggestions
        suggestions.append("Review the test implementation and fix any assertion errors")
        suggestions.append("Check test data and mock configurations")

        # Add specific suggestions based on context
        if context.get("error_types"):
            error_types = context["error_types"]
            if "ImportError" in error_types or "ModuleNotFoundError" in error_types:
                suggestions.append("Verify import statements and module dependencies")
            if "AssertionError" in error_types:
                suggestions.append("Review assertion logic and expected vs actual values")
            if "AttributeError" in error_types:
                suggestions.append("Check object attribute names and method calls")
            if "SyntaxError" in error_types or "IndentationError" in error_types:
                suggestions.append("Fix syntax errors and indentation issues")

        # Suggestions based on test files
        if context.get("test_files"):
            suggestions.append("Focus on the failing test files: " + ", ".join(context["test_files"]))

        # Suggestions based on failure patterns
        indicator_text = " ".join(failure_indicators).lower()
        if "fixture" in indicator_text:
            suggestions.append("Check pytest fixture setup and teardown")
        if "mock" in indicator_text:
            suggestions.append("Verify mock object configurations and return values")
        if "database" in indicator_text or "db" in indicator_text:
            suggestions.append("Check test database setup and connection")
        if "coverage" in indicator_text:
            suggestions.append("Review test coverage requirements and add missing tests")

        # Add investigation suggestion
        suggestions.append("Run tests individually to isolate specific failures")

        return suggestions[:6]  # Limit to 6 suggestions to avoid overwhelming

    def _create_no_blocker_result(self) -> BlockerDetails:
        """Create a result indicating no test failures were detected."""
        return BlockerDetails(
            blocker_type=BlockerType.NONE,
            message="No test failures detected in agent response"
        )