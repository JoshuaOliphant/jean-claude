# ABOUTME: NotesProjectionBuilder class for agent notes projections
# ABOUTME: Extends ProjectionBuilder to provide notes functionality with basic structure and empty state initialization

"""NotesProjectionBuilder for agent notes projections.

This module provides the NotesProjectionBuilder class which extends the abstract
ProjectionBuilder to create projections specifically for agent notes functionality.
It maintains notes list and empty indexes for by_category, by_agent, and by_tag.

The NotesProjectionBuilder processes agent note events to build read models
that support notes views, categorization, and searching.

Key Features:
- Maintains notes list for all notes
- Provides empty indexes for by_category, by_agent, and by_tag
- Provides basic state initialization
"""

from typing import Dict, Any
from datetime import datetime
from copy import deepcopy

from .projection_builder import ProjectionBuilder
from .event_models import Event


class NotesProjectionBuilder(ProjectionBuilder):
    """Projection builder for agent notes functionality.

    This class extends ProjectionBuilder to provide specialized handling for
    agent note events. It creates and maintains projections that support
    notes views, categorization, and searching functionality.

    State Structure:
        The projection state maintained by this builder contains:
        - notes: List of all notes
        - by_category: Empty dictionary for indexing notes by category
        - by_agent: Empty dictionary for indexing notes by agent_id
        - by_tag: Empty dictionary for indexing notes by tags

    Event Handling:
        Currently provides basic implementations that return the current state.
        Future features will implement full event processing logic for:
        - Agent note observation events
        - Agent note learning events
        - Agent note decision events
        - Agent note warning events
        - Agent note accomplishment events
        - Agent note context events
        - Agent note todo events
        - Agent message events

    Example:
        >>> builder = NotesProjectionBuilder()
        >>> initial_state = builder.get_initial_state()
        >>> print(initial_state)
        {'notes': [], 'by_category': {}, 'by_agent': {}, 'by_tag': {}}
    """

    def get_initial_state(self) -> Dict[str, Any]:
        """Create the initial state for a notes projection.

        Returns:
            Dict containing empty list for notes and empty dictionaries for indexes

        Example:
            >>> builder = NotesProjectionBuilder()
            >>> state = builder.get_initial_state()
            >>> state
            {'notes': [], 'by_category': {}, 'by_agent': {}, 'by_tag': {}}
        """
        return {
            'notes': [],
            'by_category': {},
            'by_agent': {},
            'by_tag': {}
        }

    # Agent message event handlers

    def apply_agent_message_sent(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.message.sent event to update projection state.

        Args:
            event_data: Event data containing message details (from_agent, to_agent, content, etc.)
            current_state: Current projection state

        Returns:
            Updated projection state

        Note:
            This is a basic implementation that returns the current state unchanged.
            Full implementation will be added in future features.
        """
        # Basic implementation - full logic will be added in future features
        return current_state

    def apply_agent_message_acknowledged(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.message.acknowledged event to update projection state.

        Args:
            event_data: Event data containing correlation_id, from_agent, acknowledged_at
            current_state: Current projection state

        Returns:
            Updated projection state

        Note:
            This is a basic implementation that returns the current state unchanged.
            Full implementation will be added in future features.
        """
        # Basic implementation - full logic will be added in future features
        return current_state

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
            Full implementation will be added in future features.
        """
        # Basic implementation - full logic will be added in future features
        return current_state

    # Agent note event handlers

    def apply_agent_note_observation(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.observation event to update projection state.

        Processes an observation note event by adding it to the notes list and
        updating the by_category, by_agent, and by_tag indexes.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
                Expected fields: agent_id, title, content, tags
                Optional fields: related_file, related_feature
            current_state: Current projection state

        Returns:
            Updated projection state with new observation note added

        Example:
            >>> event_data = {
            ...     "agent_id": "agent-123",
            ...     "title": "Test Observation",
            ...     "content": "Observed system behavior",
            ...     "tags": ["system", "behavior"],
            ...     "related_file": "src/main.py"
            ... }
            >>> new_state = builder.apply_agent_note_observation(event_data, state)
        """
        # Create a deep copy of the current state to ensure immutability
        new_state = deepcopy(current_state)

        # Ensure all required state keys exist
        if 'notes' not in new_state:
            new_state['notes'] = []
        if 'by_category' not in new_state:
            new_state['by_category'] = {}
        if 'by_agent' not in new_state:
            new_state['by_agent'] = {}
        if 'by_tag' not in new_state:
            new_state['by_tag'] = {}

        # Create the note object
        note = {
            'agent_id': event_data['agent_id'],
            'title': event_data['title'],
            'content': event_data.get('content', ''),
            'category': 'observation',
            'tags': event_data.get('tags', []),
            'related_file': event_data.get('related_file'),
            'related_feature': event_data.get('related_feature'),
            'created_at': datetime.now().isoformat() + 'Z'
        }

        # Add note to notes list
        new_state['notes'].append(note)
        note_index = len(new_state['notes']) - 1

        # Update by_category index
        category = 'observation'
        if category not in new_state['by_category']:
            new_state['by_category'][category] = []
        new_state['by_category'][category].append(note_index)

        # Update by_agent index
        agent_id = event_data['agent_id']
        if agent_id not in new_state['by_agent']:
            new_state['by_agent'][agent_id] = []
        new_state['by_agent'][agent_id].append(note_index)

        # Update by_tag index
        tags = event_data.get('tags', [])
        for tag in tags:
            if tag not in new_state['by_tag']:
                new_state['by_tag'][tag] = []
            new_state['by_tag'][tag].append(note_index)

        return new_state

    def apply_agent_note_learning(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.learning event to update projection state.

        Processes a learning note event by adding it to the notes list and
        updating the by_category, by_agent, and by_tag indexes.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
                Expected fields: agent_id, title, content, tags
                Optional fields: related_file, related_feature
            current_state: Current projection state

        Returns:
            Updated projection state with new learning note added

        Example:
            >>> event_data = {
            ...     "agent_id": "agent-123",
            ...     "title": "Test Learning",
            ...     "content": "Key insight about patterns",
            ...     "tags": ["patterns", "insight"],
            ...     "related_file": "src/core/base.py"
            ... }
            >>> new_state = builder.apply_agent_note_learning(event_data, state)
        """
        # Create a deep copy of the current state to ensure immutability
        new_state = deepcopy(current_state)

        # Ensure all required state keys exist
        if 'notes' not in new_state:
            new_state['notes'] = []
        if 'by_category' not in new_state:
            new_state['by_category'] = {}
        if 'by_agent' not in new_state:
            new_state['by_agent'] = {}
        if 'by_tag' not in new_state:
            new_state['by_tag'] = {}

        # Create the note object
        note = {
            'agent_id': event_data['agent_id'],
            'title': event_data['title'],
            'content': event_data.get('content', ''),
            'category': 'learning',
            'tags': event_data.get('tags', []),
            'related_file': event_data.get('related_file'),
            'related_feature': event_data.get('related_feature'),
            'created_at': datetime.now().isoformat() + 'Z'
        }

        # Add note to notes list
        new_state['notes'].append(note)
        note_index = len(new_state['notes']) - 1

        # Update by_category index
        category = 'learning'
        if category not in new_state['by_category']:
            new_state['by_category'][category] = []
        new_state['by_category'][category].append(note_index)

        # Update by_agent index
        agent_id = event_data['agent_id']
        if agent_id not in new_state['by_agent']:
            new_state['by_agent'][agent_id] = []
        new_state['by_agent'][agent_id].append(note_index)

        # Update by_tag index
        tags = event_data.get('tags', [])
        for tag in tags:
            if tag not in new_state['by_tag']:
                new_state['by_tag'][tag] = []
            new_state['by_tag'][tag].append(note_index)

        return new_state

    def apply_agent_note_decision(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.decision event to update projection state.

        Processes a decision note event by adding it to the notes list and
        updating the by_category, by_agent, and by_tag indexes.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
                Expected fields: agent_id, title, content, tags
                Optional fields: related_file, related_feature
            current_state: Current projection state

        Returns:
            Updated projection state with new decision note added

        Example:
            >>> event_data = {
            ...     "agent_id": "agent-123",
            ...     "title": "Test Decision",
            ...     "content": "Key decision about patterns",
            ...     "tags": ["patterns", "decision"],
            ...     "related_file": "src/core/base.py"
            ... }
            >>> new_state = builder.apply_agent_note_decision(event_data, state)
        """
        # Create a deep copy of the current state to ensure immutability
        new_state = deepcopy(current_state)

        # Ensure all required state keys exist
        if 'notes' not in new_state:
            new_state['notes'] = []
        if 'by_category' not in new_state:
            new_state['by_category'] = {}
        if 'by_agent' not in new_state:
            new_state['by_agent'] = {}
        if 'by_tag' not in new_state:
            new_state['by_tag'] = {}

        # Create the note object
        note = {
            'agent_id': event_data['agent_id'],
            'title': event_data['title'],
            'content': event_data.get('content', ''),
            'category': 'decision',
            'tags': event_data.get('tags', []),
            'related_file': event_data.get('related_file'),
            'related_feature': event_data.get('related_feature'),
            'created_at': datetime.now().isoformat() + 'Z'
        }

        # Add note to notes list
        new_state['notes'].append(note)
        note_index = len(new_state['notes']) - 1

        # Update by_category index
        category = 'decision'
        if category not in new_state['by_category']:
            new_state['by_category'][category] = []
        new_state['by_category'][category].append(note_index)

        # Update by_agent index
        agent_id = event_data['agent_id']
        if agent_id not in new_state['by_agent']:
            new_state['by_agent'][agent_id] = []
        new_state['by_agent'][agent_id].append(note_index)

        # Update by_tag index for each tag
        for tag in event_data.get('tags', []):
            if tag not in new_state['by_tag']:
                new_state['by_tag'][tag] = []
            new_state['by_tag'][tag].append(note_index)

        return new_state

    def apply_agent_note_warning(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.warning event to update projection state.

        Processes a warning note event by adding it to the notes list and
        updating the by_category, by_agent, and by_tag indexes.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
                Expected fields: agent_id, title, content, tags
                Optional fields: related_file, related_feature
            current_state: Current projection state

        Returns:
            Updated projection state with new warning note added

        Example:
            >>> event_data = {
            ...     "agent_id": "agent-123",
            ...     "title": "Test Warning",
            ...     "content": "Potential issue detected",
            ...     "tags": ["risk", "attention"],
            ...     "related_file": "src/core/base.py"
            ... }
            >>> new_state = builder.apply_agent_note_warning(event_data, state)
        """
        # Create a deep copy of the current state to ensure immutability
        new_state = deepcopy(current_state)

        # Ensure all required state keys exist
        if 'notes' not in new_state:
            new_state['notes'] = []
        if 'by_category' not in new_state:
            new_state['by_category'] = {}
        if 'by_agent' not in new_state:
            new_state['by_agent'] = {}
        if 'by_tag' not in new_state:
            new_state['by_tag'] = {}

        # Create the note object
        note = {
            'agent_id': event_data['agent_id'],
            'title': event_data['title'],
            'content': event_data.get('content', ''),
            'category': 'warning',
            'tags': event_data.get('tags', []),
            'related_file': event_data.get('related_file'),
            'related_feature': event_data.get('related_feature'),
            'created_at': datetime.now().isoformat() + 'Z'
        }

        # Add note to notes list
        new_state['notes'].append(note)
        note_index = len(new_state['notes']) - 1

        # Update by_category index
        category = 'warning'
        if category not in new_state['by_category']:
            new_state['by_category'][category] = []
        new_state['by_category'][category].append(note_index)

        # Update by_agent index
        agent_id = event_data['agent_id']
        if agent_id not in new_state['by_agent']:
            new_state['by_agent'][agent_id] = []
        new_state['by_agent'][agent_id].append(note_index)

        # Update by_tag index
        tags = event_data.get('tags', [])
        for tag in tags:
            if tag not in new_state['by_tag']:
                new_state['by_tag'][tag] = []
            new_state['by_tag'][tag].append(note_index)

        return new_state

    def apply_agent_note_accomplishment(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.accomplishment event to update projection state.

        Processes an accomplishment note event by adding it to the notes list and
        updating the by_category, by_agent, and by_tag indexes.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
                Expected fields: agent_id, title, content, tags
                Optional fields: related_file, related_feature
            current_state: Current projection state

        Returns:
            Updated projection state with new accomplishment note added

        Example:
            >>> event_data = {
            ...     "agent_id": "agent-123",
            ...     "title": "Test Accomplishment",
            ...     "content": "Successfully completed milestone",
            ...     "tags": ["milestone", "success"],
            ...     "related_feature": "user-auth"
            ... }
            >>> new_state = builder.apply_agent_note_accomplishment(event_data, state)
        """
        # Create a deep copy of the current state to ensure immutability
        new_state = deepcopy(current_state)

        # Ensure all required state keys exist
        if 'notes' not in new_state:
            new_state['notes'] = []
        if 'by_category' not in new_state:
            new_state['by_category'] = {}
        if 'by_agent' not in new_state:
            new_state['by_agent'] = {}
        if 'by_tag' not in new_state:
            new_state['by_tag'] = {}

        # Create the note object
        note = {
            'agent_id': event_data['agent_id'],
            'title': event_data['title'],
            'content': event_data.get('content', ''),
            'category': 'accomplishment',
            'tags': event_data.get('tags', []),
            'related_file': event_data.get('related_file'),
            'related_feature': event_data.get('related_feature'),
            'created_at': datetime.now().isoformat() + 'Z'
        }

        # Add note to notes list
        new_state['notes'].append(note)
        note_index = len(new_state['notes']) - 1

        # Update by_category index
        category = 'accomplishment'
        if category not in new_state['by_category']:
            new_state['by_category'][category] = []
        new_state['by_category'][category].append(note_index)

        # Update by_agent index
        agent_id = event_data['agent_id']
        if agent_id not in new_state['by_agent']:
            new_state['by_agent'][agent_id] = []
        new_state['by_agent'][agent_id].append(note_index)

        # Update by_tag index
        tags = event_data.get('tags', [])
        for tag in tags:
            if tag not in new_state['by_tag']:
                new_state['by_tag'][tag] = []
            new_state['by_tag'][tag].append(note_index)

        return new_state

    def apply_agent_note_context(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.context event to update projection state.

        Processes a context note event by adding it to the notes list and
        updating the by_category, by_agent, and by_tag indexes.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
                Expected fields: agent_id, title, content, tags
                Optional fields: related_file, related_feature
            current_state: Current projection state

        Returns:
            Updated projection state with new context note added

        Example:
            >>> event_data = {
            ...     "agent_id": "agent-123",
            ...     "title": "Test Context",
            ...     "content": "Background information for the task",
            ...     "tags": ["background", "reference"],
            ...     "related_file": "docs/architecture.md"
            ... }
            >>> new_state = builder.apply_agent_note_context(event_data, state)
        """
        # Create a deep copy of the current state to ensure immutability
        new_state = deepcopy(current_state)

        # Ensure all required state keys exist
        if 'notes' not in new_state:
            new_state['notes'] = []
        if 'by_category' not in new_state:
            new_state['by_category'] = {}
        if 'by_agent' not in new_state:
            new_state['by_agent'] = {}
        if 'by_tag' not in new_state:
            new_state['by_tag'] = {}

        # Create the note object
        note = {
            'agent_id': event_data['agent_id'],
            'title': event_data['title'],
            'content': event_data.get('content', ''),
            'category': 'context',
            'tags': event_data.get('tags', []),
            'related_file': event_data.get('related_file'),
            'related_feature': event_data.get('related_feature'),
            'created_at': datetime.now().isoformat() + 'Z'
        }

        # Add note to notes list
        new_state['notes'].append(note)
        note_index = len(new_state['notes']) - 1

        # Update by_category index
        category = 'context'
        if category not in new_state['by_category']:
            new_state['by_category'][category] = []
        new_state['by_category'][category].append(note_index)

        # Update by_agent index
        agent_id = event_data['agent_id']
        if agent_id not in new_state['by_agent']:
            new_state['by_agent'][agent_id] = []
        new_state['by_agent'][agent_id].append(note_index)

        # Update by_tag index
        tags = event_data.get('tags', [])
        for tag in tags:
            if tag not in new_state['by_tag']:
                new_state['by_tag'][tag] = []
            new_state['by_tag'][tag].append(note_index)

        return new_state

    def apply_agent_note_todo(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.todo event to update projection state.

        Processes a todo note event by adding it to the notes list and
        updating the by_category, by_agent, and by_tag indexes.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
                Expected fields: agent_id, title, content, tags
                Optional fields: related_file, related_feature
            current_state: Current projection state

        Returns:
            Updated projection state with new todo note added

        Example:
            >>> event_data = {
            ...     "agent_id": "agent-123",
            ...     "title": "Test Todo",
            ...     "content": "Task that needs to be completed",
            ...     "tags": ["task", "urgent"],
            ...     "related_file": "src/core/base.py"
            ... }
            >>> new_state = builder.apply_agent_note_todo(event_data, state)
        """
        # Create a deep copy of the current state to ensure immutability
        new_state = deepcopy(current_state)

        # Ensure all required state keys exist
        if 'notes' not in new_state:
            new_state['notes'] = []
        if 'by_category' not in new_state:
            new_state['by_category'] = {}
        if 'by_agent' not in new_state:
            new_state['by_agent'] = {}
        if 'by_tag' not in new_state:
            new_state['by_tag'] = {}

        # Create the note object
        note = {
            'agent_id': event_data['agent_id'],
            'title': event_data['title'],
            'content': event_data.get('content', ''),
            'category': 'todo',
            'tags': event_data.get('tags', []),
            'related_file': event_data.get('related_file'),
            'related_feature': event_data.get('related_feature'),
            'created_at': datetime.now().isoformat() + 'Z'
        }

        # Add note to notes list
        new_state['notes'].append(note)
        note_index = len(new_state['notes']) - 1

        # Update by_category index
        category = 'todo'
        if category not in new_state['by_category']:
            new_state['by_category'][category] = []
        new_state['by_category'][category].append(note_index)

        # Update by_agent index
        agent_id = event_data['agent_id']
        if agent_id not in new_state['by_agent']:
            new_state['by_agent'][agent_id] = []
        new_state['by_agent'][agent_id].append(note_index)

        # Update by_tag index for each tag
        for tag in event_data.get('tags', []):
            if tag not in new_state['by_tag']:
                new_state['by_tag'][tag] = []
            new_state['by_tag'][tag].append(note_index)

        return new_state

    def apply_agent_note_question(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.question event to update projection state.

        Processes a question note event by adding it to the notes list and
        updating the by_category, by_agent, and by_tag indexes.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
                Expected fields: agent_id, title, content, tags
                Optional fields: related_file, related_feature
            current_state: Current projection state

        Returns:
            Updated projection state with new question note added

        Example:
            >>> event_data = {
            ...     "agent_id": "agent-123",
            ...     "title": "Test Question",
            ...     "content": "What is the best approach for this?",
            ...     "tags": ["implementation", "approach"],
            ...     "related_file": "src/core/base.py"
            ... }
            >>> new_state = builder.apply_agent_note_question(event_data, state)
        """
        # Create a deep copy of the current state to ensure immutability
        new_state = deepcopy(current_state)

        # Ensure all required state keys exist
        if 'notes' not in new_state:
            new_state['notes'] = []
        if 'by_category' not in new_state:
            new_state['by_category'] = {}
        if 'by_agent' not in new_state:
            new_state['by_agent'] = {}
        if 'by_tag' not in new_state:
            new_state['by_tag'] = {}

        # Create the note object
        note = {
            'agent_id': event_data['agent_id'],
            'title': event_data['title'],
            'content': event_data.get('content', ''),
            'category': 'question',
            'tags': event_data.get('tags', []),
            'related_file': event_data.get('related_file'),
            'related_feature': event_data.get('related_feature'),
            'created_at': datetime.now().isoformat() + 'Z'
        }

        # Add note to notes list
        new_state['notes'].append(note)
        note_index = len(new_state['notes']) - 1

        # Update by_category index
        category = 'question'
        if category not in new_state['by_category']:
            new_state['by_category'][category] = []
        new_state['by_category'][category].append(note_index)

        # Update by_agent index
        agent_id = event_data['agent_id']
        if agent_id not in new_state['by_agent']:
            new_state['by_agent'][agent_id] = []
        new_state['by_agent'][agent_id].append(note_index)

        # Update by_tag index for each tag
        for tag in event_data.get('tags', []):
            if tag not in new_state['by_tag']:
                new_state['by_tag'][tag] = []
            new_state['by_tag'][tag].append(note_index)

        return new_state

    def apply_agent_note_idea(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.idea event to update projection state.

        Processes an idea note event by adding it to the notes list and
        updating the by_category, by_agent, and by_tag indexes.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
                Expected fields: agent_id, title, content, tags
                Optional fields: related_file, related_feature
            current_state: Current projection state

        Returns:
            Updated projection state with new idea note added

        Example:
            >>> event_data = {
            ...     "agent_id": "agent-123",
            ...     "title": "Test Idea",
            ...     "content": "Brilliant idea about patterns",
            ...     "tags": ["innovation", "patterns"],
            ...     "related_file": "src/core/base.py"
            ... }
            >>> new_state = builder.apply_agent_note_idea(event_data, state)
        """
        # Create a deep copy of the current state to ensure immutability
        new_state = deepcopy(current_state)

        # Ensure all required state keys exist
        if 'notes' not in new_state:
            new_state['notes'] = []
        if 'by_category' not in new_state:
            new_state['by_category'] = {}
        if 'by_agent' not in new_state:
            new_state['by_agent'] = {}
        if 'by_tag' not in new_state:
            new_state['by_tag'] = {}

        # Create the note object
        note = {
            'agent_id': event_data['agent_id'],
            'title': event_data['title'],
            'content': event_data.get('content', ''),
            'category': 'idea',
            'tags': event_data.get('tags', []),
            'related_file': event_data.get('related_file'),
            'related_feature': event_data.get('related_feature'),
            'created_at': datetime.now().isoformat() + 'Z'
        }

        # Add note to notes list
        new_state['notes'].append(note)
        note_index = len(new_state['notes']) - 1

        # Update by_category index
        category = 'idea'
        if category not in new_state['by_category']:
            new_state['by_category'][category] = []
        new_state['by_category'][category].append(note_index)

        # Update by_agent index
        agent_id = event_data['agent_id']
        if agent_id not in new_state['by_agent']:
            new_state['by_agent'][agent_id] = []
        new_state['by_agent'][agent_id].append(note_index)

        # Update by_tag index for each tag
        for tag in event_data.get('tags', []):
            if tag not in new_state['by_tag']:
                new_state['by_tag'][tag] = []
            new_state['by_tag'][tag].append(note_index)

        return new_state

    def apply_agent_note_reflection(
        self, event_data: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent.note.reflection event to update projection state.

        Processes a reflection note event by adding it to the notes list and
        updating the by_category, by_agent, and by_tag indexes.

        Args:
            event_data: Event data containing agent_id, title, content, tags, etc.
                Expected fields: agent_id, title, content, tags
                Optional fields: related_file, related_feature
            current_state: Current projection state

        Returns:
            Updated projection state with new reflection note added

        Example:
            >>> event_data = {
            ...     "agent_id": "agent-123",
            ...     "title": "Test Reflection",
            ...     "content": "Thoughtful reflection on process",
            ...     "tags": ["process", "reflection"],
            ...     "related_file": "src/core/base.py"
            ... }
            >>> new_state = builder.apply_agent_note_reflection(event_data, state)
        """
        # Create a deep copy of the current state to ensure immutability
        new_state = deepcopy(current_state)

        # Ensure all required state keys exist
        if 'notes' not in new_state:
            new_state['notes'] = []
        if 'by_category' not in new_state:
            new_state['by_category'] = {}
        if 'by_agent' not in new_state:
            new_state['by_agent'] = {}
        if 'by_tag' not in new_state:
            new_state['by_tag'] = {}

        # Create the note object
        note = {
            'agent_id': event_data['agent_id'],
            'title': event_data['title'],
            'content': event_data.get('content', ''),
            'category': 'reflection',
            'tags': event_data.get('tags', []),
            'related_file': event_data.get('related_file'),
            'related_feature': event_data.get('related_feature'),
            'created_at': datetime.now().isoformat() + 'Z'
        }

        # Add note to notes list
        new_state['notes'].append(note)
        note_index = len(new_state['notes']) - 1

        # Update by_category index
        category = 'reflection'
        if category not in new_state['by_category']:
            new_state['by_category'][category] = []
        new_state['by_category'][category].append(note_index)

        # Update by_agent index
        agent_id = event_data['agent_id']
        if agent_id not in new_state['by_agent']:
            new_state['by_agent'][agent_id] = []
        new_state['by_agent'][agent_id].append(note_index)

        # Update by_tag index for each tag
        for tag in event_data.get('tags', []):
            if tag not in new_state['by_tag']:
                new_state['by_tag'][tag] = []
            new_state['by_tag'][tag].append(note_index)

        return new_state

    # ProjectionBuilder abstract method implementations
    # These provide basic implementations that maintain current state
    # Future features will add specific logic for notes functionality

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