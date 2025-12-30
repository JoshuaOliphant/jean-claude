# ABOUTME: ResponseParser implementation - extracts user decisions from OUTBOX messages
# ABOUTME: Parses user response content for skip/fix/abort/continue decisions

"""ResponseParser - Extracts user decisions from OUTBOX message content.

This module provides the ResponseParser class that analyzes user response
messages and extracts clear decisions about how to proceed with workflow
blockers (skip/fix/abort/continue).
"""

import re
from enum import Enum
from typing import Dict, Any, List, Optional

from pydantic import BaseModel


class DecisionType(str, Enum):
    """Enum representing the types of user decisions.

    Attributes:
        SKIP: Skip the current blocker and continue
        FIX: Fix the issue before continuing
        ABORT: Abort the entire workflow
        CONTINUE: Continue with current approach
        UNCLEAR: Decision is ambiguous or unclear
    """

    SKIP = "skip"
    FIX = "fix"
    ABORT = "abort"
    CONTINUE = "continue"
    UNCLEAR = "unclear"


class UserDecision(BaseModel):
    """Model representing a parsed user decision.

    Attributes:
        decision_type: The type of decision made by the user
        message: Description of the decision
        context: Additional context about the decision and parsing
    """

    decision_type: DecisionType
    message: str
    context: Dict[str, Any] = {}


