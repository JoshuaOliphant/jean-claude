# ABOUTME: Test suite for AgentNoteEventData Pydantic schema model
# ABOUTME: Tests validation, serialization, and field requirements for agent note event data structure

"""Test suite for AgentNoteEventData schema model.

Tests the AgentNoteEventData Pydantic model that provides structured data
for agent note events. Validates field types, requirements, and serialization
for the following fields:
- agent_id (str, required)
- title (str, required)
- content (str, required)
- tags (list[str], required)
- related_file (str | None, optional)
- related_feature (str | None, optional)
"""

import pytest
from pydantic import ValidationError

# Import will fail until we implement the schema - that's expected in TDD
try:
    from jean_claude.core.events import AgentNoteEventData
except ImportError:
    # Allow tests to be written before implementation
    AgentNoteEventData = None


@pytest.mark.skipif(AgentNoteEventData is None, reason="AgentNoteEventData not implemented yet")
class TestAgentNoteEventData:
    """Test the AgentNoteEventData Pydantic model."""

    def test_creates_with_required_fields(self):
        """Test that AgentNoteEventData can be created with all required fields."""
        data = AgentNoteEventData(
            agent_id="agent-123",
            title="Test Note",
            content="This is a test note content",
            tags=["important", "test"]
        )

        assert data.agent_id == "agent-123"
        assert data.title == "Test Note"
        assert data.content == "This is a test note content"
        assert data.tags == ["important", "test"]
        assert data.related_file is None
        assert data.related_feature is None

    def test_creates_with_all_fields(self):
        """Test that AgentNoteEventData can be created with all fields including optional ones."""
        data = AgentNoteEventData(
            agent_id="agent-456",
            title="Implementation Note",
            content="Implemented the authentication feature",
            tags=["feature", "auth", "completed"],
            related_file="src/auth/login.py",
            related_feature="user-authentication"
        )

        assert data.agent_id == "agent-456"
        assert data.title == "Implementation Note"
        assert data.content == "Implemented the authentication feature"
        assert data.tags == ["feature", "auth", "completed"]
        assert data.related_file == "src/auth/login.py"
        assert data.related_feature == "user-authentication"

    def test_agent_id_is_required(self):
        """Test that agent_id field is required."""
        with pytest.raises(ValidationError) as exc_info:
            AgentNoteEventData(
                title="Test Note",
                content="Test content",
                tags=["test"]
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("agent_id",) and "missing" in error["type"] for error in errors)

    def test_title_is_required(self):
        """Test that title field is required."""
        with pytest.raises(ValidationError) as exc_info:
            AgentNoteEventData(
                agent_id="agent-123",
                content="Test content",
                tags=["test"]
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("title",) and "missing" in error["type"] for error in errors)

    def test_content_is_required(self):
        """Test that content field is required."""
        with pytest.raises(ValidationError) as exc_info:
            AgentNoteEventData(
                agent_id="agent-123",
                title="Test Note",
                tags=["test"]
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("content",) and "missing" in error["type"] for error in errors)

    def test_tags_is_required(self):
        """Test that tags field is required."""
        with pytest.raises(ValidationError) as exc_info:
            AgentNoteEventData(
                agent_id="agent-123",
                title="Test Note",
                content="Test content"
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("tags",) and "missing" in error["type"] for error in errors)

    def test_tags_must_be_list_of_strings(self):
        """Test that tags field must be a list of strings."""
        # Test with valid list of strings
        data = AgentNoteEventData(
            agent_id="agent-123",
            title="Test Note",
            content="Test content",
            tags=["tag1", "tag2", "tag3"]
        )
        assert data.tags == ["tag1", "tag2", "tag3"]

        # Test with empty list is allowed
        data = AgentNoteEventData(
            agent_id="agent-123",
            title="Test Note",
            content="Test content",
            tags=[]
        )
        assert data.tags == []

        # Test with invalid types
        with pytest.raises(ValidationError):
            AgentNoteEventData(
                agent_id="agent-123",
                title="Test Note",
                content="Test content",
                tags="invalid"  # Should be list, not string
            )

        with pytest.raises(ValidationError):
            AgentNoteEventData(
                agent_id="agent-123",
                title="Test Note",
                content="Test content",
                tags=[1, 2, 3]  # Should be strings, not ints
            )

    def test_related_file_is_optional_string_or_none(self):
        """Test that related_file field is optional and accepts string or None."""
        # Test with None (default)
        data = AgentNoteEventData(
            agent_id="agent-123",
            title="Test Note",
            content="Test content",
            tags=["test"]
        )
        assert data.related_file is None

        # Test with explicit None
        data = AgentNoteEventData(
            agent_id="agent-123",
            title="Test Note",
            content="Test content",
            tags=["test"],
            related_file=None
        )
        assert data.related_file is None

        # Test with string value
        data = AgentNoteEventData(
            agent_id="agent-123",
            title="Test Note",
            content="Test content",
            tags=["test"],
            related_file="src/main.py"
        )
        assert data.related_file == "src/main.py"

    def test_related_feature_is_optional_string_or_none(self):
        """Test that related_feature field is optional and accepts string or None."""
        # Test with None (default)
        data = AgentNoteEventData(
            agent_id="agent-123",
            title="Test Note",
            content="Test content",
            tags=["test"]
        )
        assert data.related_feature is None

        # Test with explicit None
        data = AgentNoteEventData(
            agent_id="agent-123",
            title="Test Note",
            content="Test content",
            tags=["test"],
            related_feature=None
        )
        assert data.related_feature is None

        # Test with string value
        data = AgentNoteEventData(
            agent_id="agent-123",
            title="Test Note",
            content="Test content",
            tags=["test"],
            related_feature="user-login"
        )
        assert data.related_feature == "user-login"

    def test_serialization_to_dict(self):
        """Test that AgentNoteEventData can be serialized to dict."""
        data = AgentNoteEventData(
            agent_id="agent-789",
            title="Serialization Test",
            content="Testing serialization functionality",
            tags=["serialization", "test"],
            related_file="tests/test_schema.py",
            related_feature="note-event-schema"
        )

        result = data.model_dump()
        expected = {
            "agent_id": "agent-789",
            "title": "Serialization Test",
            "content": "Testing serialization functionality",
            "tags": ["serialization", "test"],
            "related_file": "tests/test_schema.py",
            "related_feature": "note-event-schema"
        }

        assert result == expected

    def test_serialization_to_dict_with_none_optionals(self):
        """Test serialization with None values for optional fields."""
        data = AgentNoteEventData(
            agent_id="agent-101",
            title="None Test",
            content="Testing None values",
            tags=["none", "test"]
        )

        result = data.model_dump()
        expected = {
            "agent_id": "agent-101",
            "title": "None Test",
            "content": "Testing None values",
            "tags": ["none", "test"],
            "related_file": None,
            "related_feature": None
        }

        assert result == expected

    def test_json_serialization(self):
        """Test that AgentNoteEventData can be serialized to JSON."""
        data = AgentNoteEventData(
            agent_id="agent-999",
            title="JSON Test",
            content="Testing JSON serialization",
            tags=["json", "serialization"],
            related_file="config.json"
        )

        json_str = data.model_dump_json()

        # Should be valid JSON string
        import json
        parsed = json.loads(json_str)

        expected = {
            "agent_id": "agent-999",
            "title": "JSON Test",
            "content": "Testing JSON serialization",
            "tags": ["json", "serialization"],
            "related_file": "config.json",
            "related_feature": None
        }

        assert parsed == expected


