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

from datetime import datetime
from typing import Dict, Any, Optional

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
                    acknowledged_at=acknowledged_at if not inbox_message.acknowledged else inbox_message.acknowledged_at,
                    correlation_id=inbox_message.correlation_id
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

        Processes agent.message.completed events by:
        - Finding outbox messages where event_id matches the correlation_id
        - Verifying the completing agent is the sender (from_agent matches current_agent_id)
        - Removing the matching outbox message and adding it to conversation history
        - Preserving completed status and result information

        Args:
            event_data: Event data containing:
                - correlation_id: ID of the original event that created the message to complete
                - from_agent: ID of the agent completing the message (must be sender)
                - completed_at: Timestamp when message was completed
                - success: Whether the message was successfully processed
                - result: Description of the completion result
                - current_agent_id: ID of the agent whose projection this is

        Returns:
            Updated projection state with outbox messages completed and moved to conversation history
        """
        # Validate event data has required fields
        required_fields = ['correlation_id', 'from_agent', 'completed_at', 'success', 'current_agent_id']
        if not all(key in event_data for key in required_fields):
            # Return unchanged state if required data is missing
            return current_state

        correlation_id = event_data['correlation_id']
        from_agent = event_data['from_agent']
        completed_at = event_data['completed_at']
        success = event_data['success']
        result = event_data.get('result', '')  # Optional field
        current_agent_id = event_data['current_agent_id']

        # Only process completions for the current agent's projection
        if current_agent_id != from_agent:
            # This completion is not from the current agent, so ignore it
            return current_state

        # Import here to avoid circular imports
        from .mailbox_message_models import ConversationMessage, OutboxMessage

        # Create a copy of current state to avoid mutating the original
        new_state = {
            'inbox': current_state['inbox'][:],
            'outbox': [],
            'conversation_history': current_state['conversation_history'][:]
        }

        # Process each outbox message
        for outbox_message in current_state['outbox']:
            # Check if this message matches the correlation_id and is from the current agent
            if (outbox_message.event_id == correlation_id and
                outbox_message.from_agent == current_agent_id):

                # Create ConversationMessage from the completed outbox message
                # First mark the outbox message as completed
                completed_outbox_message = OutboxMessage(
                    event_id=outbox_message.event_id,
                    message_id=outbox_message.message_id,
                    from_agent=outbox_message.from_agent,
                    to_agent=outbox_message.to_agent,
                    subject=outbox_message.subject,
                    body=outbox_message.body,
                    priority=outbox_message.priority,
                    created_at=outbox_message.created_at,
                    sent_at=outbox_message.sent_at,
                    completed=True,
                    completed_at=completed_at,
                    success=success,
                    correlation_id=outbox_message.correlation_id
                )

                # Convert to conversation message (use outbox_message's correlation_id, not event's)
                conversation_message = ConversationMessage.from_outbox_message(
                    outbox_message=completed_outbox_message,
                    correlation_id=outbox_message.correlation_id or correlation_id
                )

                # Add to conversation history
                new_state['conversation_history'].append(conversation_message)

            else:
                # Message doesn't match or not from current agent, keep in outbox
                new_state['outbox'].append(outbox_message)

        return new_state

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

    # =============================================================================
    # Helper Methods for Inbox Filtering
    # =============================================================================

    def get_unread_inbox(self, current_state: Dict[str, Any]) -> list:
        """Get unread inbox messages filtered by acknowledged=False and sorted by priority.

        This helper method filters inbox messages to return only unacknowledged messages,
        sorted by priority in descending order (URGENT > HIGH > NORMAL > LOW).
        For messages with the same priority, they are sorted by received_at timestamp
        (oldest first) to maintain a stable sort order.

        Args:
            current_state: Current projection state containing inbox messages

        Returns:
            List of InboxMessage objects that are unacknowledged, sorted by priority
            and received_at timestamp. Returns empty list if no unread messages
            or if inbox is missing from state.

        Example:
            >>> state = {
            ...     'inbox': [urgent_unread, normal_read, high_unread],
            ...     'outbox': [],
            ...     'conversation_history': []
            ... }
            >>> unread = builder.get_unread_inbox(state)
            >>> # Returns [urgent_unread, high_unread] sorted by priority
        """
        # Import here to avoid circular imports
        from .message import MessagePriority

        # Handle missing or None inbox gracefully
        inbox_messages = current_state.get('inbox', []) or []

        # Filter for unacknowledged messages only
        unread_messages = [msg for msg in inbox_messages if not msg.acknowledged]

        # Define priority order for sorting (higher values = higher priority)
        priority_order = {
            MessagePriority.URGENT: 4,
            MessagePriority.HIGH: 3,
            MessagePriority.NORMAL: 2,
            MessagePriority.LOW: 1
        }

        # Sort by priority (descending) then by received_at (ascending for stable order)
        unread_messages.sort(
            key=lambda msg: (-priority_order.get(msg.priority, 0), msg.received_at)
        )

        return unread_messages

    # =============================================================================
    # Helper Methods for Outbox Filtering
    # =============================================================================

    def get_pending_outbox(self, current_state: Dict[str, Any]) -> list:
        """Get pending outbox messages filtered by completed=False and sorted by sent_at timestamp.

        This helper method filters outbox messages to return only uncompleted messages,
        sorted by sent_at timestamp in ascending order (oldest first). This provides
        a view of pending outbound messages that are still awaiting completion.

        Args:
            current_state: Current projection state containing outbox messages

        Returns:
            List of OutboxMessage objects that are not yet completed, sorted by sent_at
            timestamp (oldest first). Returns empty list if no pending messages
            or if outbox is missing from state.

        Example:
            >>> state = {
            ...     'inbox': [],
            ...     'outbox': [old_pending, new_pending, completed_msg],
            ...     'conversation_history': []
            ... }
            >>> pending = builder.get_pending_outbox(state)
            >>> # Returns [old_pending, new_pending] sorted by sent_at
        """
        # Handle missing outbox gracefully
        outbox_messages = current_state.get('outbox', [])

        # Filter for uncompleted messages only
        pending_messages = [msg for msg in outbox_messages if not msg.completed]

        # Sort by sent_at timestamp (ascending - oldest first)
        pending_messages.sort(key=lambda msg: msg.sent_at)

        return pending_messages

    # =============================================================================
    # Helper Methods for Conversation History
    # =============================================================================

    def get_conversation(
        self, current_state: Dict[str, Any], agent: Optional[str] = None
    ) -> list:
        """Get conversation history messages in chronological order with optional agent filtering.

        This helper method returns all conversation history messages sorted by completed_at
        timestamp in ascending order (earliest first). Optionally filters to include only
        messages where the specified agent appears as either sender or recipient.

        Args:
            current_state: Current projection state containing conversation_history messages
            agent: Optional agent ID to filter messages. If provided, returns only messages
                  where this agent appears as either from_agent or to_agent.

        Returns:
            List of ConversationMessage objects sorted by completed_at timestamp (earliest first).
            Returns empty list if no messages match the criteria or if conversation_history
            is missing from state.

        Example:
            >>> state = {
            ...     'inbox': [],
            ...     'outbox': [],
            ...     'conversation_history': [msg1, msg2, msg3]
            ... }
            >>> # Get all messages in chronological order
            >>> all_conversation = builder.get_conversation(state)
            >>> # Get only messages involving agent-1
            >>> agent_conversation = builder.get_conversation(state, agent="agent-1")
        """
        # Handle missing conversation_history gracefully
        conversation_messages = current_state.get('conversation_history', [])

        # Apply agent filter if specified
        if agent is not None:
            filtered_messages = [
                msg for msg in conversation_messages
                if msg.from_agent == agent or msg.to_agent == agent
            ]
        else:
            filtered_messages = conversation_messages[:]  # Create a copy

        # Sort by completed_at timestamp (ascending - earliest first)
        filtered_messages.sort(key=lambda msg: msg.completed_at)

        return filtered_messages

    # =============================================================================
    # Correlation ID Tracking and Validation Methods
    # =============================================================================

    def get_messages_by_correlation_id(
        self, current_state: Dict[str, Any], correlation_id: str
    ) -> Dict[str, list]:
        """Get all messages with a specific correlation_id across all message stores.

        This helper method retrieves all messages (inbox, outbox, and conversation_history)
        that share the same correlation_id, providing a complete view of a message thread.

        Args:
            current_state: Current projection state containing all message stores
            correlation_id: The correlation_id to search for

        Returns:
            Dictionary with keys 'inbox', 'outbox', 'conversation_history' containing
            lists of messages that match the correlation_id. Also includes an 'all'
            key with all matching messages combined.

        Example:
            >>> state = {
            ...     'inbox': [msg1, msg2],
            ...     'outbox': [msg3],
            ...     'conversation_history': [msg4, msg5]
            ... }
            >>> thread_messages = builder.get_messages_by_correlation_id(state, "thread-001")
            >>> print(f"Total messages in thread: {len(thread_messages['all'])}")
        """
        result = {
            'inbox': [],
            'outbox': [],
            'conversation_history': [],
            'all': []
        }

        # Search inbox messages
        for msg in current_state.get('inbox', []):
            if msg.correlation_id == correlation_id:
                result['inbox'].append(msg)
                result['all'].append(msg)

        # Search outbox messages
        for msg in current_state.get('outbox', []):
            if msg.correlation_id == correlation_id:
                result['outbox'].append(msg)
                result['all'].append(msg)

        # Search conversation history
        for msg in current_state.get('conversation_history', []):
            if msg.correlation_id == correlation_id:
                result['conversation_history'].append(msg)
                result['all'].append(msg)

        return result

    def validate_thread_consistency(
        self, current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate correlation_id consistency across all message threads.

        This method examines all messages in the projection state and validates that:
        - All messages with the same correlation_id form coherent conversation threads
        - Thread participants are consistent and logical
        - No obvious inconsistencies exist in thread structure

        Args:
            current_state: Current projection state containing all message stores

        Returns:
            Dictionary containing validation results with keys:
            - 'valid': Boolean indicating if all threads are consistent
            - 'inconsistencies': List of detected inconsistencies
            - 'thread_participants': Map of correlation_id to set of participating agents
            - 'thread_statistics': Summary statistics about threads

        Example:
            >>> validation = builder.validate_thread_consistency(state)
            >>> if not validation['valid']:
            ...     print(f"Found {len(validation['inconsistencies'])} issues")
        """
        inconsistencies = []
        correlation_id_agents = {}
        thread_statistics = {
            'total_threads': 0,
            'total_messages': 0,
            'orphaned_threads': 0
        }

        # Collect all messages and analyze by correlation_id
        all_messages = (
            current_state.get('inbox', []) +
            current_state.get('outbox', []) +
            current_state.get('conversation_history', [])
        )

        thread_statistics['total_messages'] = len(all_messages)

        # Group messages by correlation_id
        threads = {}
        for msg in all_messages:
            corr_id = msg.correlation_id
            if corr_id not in threads:
                threads[corr_id] = []
            threads[corr_id].append(msg)

        thread_statistics['total_threads'] = len(threads)

        # Analyze each thread for consistency
        for corr_id, thread_messages in threads.items():
            agents = set()

            # Collect all agents involved in this thread
            for msg in thread_messages:
                agents.add(msg.from_agent)
                agents.add(msg.to_agent)

            correlation_id_agents[corr_id] = agents

            # Check for single-message threads (potentially orphaned)
            if len(thread_messages) == 1:
                msg = thread_messages[0]
                # Only flag as orphaned if it's an acknowledged inbox message
                # (which suggests activity but no corresponding thread)
                if (hasattr(msg, 'acknowledged') and msg.acknowledged and
                    msg in current_state.get('inbox', [])):
                    thread_statistics['orphaned_threads'] += 1
                    inconsistencies.append({
                        'type': 'potentially_orphaned',
                        'correlation_id': corr_id,
                        'message': msg,
                        'issue': 'acknowledged_message_without_thread_activity'
                    })

            # Additional consistency checks can be added here
            # For example: checking for logical message flow, timing consistency, etc.

        return {
            'valid': len(inconsistencies) == 0,
            'inconsistencies': inconsistencies,
            'thread_participants': correlation_id_agents,
            'thread_statistics': thread_statistics
        }

    def get_thread_summary(
        self, current_state: Dict[str, Any], correlation_id: str
    ) -> Dict[str, Any]:
        """Get a comprehensive summary of a message thread by correlation_id.

        This method provides a detailed view of a complete message thread, including
        timeline, participants, status, and message flow.

        Args:
            current_state: Current projection state containing all message stores
            correlation_id: The correlation_id of the thread to summarize

        Returns:
            Dictionary containing thread summary with keys:
            - 'correlation_id': The thread correlation ID
            - 'participants': Set of all agents involved in the thread
            - 'message_count': Total number of messages in thread
            - 'status': Thread status (active, completed, orphaned)
            - 'timeline': Chronologically ordered list of messages
            - 'pending_actions': List of messages awaiting acknowledgment/completion

        Example:
            >>> summary = builder.get_thread_summary(state, "thread-001")
            >>> print(f"Thread has {summary['message_count']} messages")
            >>> print(f"Participants: {', '.join(summary['participants'])}")
        """
        thread_messages = self.get_messages_by_correlation_id(current_state, correlation_id)
        all_messages = thread_messages['all']

        if not all_messages:
            return {
                'correlation_id': correlation_id,
                'participants': set(),
                'message_count': 0,
                'status': 'not_found',
                'timeline': [],
                'pending_actions': []
            }

        # Collect participants
        participants = set()
        for msg in all_messages:
            participants.add(msg.from_agent)
            participants.add(msg.to_agent)

        # Create chronological timeline
        timeline = []

        # Add inbox messages
        for msg in thread_messages['inbox']:
            timeline.append({
                'type': 'received',
                'message': msg,
                'timestamp': getattr(msg, 'received_at', getattr(msg, 'created_at', None)),
                'status': 'acknowledged' if getattr(msg, 'acknowledged', False) else 'pending'
            })

        # Add outbox messages
        for msg in thread_messages['outbox']:
            timeline.append({
                'type': 'sent',
                'message': msg,
                'timestamp': getattr(msg, 'sent_at', getattr(msg, 'created_at', None)),
                'status': 'pending_completion'
            })

        # Add conversation history
        for msg in thread_messages['conversation_history']:
            timeline.append({
                'type': 'completed',
                'message': msg,
                'timestamp': getattr(msg, 'completed_at', getattr(msg, 'created_at', None)),
                'status': 'completed'
            })

        # Sort timeline by timestamp
        timeline.sort(key=lambda item: item['timestamp'] or datetime.min)

        # Determine thread status
        has_pending_inbox = any(
            not getattr(msg, 'acknowledged', True) for msg in thread_messages['inbox']
        )
        has_pending_outbox = len(thread_messages['outbox']) > 0

        if has_pending_inbox or has_pending_outbox:
            status = 'active'
        elif len(thread_messages['conversation_history']) > 0:
            status = 'completed'
        elif len(all_messages) == 1:
            status = 'orphaned'
        else:
            status = 'active'

        # Identify pending actions
        pending_actions = []
        for msg in thread_messages['inbox']:
            if not getattr(msg, 'acknowledged', True):
                pending_actions.append({
                    'type': 'acknowledge_required',
                    'message': msg,
                    'agent': msg.to_agent
                })

        for msg in thread_messages['outbox']:
            pending_actions.append({
                'type': 'completion_required',
                'message': msg,
                'agent': msg.from_agent
            })

        return {
            'correlation_id': correlation_id,
            'participants': participants,
            'message_count': len(all_messages),
            'status': status,
            'timeline': timeline,
            'pending_actions': pending_actions
        }

    # =============================================================================
    # Priority Handling Methods
    # =============================================================================

    def get_messages_by_priority(
        self,
        current_state: Dict[str, Any],
        priority: 'MessagePriority',
        include_all_stores: bool = False
    ) -> list:
        """Get messages filtered by specific priority level.

        Args:
            current_state: Current projection state with inbox, outbox, conversation_history
            priority: Priority level to filter by (URGENT, HIGH, NORMAL, LOW)
            include_all_stores: If True, search all stores; if False, search only inbox

        Returns:
            List of messages with the specified priority, sorted by priority rules

        Examples:
            >>> urgent_msgs = builder.get_messages_by_priority(state, MessagePriority.URGENT)
            >>> all_normal = builder.get_messages_by_priority(
            ...     state, MessagePriority.NORMAL, include_all_stores=True
            ... )
        """
        from .message import MessagePriority

        result_messages = []

        # Always include inbox
        inbox_messages = current_state.get('inbox', [])
        result_messages.extend([msg for msg in inbox_messages if msg.priority == priority])

        if include_all_stores:
            # Include outbox
            outbox_messages = current_state.get('outbox', [])
            result_messages.extend([msg for msg in outbox_messages if msg.priority == priority])

            # Include conversation history
            history_messages = current_state.get('conversation_history', [])
            result_messages.extend([msg for msg in history_messages if msg.priority == priority])

        # Sort using the same priority logic as get_unread_inbox
        priority_order = {
            MessagePriority.URGENT: 4,
            MessagePriority.HIGH: 3,
            MessagePriority.NORMAL: 2,
            MessagePriority.LOW: 1
        }

        result_messages.sort(
            key=lambda msg: (
                -priority_order.get(msg.priority, 0),
                getattr(msg, 'received_at', getattr(msg, 'sent_at', getattr(msg, 'created_at', datetime.min)))
            )
        )

        return result_messages

    def get_high_priority_messages(self, current_state: Dict[str, Any]) -> list:
        """Get high priority messages (URGENT and HIGH) from inbox.

        Args:
            current_state: Current projection state

        Returns:
            List of URGENT and HIGH priority messages from inbox, sorted by priority

        Example:
            >>> high_priority = builder.get_high_priority_messages(state)
            >>> # Returns [urgent_msgs..., high_msgs...] sorted by priority
        """
        from .message import MessagePriority

        inbox_messages = current_state.get('inbox', [])
        high_priority_msgs = [
            msg for msg in inbox_messages
            if msg.priority in [MessagePriority.URGENT, MessagePriority.HIGH]
        ]

        # Sort by priority (URGENT first, then HIGH)
        priority_order = {
            MessagePriority.URGENT: 4,
            MessagePriority.HIGH: 3
        }

        high_priority_msgs.sort(
            key=lambda msg: (
                -priority_order.get(msg.priority, 0),
                getattr(msg, 'received_at', datetime.min)
            )
        )

        return high_priority_msgs

    def get_low_priority_messages(self, current_state: Dict[str, Any]) -> list:
        """Get low priority messages (LOW only) from inbox.

        Args:
            current_state: Current projection state

        Returns:
            List of LOW priority messages from inbox

        Example:
            >>> low_priority = builder.get_low_priority_messages(state)
            >>> # Returns only LOW priority messages
        """
        from .message import MessagePriority

        inbox_messages = current_state.get('inbox', [])
        low_priority_msgs = [
            msg for msg in inbox_messages
            if msg.priority == MessagePriority.LOW
        ]

        low_priority_msgs.sort(key=lambda msg: getattr(msg, 'received_at', datetime.min))

        return low_priority_msgs

    def get_messages_above_priority(
        self,
        current_state: Dict[str, Any],
        threshold_priority: 'MessagePriority'
    ) -> list:
        """Get messages with priority above a threshold level.

        Args:
            current_state: Current projection state
            threshold_priority: Priority threshold (messages above this will be returned)

        Returns:
            List of messages with priority higher than threshold, sorted by priority

        Example:
            >>> above_normal = builder.get_messages_above_priority(
            ...     state, MessagePriority.NORMAL
            ... )
            >>> # Returns URGENT and HIGH priority messages
        """
        from .message import MessagePriority

        priority_order = {
            MessagePriority.URGENT: 4,
            MessagePriority.HIGH: 3,
            MessagePriority.NORMAL: 2,
            MessagePriority.LOW: 1
        }

        threshold_value = priority_order.get(threshold_priority, 0)
        inbox_messages = current_state.get('inbox', [])

        above_threshold = [
            msg for msg in inbox_messages
            if priority_order.get(msg.priority, 0) > threshold_value
        ]

        above_threshold.sort(
            key=lambda msg: (
                -priority_order.get(msg.priority, 0),
                getattr(msg, 'received_at', datetime.min)
            )
        )

        return above_threshold

    def get_outbox_messages_by_priority(
        self,
        current_state: Dict[str, Any],
        priority: 'MessagePriority'
    ) -> list:
        """Get outbox messages filtered by specific priority level.

        Args:
            current_state: Current projection state
            priority: Priority level to filter by

        Returns:
            List of outbox messages with the specified priority

        Example:
            >>> urgent_outbox = builder.get_outbox_messages_by_priority(
            ...     state, MessagePriority.URGENT
            ... )
        """
        outbox_messages = current_state.get('outbox', [])
        filtered_messages = [msg for msg in outbox_messages if msg.priority == priority]

        filtered_messages.sort(key=lambda msg: getattr(msg, 'sent_at', datetime.min))

        return filtered_messages

    def get_conversation_messages_by_priority(
        self,
        current_state: Dict[str, Any],
        priority: 'MessagePriority'
    ) -> list:
        """Get conversation history messages filtered by specific priority level.

        Args:
            current_state: Current projection state
            priority: Priority level to filter by

        Returns:
            List of conversation history messages with the specified priority

        Example:
            >>> urgent_history = builder.get_conversation_messages_by_priority(
            ...     state, MessagePriority.URGENT
            ... )
        """
        history_messages = current_state.get('conversation_history', [])
        filtered_messages = [msg for msg in history_messages if msg.priority == priority]

        filtered_messages.sort(key=lambda msg: getattr(msg, 'completed_at', datetime.min))

        return filtered_messages

    def get_priority_distribution(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get priority distribution statistics across all message stores.

        Args:
            current_state: Current projection state

        Returns:
            Dict with priority distribution statistics including:
            - total_messages: Total number of messages
            - by_priority: Count by each priority level
            - by_store: Count by priority for each store (inbox, outbox, history)

        Example:
            >>> distribution = builder.get_priority_distribution(state)
            >>> print(distribution['by_priority'][MessagePriority.URGENT])
            >>> print(distribution['by_store']['inbox'][MessagePriority.HIGH])
        """
        from .message import MessagePriority

        # Initialize counters
        priority_counts = {priority: 0 for priority in MessagePriority}
        store_priority_counts = {
            'inbox': {priority: 0 for priority in MessagePriority},
            'outbox': {priority: 0 for priority in MessagePriority},
            'conversation_history': {priority: 0 for priority in MessagePriority}
        }

        total_messages = 0

        # Count inbox messages
        for msg in current_state.get('inbox', []):
            priority_counts[msg.priority] += 1
            store_priority_counts['inbox'][msg.priority] += 1
            total_messages += 1

        # Count outbox messages
        for msg in current_state.get('outbox', []):
            priority_counts[msg.priority] += 1
            store_priority_counts['outbox'][msg.priority] += 1
            total_messages += 1

        # Count conversation history messages
        for msg in current_state.get('conversation_history', []):
            priority_counts[msg.priority] += 1
            store_priority_counts['conversation_history'][msg.priority] += 1
            total_messages += 1

        return {
            'total_messages': total_messages,
            'by_priority': priority_counts,
            'by_store': store_priority_counts
        }

    def get_priority_summary(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get priority summary statistics.

        Args:
            current_state: Current projection state

        Returns:
            Dict with priority summary including:
            - total_messages: Total number of messages
            - urgent_count: Number of URGENT messages
            - high_priority_count: Number of URGENT + HIGH messages
            - low_priority_count: Number of LOW messages
            - priority_percentage: Percentage breakdown by priority

        Example:
            >>> summary = builder.get_priority_summary(state)
            >>> print(f"Urgent: {summary['urgent_count']}")
            >>> print(f"High priority: {summary['high_priority_count']}")
        """
        from .message import MessagePriority

        distribution = self.get_priority_distribution(current_state)
        total_messages = distribution['total_messages']

        urgent_count = distribution['by_priority'][MessagePriority.URGENT]
        high_count = distribution['by_priority'][MessagePriority.HIGH]
        normal_count = distribution['by_priority'][MessagePriority.NORMAL]
        low_count = distribution['by_priority'][MessagePriority.LOW]

        high_priority_count = urgent_count + high_count

        # Calculate percentages
        priority_percentage = {}
        if total_messages > 0:
            priority_percentage = {
                priority: (count / total_messages) * 100
                for priority, count in distribution['by_priority'].items()
            }
        else:
            priority_percentage = {priority: 0.0 for priority in MessagePriority}

        return {
            'total_messages': total_messages,
            'urgent_count': urgent_count,
            'high_priority_count': high_priority_count,
            'low_priority_count': low_count,
            'priority_percentage': priority_percentage
        }

    def has_urgent_messages(self, current_state: Dict[str, Any]) -> bool:
        """Check if there are any urgent messages in any store.

        Args:
            current_state: Current projection state

        Returns:
            True if there are URGENT messages in inbox, outbox, or history

        Example:
            >>> if builder.has_urgent_messages(state):
            ...     print("Urgent attention required!")
        """
        from .message import MessagePriority

        # Check inbox
        for msg in current_state.get('inbox', []):
            if msg.priority == MessagePriority.URGENT:
                return True

        # Check outbox
        for msg in current_state.get('outbox', []):
            if msg.priority == MessagePriority.URGENT:
                return True

        # Check conversation history
        for msg in current_state.get('conversation_history', []):
            if msg.priority == MessagePriority.URGENT:
                return True

        return False

    def get_next_priority_message(self, current_state: Dict[str, Any]):
        """Get the next highest priority unread message from inbox.

        Args:
            current_state: Current projection state

        Returns:
            The highest priority unacknowledged InboxMessage, or None if no unread messages

        Example:
            >>> next_msg = builder.get_next_priority_message(state)
            >>> if next_msg:
            ...     print(f"Next: {next_msg.priority} - {next_msg.subject}")
        """
        unread_messages = self.get_unread_inbox(current_state)
        return unread_messages[0] if unread_messages else None