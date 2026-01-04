# ABOUTME: MailboxProjectionBuilder class for agent messaging projections
# ABOUTME: Extends ProjectionBuilder to provide inbox/outbox functionality with basic initialization

"""MailboxProjectionBuilder for agent messaging projections.

This module provides the MailboxProjectionBuilder class which extends the abstract
ProjectionBuilder to create projections specifically for agent messaging functionality.
It maintains inbox, outbox, and conversation history state for tracking messages
between agents.

The MailboxProjectionBuilder processes agent messaging events to build read models
that support mailbox views, message tracking, and conversation history.

Key Features:
- Maintains inbox for incoming messages
- Maintains outbox for outgoing messages
- Tracks conversation history
- Provides basic state initialization
"""

from typing import Dict, Any

from .projection_builder import ProjectionBuilder
from .event_models import Event


class MailboxProjectionBuilder(ProjectionBuilder):
    """Projection builder for agent mailbox functionality.

    This class extends ProjectionBuilder to provide specialized handling for
    agent messaging events. It creates and maintains projections that support
    inbox/outbox views and conversation tracking.

    State Structure:
        The projection state maintained by this builder contains:
        - inbox: List of incoming messages for the agent
        - outbox: List of outgoing messages from the agent
        - conversation_history: List of completed message conversations

    Event Handling:
        Currently provides basic implementations that return the current state.
        Future features will implement full event processing logic for:
        - Agent message sent events
        - Agent message acknowledged events
        - Agent message completed events
        - Agent note events

    Example:
        >>> builder = MailboxProjectionBuilder()
        >>> initial_state = builder.get_initial_state()
        >>> print(initial_state)
        {'inbox': [], 'outbox': [], 'conversation_history': []}
    """

    def get_initial_state(self) -> Dict[str, Any]:
        """Return the initial state for a mailbox projection.

        Returns:
            Dict containing empty arrays for inbox, outbox, and conversation_history

        Example:
            >>> builder = MailboxProjectionBuilder()
            >>> state = builder.get_initial_state()
            >>> state
            {'inbox': [], 'outbox': [], 'conversation_history': []}
        """
        return {
            'inbox': [],
            'outbox': [],
            'conversation_history': []
        }

    # ProjectionBuilder abstract method implementations
    # These provide basic implementations that maintain current state
    # Future features will add specific logic for mailbox functionality

    def apply_workflow_started(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorkflowStarted event. Basic implementation maintains current state."""
        return state

    def apply_workflow_completed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorkflowCompleted event. Basic implementation maintains current state."""
        return state

    def apply_workflow_failed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorkflowFailed event. Basic implementation maintains current state."""
        return state

    def apply_worktree_created(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorktreeCreated event. Basic implementation maintains current state."""
        return state

    def apply_worktree_active(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorktreeActive event. Basic implementation maintains current state."""
        return state

    def apply_worktree_merged(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorktreeMerged event. Basic implementation maintains current state."""
        return state

    def apply_worktree_deleted(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply WorktreeDeleted event. Basic implementation maintains current state."""
        return state

    def apply_feature_planned(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply FeaturePlanned event. Basic implementation maintains current state."""
        return state

    def apply_feature_started(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply FeatureStarted event. Basic implementation maintains current state."""
        return state

    def apply_feature_completed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply FeatureCompleted event. Basic implementation maintains current state."""
        return state

    def apply_feature_failed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply FeatureFailed event. Basic implementation maintains current state."""
        return state

    def apply_phase_changed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply PhaseChanged event. Basic implementation maintains current state."""
        return state

    def apply_tests_started(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply TestsStarted event. Basic implementation maintains current state."""
        return state

    def apply_tests_passed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply TestsPassed event. Basic implementation maintains current state."""
        return state

    def apply_tests_failed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply TestsFailed event. Basic implementation maintains current state."""
        return state

    def apply_commit_created(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply CommitCreated event. Basic implementation maintains current state."""
        return state

    def apply_commit_failed(self, state: Dict[str, Any], event: Event) -> Dict[str, Any]:
        """Apply CommitFailed event. Basic implementation maintains current state."""
        return state

    # Agent message event handlers

    def apply_agent_message_sent(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.message.sent event to update projection state.

        Processes agent.message.sent events by:
        - Adding message to inbox if current_agent_id matches to_agent (recipient)
        - Adding message to outbox if current_agent_id matches from_agent (sender)
        - Ignoring message if current_agent_id doesn't match either agent

        Args:
            event_data: Event data containing:
                - event_id: ID of the event that created this message
                - message: Message object with from_agent, to_agent, subject, body, etc.
                - sent_at: Timestamp when message was sent
                - current_agent_id: ID of the agent whose projection this is
            current_state: Current projection state with inbox, outbox, conversation_history

        Returns:
            Updated projection state with new message added to appropriate list
        """
        # Import here to avoid circular imports
        from .mailbox_message_models import InboxMessage, OutboxMessage

        # Validate event data has required fields
        if not all(key in event_data for key in ['event_id', 'message', 'sent_at', 'current_agent_id']):
            # Return unchanged state if required data is missing
            return current_state

        event_id = event_data['event_id']
        message = event_data['message']
        sent_at = event_data['sent_at']
        current_agent_id = event_data['current_agent_id']

        # Create a copy of current state to avoid mutating the original
        new_state = {
            'inbox': current_state['inbox'][:],
            'outbox': current_state['outbox'][:],
            'conversation_history': current_state['conversation_history'][:]
        }

        # Determine if this message involves the current agent
        if current_agent_id == message.to_agent:
            # Current agent is the recipient - add to inbox
            inbox_message = InboxMessage.from_message(
                message=message,
                event_id=event_id,
                received_at=sent_at
            )
            new_state['inbox'].append(inbox_message)

        elif current_agent_id == message.from_agent:
            # Current agent is the sender - add to outbox
            outbox_message = OutboxMessage.from_message(
                message=message,
                event_id=event_id,
                sent_at=sent_at
            )
            new_state['outbox'].append(outbox_message)

        # If current_agent_id matches neither from_agent nor to_agent,
        # this message doesn't involve the current agent, so ignore it

        return new_state

    def apply_agent_message_acknowledged(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.message.acknowledged event to update projection state.

        Processes agent.message.acknowledged events by:
        - Finding inbox messages where event_id matches the correlation_id
        - Verifying the acknowledging agent is the recipient (from_agent matches current_agent_id)
        - Marking the matching inbox message as acknowledged with the provided timestamp
        - Preserving already-acknowledged messages without changing their timestamp

        Args:
            event_data: Event data containing:
                - correlation_id: ID of the original event that created the message to acknowledge
                - from_agent: ID of the agent acknowledging the message (must be recipient)
                - acknowledged_at: Timestamp when message was acknowledged
                - current_agent_id: ID of the agent whose projection this is

        Returns:
            Updated projection state with inbox messages marked as acknowledged where appropriate
        """
        # Validate event data has required fields
        required_fields = ['correlation_id', 'from_agent', 'acknowledged_at', 'current_agent_id']
        if not all(key in event_data for key in required_fields):
            # Return unchanged state if required data is missing
            return current_state

        correlation_id = event_data['correlation_id']
        from_agent = event_data['from_agent']
        acknowledged_at = event_data['acknowledged_at']
        current_agent_id = event_data['current_agent_id']

        # Only process acknowledgments for the current agent's projection
        if current_agent_id != from_agent:
            # This acknowledgment is not from the current agent, so ignore it
            return current_state

        # Import here to avoid circular imports
        from .mailbox_message_models import InboxMessage

        # Create a copy of current state to avoid mutating the original
        new_state = {
            'inbox': [],
            'outbox': current_state['outbox'][:],
            'conversation_history': current_state['conversation_history'][:]
        }

        # Process each inbox message
        for inbox_message in current_state['inbox']:
            # Check if this message matches the correlation_id and is for the current agent
            if (inbox_message.event_id == correlation_id and
                inbox_message.to_agent == current_agent_id):

                # Create a copy of the message to avoid mutating original
                acknowledged_message = InboxMessage(
                    event_id=inbox_message.event_id,
                    message_id=inbox_message.message_id,
                    from_agent=inbox_message.from_agent,
                    to_agent=inbox_message.to_agent,
                    subject=inbox_message.subject,
                    body=inbox_message.body,
                    priority=inbox_message.priority,
                    created_at=inbox_message.created_at,
                    received_at=inbox_message.received_at,
                    acknowledged=True,
                    acknowledged_at=acknowledged_at if not inbox_message.acknowledged else inbox_message.acknowledged_at
                )
                new_state['inbox'].append(acknowledged_message)
            else:
                # Message doesn't match or not for current agent, keep unchanged
                new_state['inbox'].append(inbox_message)

        return new_state

    def apply_agent_message_completed(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.message.completed event to update projection state.

        Args:
            event_data: Event data containing correlation_id, from_agent, result, success
            current_state: Current projection state

        Returns:
            Updated projection state

        Note:
            This is a basic implementation that returns the current state unchanged.
            Full implementation will be added in the apply-agent-message-completed feature.
        """
        # Basic implementation - full logic will be added in apply-agent-message-completed feature
        return current_state

    # Agent note event handlers

    def apply_agent_note_observation(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.observation event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Note:
            This is a basic implementation that returns the current state unchanged.
            Note handling is not part of the current mailbox feature set.
        """
        # Basic implementation - note handling not part of mailbox features
        return current_state

    def apply_agent_note_learning(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.learning event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Note:
            This is a basic implementation that returns the current state unchanged.
            Note handling is not part of the current mailbox feature set.
        """
        # Basic implementation - note handling not part of mailbox features
        return current_state

    def apply_agent_note_decision(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.decision event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Note:
            This is a basic implementation that returns the current state unchanged.
            Note handling is not part of the current mailbox feature set.
        """
        # Basic implementation - note handling not part of mailbox features
        return current_state

    def apply_agent_note_warning(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.warning event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Note:
            This is a basic implementation that returns the current state unchanged.
            Note handling is not part of the current mailbox feature set.
        """
        # Basic implementation - note handling not part of mailbox features
        return current_state

    def apply_agent_note_accomplishment(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.accomplishment event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Note:
            This is a basic implementation that returns the current state unchanged.
            Note handling is not part of the current mailbox feature set.
        """
        # Basic implementation - note handling not part of mailbox features
        return current_state

    def apply_agent_note_context(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.context event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Note:
            This is a basic implementation that returns the current state unchanged.
            Note handling is not part of the current mailbox feature set.
        """
        # Basic implementation - note handling not part of mailbox features
        return current_state

    def apply_agent_note_todo(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.todo event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Note:
            This is a basic implementation that returns the current state unchanged.
            Note handling is not part of the current mailbox feature set.
        """
        # Basic implementation - note handling not part of mailbox features
        return current_state

    def apply_agent_note_question(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.question event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Note:
            This is a basic implementation that returns the current state unchanged.
            Note handling is not part of the current mailbox feature set.
        """
        # Basic implementation - note handling not part of mailbox features
        return current_state

    def apply_agent_note_idea(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.idea event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Note:
            This is a basic implementation that returns the current state unchanged.
            Note handling is not part of the current mailbox feature set.
        """
        # Basic implementation - note handling not part of mailbox features
        return current_state

    def apply_agent_note_reflection(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.reflection event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Note:
            This is a basic implementation that returns the current state unchanged.
            Note handling is not part of the current mailbox feature set.
        """
        # Basic implementation - note handling not part of mailbox features
        return current_state