class TestAgentNoteEventDataIntegration:
    """Test AgentNoteEventData integration with events system."""

    @pytest.mark.skipif(AgentNoteEventData is None, reason="AgentNoteEventData not implemented yet")
    def test_can_be_used_as_event_data(self):
        """Test that AgentNoteEventData can be used as data field in Event objects."""
        from jean_claude.core.events import Event, EventType

        note_data = AgentNoteEventData(
            agent_id="agent-integration",
            title="Integration Test Note",
            content="Testing integration with Event system",
            tags=["integration", "event", "test"],
            related_feature="note-event-data-schema"
        )

        # Should be able to use AgentNoteEventData as event data
        event = Event(
            workflow_id="test-workflow",
            event_type=EventType.AGENT_NOTE_OBSERVATION,
            data=note_data.model_dump()  # Convert to dict for Event.data field
        )

        assert event.event_type == EventType.AGENT_NOTE_OBSERVATION
        assert event.workflow_id == "test-workflow"
        assert event.data["agent_id"] == "agent-integration"
        assert event.data["title"] == "Integration Test Note"
        assert event.data["content"] == "Testing integration with Event system"
        assert event.data["tags"] == ["integration", "event", "test"]
        assert event.data["related_feature"] == "note-event-data-schema"
        assert event.data["related_file"] is None

    @pytest.mark.skipif(AgentNoteEventData is None, reason="AgentNoteEventData not implemented yet")
    def test_works_with_all_note_event_types(self):
        """Test that AgentNoteEventData can be used with all agent note event types."""
        from jean_claude.core.events import Event, EventType

        note_event_types = [
            EventType.AGENT_NOTE_OBSERVATION,
            EventType.AGENT_NOTE_LEARNING,
            EventType.AGENT_NOTE_DECISION,
            EventType.AGENT_NOTE_WARNING,
            EventType.AGENT_NOTE_ACCOMPLISHMENT,
            EventType.AGENT_NOTE_CONTEXT,
            EventType.AGENT_NOTE_TODO,
        ]

        for event_type in note_event_types:
            note_data = AgentNoteEventData(
                agent_id="agent-test",
                title=f"Test {event_type} Note",
                content=f"Testing {event_type} event type",
                tags=["test", event_type.split(".")[-1]]  # e.g., ["test", "observation"]
            )

            event = Event(
                workflow_id="test-workflow",
                event_type=event_type,
                data=note_data.model_dump()
            )

            assert event.event_type == event_type
            assert event.data["agent_id"] == "agent-test"
            assert event.data["title"] == f"Test {event_type} Note"
            assert event_type.split(".")[-1] in event.data["tags"]