# ABOUTME: ErrorDetector implementation - detects agent errors and stuck states
# ABOUTME: Concrete implementation of BlockerDetector interface for error detection

"""ErrorDetector - Detects agent errors and stuck states in agent responses.

This module provides a concrete implementation of the BlockerDetector interface
that specifically looks for error patterns and stuck states in agent responses
and returns ERROR blocker type with detailed error information.
"""

import re
from typing import List, Dict, Any

from .blocker_detector import BlockerDetector, BlockerDetails, BlockerType


class ErrorDetector(BlockerDetector):
    """Detects errors and stuck states in agent responses.

    This detector analyzes agent responses for various error patterns including:
    - Agent stuck states ("I'm stuck", "I don't know how", etc.)
    - Technical errors (RuntimeError, ConnectionError, etc.)
    - Workflow-blocking issues (API failures, missing dependencies, etc.)
    - Agent confusion and inability to proceed

    When errors are detected, it extracts relevant details and provides
    helpful suggestions for resolving the issues.
    """

    def __init__(self):
        """Initialize the ErrorDetector with compiled patterns for efficiency."""
        # Compile regex patterns for better performance
        self._error_patterns = [
            # Agent stuck patterns
            re.compile(r"i\'?m\s+(stuck|blocked|unable|confused)", re.IGNORECASE),
            re.compile(r"(can\'t|cannot)\s+(figure\s+out|understand|proceed|continue|complete)", re.IGNORECASE),
            re.compile(r"don\'t\s+know\s+(how\s+to|what\s+to)", re.IGNORECASE),
            re.compile(r"(need\s+help|at\s+a\s+loss|struggling\s+to)", re.IGNORECASE),
            re.compile(r"beyond\s+my\s+capabilities", re.IGNORECASE),
            re.compile(r"(having\s+difficulty|difficulty\s+understanding)", re.IGNORECASE),
            re.compile(r"(not\s+sure|unsure)\s+(how\s+to|about|what|of)", re.IGNORECASE),

            # General error indicators
            re.compile(r"(error\s+(has\s+)?occurred|encountered\s+an?\s+error|ran\s+into\s+.*error)", re.IGNORECASE),
            re.compile(r"(unexpected\s+error|something\s+went\s+wrong|technical\s+difficulties)", re.IGNORECASE),
            re.compile(r"(failed\s+(to|due\s+to|with)|unable\s+to|cannot\s+.*|can\'t\s+.*)", re.IGNORECASE),
            re.compile(r"(critical\s+error|blocking\s+(issue|error))", re.IGNORECASE),
            re.compile(r"(implementation\s+failed|process\s+failed)", re.IGNORECASE),
            re.compile(r"(there\'?s?\s+an?\s+)?(issues?|problems?)\s+(with|that\s+prevent)", re.IGNORECASE),
            re.compile(r"(issues?|problems?)\s+prevent", re.IGNORECASE),

            # Technical error types - common Python/system errors
            re.compile(r"RuntimeError:", re.IGNORECASE),
            re.compile(r"ConnectionError:", re.IGNORECASE),
            re.compile(r"TimeoutError:", re.IGNORECASE),
            re.compile(r"ValueError:", re.IGNORECASE),
            re.compile(r"KeyError:", re.IGNORECASE),
            re.compile(r"FileNotFoundError:", re.IGNORECASE),
            re.compile(r"PermissionError:", re.IGNORECASE),
            re.compile(r"ConfigurationError:", re.IGNORECASE),
            re.compile(r"ServiceUnavailableError:", re.IGNORECASE),
            re.compile(r"DatabaseError:", re.IGNORECASE),

            # Infrastructure and service errors
            re.compile(r"(api\s+.*not\s+responding|endpoint.*not\s+responding)", re.IGNORECASE),
            re.compile(r"(cannot\s+access.*database|database.*connection\s+failed)", re.IGNORECASE),
            re.compile(r"(missing\s+dependencies|dependencies.*prevent)", re.IGNORECASE),
            re.compile(r"(configuration.*corrupted|invalid\s+configuration)", re.IGNORECASE),
            re.compile(r"(network.*issues|connectivity\s+issues)", re.IGNORECASE),
            re.compile(r"(authentication.*invalid|credentials.*invalid)", re.IGNORECASE),
            re.compile(r"(services.*unavailable|required\s+services)", re.IGNORECASE),
            re.compile(r"(permissions.*insufficient|access\s+denied)", re.IGNORECASE),
            re.compile(r"(resource\s+limits|system\s+compatibility)", re.IGNORECASE),
        ]

        # Patterns that should NOT be considered errors (to avoid false positives)
        self._exclusion_patterns = [
            re.compile(r"error\s+(handling|checking|messages?|logs?)", re.IGNORECASE),
            re.compile(r"\b(add|implement|improve|fix)\b.*error", re.IGNORECASE),
            re.compile(r"(prevents?\s+errors|avoid.*errors)", re.IGNORECASE),
            re.compile(r"(user.*error|user.*might.*error)", re.IGNORECASE),
            re.compile(r"(previous.*errors?|had\s+errors)", re.IGNORECASE),
            re.compile(r"discussing\s+errors", re.IGNORECASE),
            # Note: Removed ambiguity patterns - they caused false negatives when agents
            # were genuinely stuck but happened to ask questions
        ]

    def detect_blocker(self, agent_response: str) -> BlockerDetails:
        """Analyze agent response for errors and stuck states.

        Args:
            agent_response: The full response text from an agent

        Returns:
            BlockerDetails with ERROR type if errors are detected,
            otherwise returns BlockerType.NONE
        """
        if not agent_response or not agent_response.strip():
            return self._create_no_blocker_result()

        # Check for exclusion patterns first to avoid false positives
        if self._has_exclusion_patterns(agent_response):
            return self._create_no_blocker_result()

        # Look for error indicators
        error_indicators = self._extract_error_indicators(agent_response)

        if not error_indicators:
            return self._create_no_blocker_result()

        # Extract additional context and create suggestions
        context = self._extract_context(agent_response, error_indicators)
        suggestions = self._generate_suggestions(error_indicators, context)

        return BlockerDetails(
            blocker_type=BlockerType.ERROR,
            message="Error or stuck state detected in agent response",
            context=context,
            suggestions=suggestions
        )

    def _has_exclusion_patterns(self, text: str) -> bool:
        """Check if text matches exclusion patterns that should not be flagged."""
        return any(pattern.search(text) for pattern in self._exclusion_patterns)

    def _extract_error_indicators(self, text: str) -> List[str]:
        """Extract specific error indicators from the text."""
        indicators = []

        for pattern in self._error_patterns:
            matches = pattern.findall(text)
            if matches:
                # Add the pattern description and matches
                indicators.extend(matches if isinstance(matches[0], str) else [str(m) for m in matches])

        # Also look for specific error lines
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            for pattern in self._error_patterns:
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

    def _extract_context(self, text: str, error_indicators: List[str]) -> Dict[str, Any]:
        """Extract additional context about the errors."""
        context = {
            "error_indicators": error_indicators,
            "response_length": len(text),
            "has_stack_trace": False,
            "error_types": [],
            "stuck_indicators": [],
            "technical_errors": []
        }

        # Look for stack trace patterns
        if re.search(r'Traceback|File ".*?", line \d+', text, re.IGNORECASE):
            context["has_stack_trace"] = True

        # Categorize error types
        indicator_text = " ".join(error_indicators).lower()

        # Check for stuck state indicators
        stuck_keywords = ["stuck", "blocked", "confused", "don't know", "can't", "unable"]
        context["stuck_indicators"] = [kw for kw in stuck_keywords if kw in indicator_text]

        # Extract technical error types
        error_types = re.findall(r'(\w*Error):', text)
        if error_types:
            context["error_types"] = list(set(error_types))

        # Extract technical errors for context
        technical_patterns = [
            "RuntimeError", "ConnectionError", "TimeoutError", "ValueError",
            "KeyError", "FileNotFoundError", "PermissionError", "ConfigurationError"
        ]
        context["technical_errors"] = [err for err in technical_patterns if err.lower() in indicator_text]

        return context

    def _generate_suggestions(self, error_indicators: List[str], context: Dict[str, Any]) -> List[str]:
        """Generate helpful suggestions for resolving errors."""
        suggestions = []

        # Always include basic suggestions
        suggestions.append("Review the error details and identify the root cause")
        suggestions.append("Check system configuration and dependencies")

        # Add specific suggestions based on context
        if context.get("error_types"):
            error_types = context["error_types"]
            if "ConnectionError" in error_types or "TimeoutError" in error_types:
                suggestions.append("Verify network connectivity and service availability")
            if "PermissionError" in error_types:
                suggestions.append("Check file and directory permissions")
            if "ConfigurationError" in error_types:
                suggestions.append("Review application configuration and environment variables")
            if "ValueError" in error_types or "KeyError" in error_types:
                suggestions.append("Validate input parameters and data structure")

        # Suggestions based on stuck indicators
        if context.get("stuck_indicators"):
            suggestions.append("Provide additional clarification or requirements")
            suggestions.append("Consider breaking down the task into smaller steps")

        # Suggestions based on error patterns
        indicator_text = " ".join(error_indicators).lower()
        if "api" in indicator_text:
            suggestions.append("Check API endpoint availability and authentication")
        if "database" in indicator_text:
            suggestions.append("Verify database connection and credentials")
        if "dependency" in indicator_text:
            suggestions.append("Install missing dependencies and check versions")
        if "authentication" in indicator_text:
            suggestions.append("Verify authentication credentials and permissions")

        # Add investigation suggestion
        suggestions.append("Debug the issue step by step to isolate the problem")

        return suggestions[:6]  # Limit to 6 suggestions to avoid overwhelming

    def _create_no_blocker_result(self) -> BlockerDetails:
        """Create a result indicating no errors were detected."""
        return BlockerDetails(
            blocker_type=BlockerType.NONE,
            message="No errors or stuck states detected in agent response"
        )