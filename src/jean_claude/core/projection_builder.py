# ABOUTME: Abstract base class for event projection builders in event sourcing architecture
# ABOUTME: Provides abstract methods for handling different event types to build read models

"""Abstract base class for event projection builders.

This module provides the ProjectionBuilder abstract base class which defines
the interface for building projections (read models) from events in an event
sourcing architecture.

A projection builder is responsible for processing events and updating read models
accordingly. Each event type has a corresponding abstract method that must be
implemented by concrete projection builders.

The ProjectionBuilder follows the abstract base class pattern to ensure all
concrete implementations provide handlers for all supported event types.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from .events import AgentNoteEventData
from .event_schemas import (
    AgentMessageSentData,
    AgentMessageAcknowledgedData,
    AgentMessageCompletedData,
)


class ProjectionBuilder(ABC):
    """Abstract base class for event projection builders.

    A ProjectionBuilder processes events and builds projections (read models)
    from the event stream. Each event type has a corresponding abstract method
    that concrete implementations must provide.

    This class enforces that all projection builders handle all supported event
    types, ensuring consistent behavior across different projection implementations.

    Event Handler Methods:
    - Agent messaging events (from jean_claude-di8)
    - Agent note events (from jean_claude-nhj)

    Example:
        >>> class MyProjectionBuilder(ProjectionBuilder):
        ...     def apply_agent_message_sent(self, event_data: Dict[str, Any], current_state: Dict) -> Dict:
        ...         # Process message sent event and return updated state
        ...         new_state = current_state.copy()
        ...         # ... update state based on message ...
        ...         return new_state
        ...     # ... implement other abstract methods
    """

    # Agent message event handlers (from jean_claude-di8)

    @abstractmethod
    def apply_agent_message_sent(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.message.sent event to update projection state.

        Args:
            event_data: Event data containing message details (from_agent, to_agent, content, etc.)
            current_state: Current projection state

        Returns:
            Updated projection state

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass

    @abstractmethod
    def apply_agent_message_acknowledged(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.message.acknowledged event to update projection state.

        Args:
            event_data: Event data containing correlation_id, from_agent, acknowledged_at
            current_state: Current projection state

        Returns:
            Updated projection state

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass

    @abstractmethod
    def apply_agent_message_completed(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.message.completed event to update projection state.

        Args:
            event_data: Event data containing correlation_id, from_agent, result, success
            current_state: Current projection state

        Returns:
            Updated projection state

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass

    # Agent note event handlers (from jean_claude-nhj)

    @abstractmethod
    def apply_agent_note_observation(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.observation event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass

    @abstractmethod
    def apply_agent_note_learning(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.learning event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass

    @abstractmethod
    def apply_agent_note_decision(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.decision event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass

    @abstractmethod
    def apply_agent_note_warning(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.warning event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass

    @abstractmethod
    def apply_agent_note_accomplishment(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.accomplishment event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass

    @abstractmethod
    def apply_agent_note_context(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.context event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass

    @abstractmethod
    def apply_agent_note_todo(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.todo event to update projection state.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
            current_state: Current projection state

        Returns:
            Updated projection state

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass
