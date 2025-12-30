# ABOUTME: BlockerDetector interface and supporting types for detecting workflow blockers
# ABOUTME: Provides abstract interface for detecting different types of blockers in agent responses

"""BlockerDetector interface and supporting types.

This module provides the abstract interface for detecting workflow blockers
in agent responses, along with supporting enums and data classes for
representing different types of blockers and their details.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class BlockerType(str, Enum):
    """Enum representing the different types of blockers that can be detected.

    Attributes:
        TEST_FAILURE: Agent encountered test failures
        ERROR: Agent reported being stuck or encountering errors
        AMBIGUITY: Agent needs clarification on requirements
        NONE: No blockers detected
    """

    TEST_FAILURE = 'test_failure'
    ERROR = 'error'
    AMBIGUITY = 'ambiguity'
    NONE = 'none'


@dataclass
class BlockerDetails:
    """Details about a detected blocker.

    Attributes:
        blocker_type: Type of blocker that was detected
        message: Human-readable description of the blocker
        context: Optional additional context about the blocker (e.g., test names, error details)
        suggestions: Optional list of suggested actions to resolve the blocker
    """

    blocker_type: BlockerType
    message: str
    context: Optional[Dict[str, Any]] = None
    suggestions: List[str] = field(default_factory=list)


class BlockerDetector(ABC):
    """Abstract interface for detecting blockers in agent responses.

    Implementations of this interface should analyze agent responses
    and detect specific types of blockers (test failures, errors, ambiguity).
    Different detector implementations can focus on specific blocker types
    or use different detection strategies.
    """

    @abstractmethod
    def detect_blocker(self, agent_response: str) -> BlockerDetails:
        """Analyze an agent response and detect any blockers.

        Args:
            agent_response: The full response text from an agent

        Returns:
            BlockerDetails containing the detected blocker type and details,
            or BlockerType.NONE if no blockers are detected

        Example:
            >>> detector = SomeBlockerDetector()
            >>> result = detector.detect_blocker("Test failed: assertion error")
            >>> result.blocker_type
            BlockerType.TEST_FAILURE
            >>> result.message
            "Test failure detected in agent response"
        """
        pass