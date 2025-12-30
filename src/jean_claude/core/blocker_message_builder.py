# ABOUTME: BlockerMessageBuilder for constructing Message objects from blocker details
# ABOUTME: Builds messages with appropriate priority and awaiting_response=True for workflow blockers

"""BlockerMessageBuilder for creating messages from detected blockers.

This module provides the BlockerMessageBuilder class that constructs Message objects
from BlockerDetails with appropriate priority levels and formatting for inter-agent
communication when workflow blockers are detected.
"""

from jean_claude.core.blocker_detector import BlockerDetails, BlockerType
from jean_claude.core.message import Message, MessagePriority


class BlockerMessageBuilder:
    """Builder for creating Message objects from blocker details.

    The BlockerMessageBuilder constructs Message objects from BlockerDetails
    with appropriate priority, subject lines, and body formatting for
    communication about workflow blockers between agents.

    All messages created for blockers (except NONE type) are marked as:
    - priority: URGENT
    - awaiting_response: True
    - type: "blocker_detected"
    """

    def build_message(
        self,
        blocker_details: BlockerDetails,
        from_agent: str,
        to_agent: str
    ) -> Message:
        """Build a Message object from blocker details.

        Args:
            blocker_details: The detected blocker information
            from_agent: Identifier of the agent sending the message
            to_agent: Identifier of the agent receiving the message

        Returns:
            Message object with appropriate priority and formatting

        Raises:
            ValueError: If blocker_details is None, agent names are empty,
                       or blocker_type is NONE (no message needed)

        Example:
            >>> builder = BlockerMessageBuilder()
            >>> blocker = BlockerDetails(
            ...     blocker_type=BlockerType.TEST_FAILURE,
            ...     message="Tests failed",
            ...     suggestions=["Fix tests"]
            ... )
            >>> msg = builder.build_message(blocker, "agent-1", "coordinator")
            >>> msg.priority
            MessagePriority.URGENT
            >>> msg.awaiting_response
            True
        """
        # Validate inputs
        if blocker_details is None:
            raise ValueError("blocker_details cannot be None")

        if not from_agent or not from_agent.strip():
            raise ValueError("from_agent cannot be empty")

        if not to_agent or not to_agent.strip():
            raise ValueError("to_agent cannot be empty")

        # Cannot build message for NONE blocker type
        if blocker_details.blocker_type == BlockerType.NONE:
            raise ValueError("Cannot build message for NONE blocker type")

        # Generate subject based on blocker type
        subject = self._generate_subject(blocker_details.blocker_type)

        # Generate formatted body
        body = self._generate_body(blocker_details)

        # Create message with urgent priority and awaiting_response=True
        return Message(
            from_agent=from_agent,
            to_agent=to_agent,
            type="blocker_detected",
            subject=subject,
            body=body,
            priority=MessagePriority.URGENT,
            awaiting_response=True
        )

    def _generate_subject(self, blocker_type: BlockerType) -> str:
        """Generate appropriate subject line based on blocker type.

        Args:
            blocker_type: The type of blocker detected

        Returns:
            Formatted subject line string
        """
        subject_map = {
            BlockerType.TEST_FAILURE: "Test Failure Detected - Requires Attention",
            BlockerType.ERROR: "Error Encountered - Need Assistance",
            BlockerType.AMBIGUITY: "Clarification Needed - Ambiguous Requirements"
        }

        return subject_map.get(blocker_type, f"Blocker Detected - {blocker_type.value}")

    def _generate_body(self, blocker_details: BlockerDetails) -> str:
        """Generate formatted message body from blocker details.

        Args:
            blocker_details: The blocker information to format

        Returns:
            Formatted message body string with sections for message, context, and suggestions
        """
        body_parts = [f"Workflow Blocker Detected\n{'=' * 25}\n"]

        # Add main message
        body_parts.append(f"Issue: {blocker_details.message}\n")

        # Add context if available
        if blocker_details.context:
            body_parts.append("Additional Context:")
            for key, value in blocker_details.context.items():
                body_parts.append(f"  - {key}: {value}")
            body_parts.append("")  # Add blank line

        # Add suggestions if available
        if blocker_details.suggestions:
            body_parts.append("Suggested Actions:")
            for suggestion in blocker_details.suggestions:
                body_parts.append(f"  • {suggestion}")
            body_parts.append("")  # Add blank line

        # Add footer
        body_parts.append("Please review and provide guidance on how to proceed.")

        return "\n".join(body_parts)