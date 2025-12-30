# ABOUTME: AmbiguityDetector implementation - detects agent requests for clarification
# ABOUTME: Concrete implementation of BlockerDetector interface for ambiguity detection

"""AmbiguityDetector - Detects agent requests for clarification in agent responses.

This module provides a concrete implementation of the BlockerDetector interface
that specifically looks for ambiguity patterns and clarification requests in agent
responses and returns AMBIGUITY blocker type with detailed information.
"""

import re
from typing import List, Dict, Any

from .blocker_detector import BlockerDetector, BlockerDetails, BlockerType


class AmbiguityDetector(BlockerDetector):
    """Detects ambiguity and clarification requests in agent responses.

    This detector analyzes agent responses for various ambiguity patterns including:
    - Direct clarification requests ("Could you clarify...", "I need clarification...")
    - Question-based ambiguity ("Should I use...", "Which approach...")
    - Uncertainty expressions ("I'm not sure...", "I'm uncertain...")
    - Requirement understanding issues ("The requirements are unclear...")
    - Assumption validation requests ("I'm assuming...", "Should I assume...")

    When ambiguity is detected, it extracts relevant details and provides
    helpful suggestions for resolving the unclear requirements.
    """

    def __init__(self):
        """Initialize the AmbiguityDetector with compiled patterns for efficiency."""
        # Compile regex patterns for better performance
        self._ambiguity_patterns = [
            # Direct clarification requests
            re.compile(r"(could\s+you|can\s+you|please)\s+(clarify|explain|specify|provide)", re.IGNORECASE),
            re.compile(r"(i\s+)?need\s+(clarification|clarification\s+on|more\s+information|more\s+details)", re.IGNORECASE),
            re.compile(r"(could\s+you|can\s+you)\s+provide\s+(more\s+)?(details|information)", re.IGNORECASE),
            re.compile(r"please\s+(clarify|specify|explain|provide\s+details)", re.IGNORECASE),

            # Question-based ambiguity patterns
            re.compile(r"should\s+i\s+(use|implement|create|add|apply)", re.IGNORECASE),
            re.compile(r"which\s+(approach|method|library|database|format|way|authentication|libraries)", re.IGNORECASE),
            re.compile(r"what\s+(exactly\s+|precisely\s+|really\s+)?(should|would\s+be|format|method|approach|database|validation|permissions)", re.IGNORECASE),
            re.compile(r"how\s+should\s+i\s+(handle|implement|structure|organize)", re.IGNORECASE),
            re.compile(r"should\s+this\s+(\w+\s+)?(be|use|implement)", re.IGNORECASE),

            # Uncertainty and options patterns
            re.compile(r"(i\'?m\s+)?(not\s+sure|not\s+certain|uncertain|unsure)\s+(which|about|how|what|if|whether)", re.IGNORECASE),
            re.compile(r"there\s+are\s+(several|multiple|many)\s+(ways|options|approaches)", re.IGNORECASE),
            re.compile(r"(i\s+have\s+)?doubts\s+about", re.IGNORECASE),
            re.compile(r"(i\'?m\s+)?hesitant\s+about", re.IGNORECASE),
            re.compile(r"(not\s+clear|unclear)\s+(on|about|whether)", re.IGNORECASE),

            # Requirement understanding issues
            re.compile(r"(i\s+)?(don\'t\s+understand|don\'t\s+fully\s+grasp)", re.IGNORECASE),
            re.compile(r"(the\s+)?(requirements|specifications|acceptance\s+criteria|requirements?)\s+(are\s+)?(not\s+clear|unclear|ambiguous|vague|incomplete|seem\s+ambiguous|seem\s+vague)", re.IGNORECASE),
            re.compile(r"(having\s+trouble|difficulty)\s+understanding", re.IGNORECASE),
            re.compile(r"(i\'?m\s+)?confused\s+about\s+(what|how|the)", re.IGNORECASE),
            re.compile(r"(i\s+need\s+a\s+better|need\s+better)\s+understanding", re.IGNORECASE),
            re.compile(r"(doesn\'t\s+provide\s+enough|are\s+incomplete|incomplete|missing)\s+(detail|information)", re.IGNORECASE),

            # Assumption validation patterns
            re.compile(r"(i\'?m\s+)?assuming.*?(is\s+that\s+correct|correct|right)", re.IGNORECASE),
            re.compile(r"should\s+i\s+assume", re.IGNORECASE),
            re.compile(r"my\s+(assumption|understanding)\s+is", re.IGNORECASE),
            re.compile(r"(i\s+presume|i\s+assume|presuming|assuming)", re.IGNORECASE),
            re.compile(r"working\s+under\s+the\s+assumption", re.IGNORECASE),
            re.compile(r"(confirm|is\s+that\s+accurate|is\s+that\s+right)", re.IGNORECASE),

            # Request for guidance
            re.compile(r"(could\s+you\s+provide|provide)\s+(guidance|direction)", re.IGNORECASE),
            re.compile(r"(i\s+need|need)\s+(guidance|direction|input)", re.IGNORECASE),
            re.compile(r"(which\s+would\s+you|what\s+do\s+you)\s+(prefer|recommend|suggest)", re.IGNORECASE),
        ]

        # Patterns that should NOT be considered ambiguity (to avoid false positives)
        self._exclusion_patterns = [
            re.compile(r"(user|users|customer)\s+(can|could|should)\s+clarify", re.IGNORECASE),
            re.compile(r"(this|that|it)\s+(clarifies|helps\s+clarify)", re.IGNORECASE),
            re.compile(r"(clarify|clarifying)\s+(the\s+)?(code|implementation|logic)", re.IGNORECASE),
            re.compile(r"let\s+me\s+clarify", re.IGNORECASE),
            re.compile(r"(error\s+message|message)\s+(should|will)\s+clarify", re.IGNORECASE),
            re.compile(r"(need\s+to|should)\s+(clarify|explain)\s+(with|using|in)", re.IGNORECASE),
            re.compile(r"should\s+i\s+continue", re.IGNORECASE),  # Simple procedural question
            re.compile(r"ask\s+the\s+(database|api|service)", re.IGNORECASE),  # Technical "ask"
        ]

    def detect_blocker(self, agent_response: str) -> BlockerDetails:
        """Analyze agent response for ambiguity and clarification requests.

        Args:
            agent_response: The full response text from an agent

        Returns:
            BlockerDetails with AMBIGUITY type if ambiguity is detected,
            otherwise returns BlockerType.NONE
        """
        if not agent_response or not agent_response.strip():
            return self._create_no_blocker_result()

        # Check for exclusion patterns first to avoid false positives
        if self._has_exclusion_patterns(agent_response):
            return self._create_no_blocker_result()

        # Look for ambiguity indicators
        ambiguity_indicators = self._extract_ambiguity_indicators(agent_response)

        if not ambiguity_indicators:
            return self._create_no_blocker_result()

        # Extract additional context and create suggestions
        context = self._extract_context(agent_response, ambiguity_indicators)
        suggestions = self._generate_suggestions(ambiguity_indicators, context)

        return BlockerDetails(
            blocker_type=BlockerType.AMBIGUITY,
            message="Ambiguity detected in agent response - clarification needed",
            context=context,
            suggestions=suggestions
        )

    def _has_exclusion_patterns(self, text: str) -> bool:
        """Check if text matches exclusion patterns that should not be flagged."""
        return any(pattern.search(text) for pattern in self._exclusion_patterns)

    def _extract_ambiguity_indicators(self, text: str) -> List[str]:
        """Extract specific ambiguity indicators from the text."""
        indicators = []

        for pattern in self._ambiguity_patterns:
            matches = pattern.findall(text)
            if matches:
                # Add the pattern description and matches
                indicators.extend(matches if isinstance(matches[0], str) else [str(m) for m in matches])

        # Also look for specific ambiguity lines
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            for pattern in self._ambiguity_patterns:
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

    def _extract_context(self, text: str, ambiguity_indicators: List[str]) -> Dict[str, Any]:
        """Extract additional context about the ambiguity."""
        context = {
            "ambiguity_indicators": ambiguity_indicators,
            "response_length": len(text),
            "question_count": 0,
            "clarification_requests": [],
            "uncertainty_expressions": [],
            "assumption_validations": []
        }

        # Count questions (lines ending with ?)
        question_lines = [line.strip() for line in text.split('\n') if line.strip().endswith('?')]
        context["question_count"] = len(question_lines)

        # Categorize ambiguity types
        indicator_text = " ".join(ambiguity_indicators).lower()

        # Extract clarification request patterns
        clarification_keywords = ["clarify", "clarification", "explain", "provide details", "more information"]
        context["clarification_requests"] = [kw for kw in clarification_keywords if kw in indicator_text]

        # Extract uncertainty expressions
        uncertainty_keywords = ["not sure", "uncertain", "unsure", "doubts", "hesitant", "unclear"]
        context["uncertainty_expressions"] = [kw for kw in uncertainty_keywords if kw in indicator_text]

        # Extract assumption validation patterns
        assumption_keywords = ["assuming", "assumption", "presume", "should i assume", "correct", "right"]
        context["assumption_validations"] = [kw for kw in assumption_keywords if kw in indicator_text]

        return context

    def _generate_suggestions(self, ambiguity_indicators: List[str], context: Dict[str, Any]) -> List[str]:
        """Generate helpful suggestions for resolving ambiguity."""
        suggestions = []

        # Always include basic suggestions
        suggestions.append("Provide clear and detailed requirements for the unclear aspects")
        suggestions.append("Specify the preferred approach or implementation method")

        # Add specific suggestions based on context
        if context.get("clarification_requests"):
            suggestions.append("Answer the specific clarification questions raised by the agent")

        if context.get("uncertainty_expressions"):
            suggestions.append("Make a decision on the uncertain implementation choices")

        if context.get("assumption_validations"):
            suggestions.append("Confirm or correct the agent's assumptions about requirements")

        # Suggestions based on ambiguity patterns
        indicator_text = " ".join(ambiguity_indicators).lower()

        if "which" in indicator_text or "should i use" in indicator_text:
            suggestions.append("Choose specific technologies, libraries, or approaches to use")

        if "database" in indicator_text:
            suggestions.append("Clarify database schema, relationships, and data requirements")

        if "api" in indicator_text or "endpoint" in indicator_text:
            suggestions.append("Specify API design, endpoints, and data formats")

        if "user" in indicator_text or "interface" in indicator_text:
            suggestions.append("Provide user interface requirements and user experience details")

        if "authentication" in indicator_text or "permission" in indicator_text:
            suggestions.append("Define authentication methods and permission requirements")

        if "validation" in indicator_text or "error" in indicator_text:
            suggestions.append("Specify validation rules and error handling requirements")

        if context.get("question_count", 0) > 2:
            suggestions.append("Consider breaking down complex requirements into smaller, clearer tasks")

        # Add general guidance suggestion
        suggestions.append("Provide examples or mockups to illustrate expected behavior")

        return suggestions[:6]  # Limit to 6 suggestions to avoid overwhelming

    def _create_no_blocker_result(self) -> BlockerDetails:
        """Create a result indicating no ambiguity was detected."""
        return BlockerDetails(
            blocker_type=BlockerType.NONE,
            message="No ambiguity detected in agent response"
        )