class ResponseParser:
    """Extracts user decisions from OUTBOX message content.

    This parser analyzes user response messages and extracts clear decisions
    about how to proceed with workflow blockers. It looks for keywords and
    patterns to determine if the user wants to skip, fix, abort, or continue
    with the current workflow.

    Decision Priority (when multiple keywords present):
    1. ABORT - Most decisive, stops everything
    2. FIX - Clear action needed before proceeding
    3. CONTINUE - Proceed with current approach
    4. SKIP - Bypass current issue
    5. UNCLEAR - No clear decision found
    """

    def __init__(self):
        """Initialize the ResponseParser with compiled patterns for efficiency."""
        # Compile regex patterns for better performance
        self._decision_patterns = {
            DecisionType.SKIP: [
                re.compile(r'\bskip\b.*(?:test|error|issue|blocker|failure)', re.IGNORECASE),
                re.compile(r'\bskip\b.*(?:this|it|that)', re.IGNORECASE),
                re.compile(r'let\'?s\s+skip', re.IGNORECASE),
                re.compile(r'please\s+skip', re.IGNORECASE),
                re.compile(r'\bskip\b.*(?:for\s+now|until|later)', re.IGNORECASE),
                re.compile(r'\bskip\b', re.IGNORECASE),
            ],

            DecisionType.FIX: [
                re.compile(r'\bfix\b.*(?:this|the|it|that)', re.IGNORECASE),
                re.compile(r'please\s+fix', re.IGNORECASE),
                re.compile(r'let\'?s\s+fix', re.IGNORECASE),
                re.compile(r'need.*to\s+fix', re.IGNORECASE),
                re.compile(r'i\s+want.*fix', re.IGNORECASE),
                re.compile(r'go\s+ahead\s+and\s+fix', re.IGNORECASE),
                re.compile(r'\bfix\b.*(?:before|first|immediately)', re.IGNORECASE),
                re.compile(r'\bfix\b', re.IGNORECASE),
            ],

            DecisionType.ABORT: [
                re.compile(r'\babort\b.*(?:this|the|workflow|task|process)', re.IGNORECASE),
                re.compile(r'please\s+abort', re.IGNORECASE),
                re.compile(r'let\'?s\s+abort', re.IGNORECASE),
                re.compile(r'i\s+want.*abort', re.IGNORECASE),
                re.compile(r'stop\s+and\s+abort', re.IGNORECASE),
                re.compile(r'\babort\b', re.IGNORECASE),
            ],

            DecisionType.CONTINUE: [
                re.compile(r'\bcontinue\b.*(?:with|working|implementing|development)', re.IGNORECASE),
                re.compile(r'please\s+continue', re.IGNORECASE),
                re.compile(r'let\'?s\s+continue', re.IGNORECASE),
                re.compile(r'go\s+ahead\s+and\s+continue', re.IGNORECASE),
                re.compile(r'keep\s+going.*continue', re.IGNORECASE),
                re.compile(r'i\s+want.*continue', re.IGNORECASE),
                re.compile(r'\bcontinue\b.*(?:despite|ignore)', re.IGNORECASE),
                re.compile(r'\bcontinue\b', re.IGNORECASE),
            ]
        }

        # Confidence indicators for decision strength
        self._high_confidence_patterns = [
            re.compile(r'(please|immediately|definitely|absolutely)', re.IGNORECASE),
            re.compile(r'(need to|must|should|have to)', re.IGNORECASE),
            re.compile(r'^(skip|fix|abort|continue)\b', re.IGNORECASE),  # Starts with decision word
        ]

        self._low_confidence_patterns = [
            re.compile(r'(maybe|perhaps|possibly|might|could|i think)', re.IGNORECASE),
            re.compile(r'(not sure|uncertain|unclear)', re.IGNORECASE),
        ]

    def parse_response(self, response_content: str) -> UserDecision:
        """Parse user response content to extract decision.

        Args:
            response_content: The full response text from user

        Returns:
            UserDecision with extracted decision type, message, and context
        """
        if not response_content or not response_content.strip():
            return self._create_unclear_decision("Empty or whitespace-only response")

        content = response_content.strip()

        # Extract all decision matches with their types and scores
        decision_matches = self._extract_decision_matches(content)

        if not decision_matches:
            return self._create_unclear_decision(content)

        # Determine the best decision based on priority and confidence
        best_decision = self._determine_best_decision(decision_matches)

        # Extract additional context
        context = self._extract_context(content, decision_matches, best_decision)

        # Generate appropriate message
        message = self._generate_decision_message(best_decision, context)

        return UserDecision(
            decision_type=best_decision,
            message=message,
            context=context
        )

    def _extract_decision_matches(self, content: str) -> List[Dict[str, Any]]:
        """Extract all decision pattern matches from content."""
        matches = []

        for decision_type, patterns in self._decision_patterns.items():
            for pattern in patterns:
                if pattern.search(content):
                    # Score this match based on pattern specificity
                    score = self._calculate_pattern_score(pattern, content)
                    matches.append({
                        'decision_type': decision_type,
                        'pattern': pattern.pattern,
                        'score': score
                    })
                    break  # Take first match for each decision type

        return matches

    def _calculate_pattern_score(self, pattern: re.Pattern, content: str) -> float:
        """Calculate confidence score for a pattern match."""
        base_score = 1.0

        # Boost score for high confidence indicators
        for conf_pattern in self._high_confidence_patterns:
            if conf_pattern.search(content):
                base_score += 0.5

        # Reduce score for low confidence indicators
        for conf_pattern in self._low_confidence_patterns:
            if conf_pattern.search(content):
                base_score -= 0.3

        # Boost score for more specific patterns (more words in pattern)
        pattern_complexity = len(pattern.pattern.split())
        base_score += pattern_complexity * 0.1

        return max(0.1, base_score)  # Minimum score of 0.1

    def _determine_best_decision(self, decision_matches: List[Dict[str, Any]]) -> DecisionType:
        """Determine the best decision based on priority and confidence."""
        if not decision_matches:
            return DecisionType.UNCLEAR

        # Priority order (higher numbers = higher priority)
        priority_order = {
            DecisionType.ABORT: 4,
            DecisionType.FIX: 3,
            DecisionType.CONTINUE: 2,
            DecisionType.SKIP: 1,
        }

        # Sort by priority first, then by confidence score
        sorted_matches = sorted(
            decision_matches,
            key=lambda x: (priority_order.get(x['decision_type'], 0), x['score']),
            reverse=True
        )

        return sorted_matches[0]['decision_type']

    def _extract_context(self, content: str, matches: List[Dict[str, Any]],
                        decision: DecisionType) -> Dict[str, Any]:
        """Extract additional context about the decision and parsing."""
        context = {
            "original_content": content,
            "content_length": len(content),
            "extracted_keywords": [],
            "decision_confidence": "medium",
            "all_detected_decisions": [m['decision_type'].value for m in matches]
        }

        # Extract relevant keywords based on decision type
        if decision == DecisionType.FIX:
            fix_keywords = re.findall(r'\b(?:fix|repair|solve|correct|update|change|modify)\b',
                                    content, re.IGNORECASE)
            context["extracted_keywords"].extend(fix_keywords)

        elif decision == DecisionType.SKIP:
            skip_keywords = re.findall(r'\b(?:skip|ignore|bypass|postpone|defer|later)\b',
                                     content, re.IGNORECASE)
            context["extracted_keywords"].extend(skip_keywords)

        elif decision == DecisionType.ABORT:
            abort_keywords = re.findall(r'\b(?:abort|stop|cancel|terminate|end|quit)\b',
                                      content, re.IGNORECASE)
            context["extracted_keywords"].extend(abort_keywords)

        elif decision == DecisionType.CONTINUE:
            continue_keywords = re.findall(r'\b(?:continue|proceed|keep|go|move|forward)\b',
                                         content, re.IGNORECASE)
            context["extracted_keywords"].extend(continue_keywords)

        # Determine confidence level
        context["decision_confidence"] = self._assess_confidence(content, matches)

        return context

    def _assess_confidence(self, content: str, matches: List[Dict[str, Any]]) -> str:
        """Assess confidence level in the decision."""
        # Check for high confidence indicators
        has_high_confidence = any(
            pattern.search(content) for pattern in self._high_confidence_patterns
        )

        # Check for low confidence indicators
        has_low_confidence = any(
            pattern.search(content) for pattern in self._low_confidence_patterns
        )

        # Multiple conflicting decisions lower confidence
        unique_decisions = len(set(m['decision_type'] for m in matches))

        # Low confidence indicators override high confidence ones
        if has_low_confidence or unique_decisions > 2:
            return "low"
        elif has_high_confidence and unique_decisions == 1:
            return "high"
        else:
            return "medium"

    def _generate_decision_message(self, decision: DecisionType, context: Dict[str, Any]) -> str:
        """Generate appropriate message for the decision."""
        confidence = context.get("decision_confidence", "medium")

        base_messages = {
            DecisionType.SKIP: "User decided to skip this blocker",
            DecisionType.FIX: "User wants to fix this issue",
            DecisionType.ABORT: "User wants to abort the workflow",
            DecisionType.CONTINUE: "User wants to continue with current approach",
            DecisionType.UNCLEAR: "User decision is unclear or ambiguous"
        }

        message = base_messages[decision]

        if confidence == "high":
            message += " (high confidence)"
        elif confidence == "low":
            message += " (low confidence)"

        return message

    def _create_unclear_decision(self, content: str) -> UserDecision:
        """Create a UserDecision for unclear/ambiguous responses."""
        return UserDecision(
            decision_type=DecisionType.UNCLEAR,
            message="User decision is unclear or ambiguous",
            context={
                "original_content": content,
                "decision_confidence": "low",
                "extracted_keywords": [],
                "all_detected_decisions": []
            }
        )