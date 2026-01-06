# ABOUTME: Dashboard API tests for notes endpoints
# ABOUTME: Tests /api/notes and /partials/notes endpoints with FastAPI TestClient

"""Dashboard API tests for notes endpoints.

This test module validates the dashboard API endpoints for querying and
displaying agent notes from the event store.

Test Coverage:
- /api/notes/{workflow_id} JSON endpoint
- /api/notes/{workflow_id}?category=X filtering
- /partials/notes/{workflow_id} HTML partial
- Category tab filtering
- Empty state handling
"""

import pytest
import sqlite3
import json
from pathlib import Path
from fastapi.testclient import TestClient

from jean_claude.dashboard.app import create_app
from jean_claude.core.events import EventLogger


@pytest.fixture
def sample_workflow_with_notes(tmp_path):
    """Create test workflow with note events in event store."""
    workflow_id = "test-workflow"

    # Create events.db with notes
    event_logger = EventLogger(tmp_path)

    # Emit various note types
    event_logger.emit(
        workflow_id=workflow_id,
        event_type="agent.note.observation",
        data={
            "agent_id": "agent-1",
            "title": "Test Observation",
            "content": "Observation content",
            "category": "observation",
            "tags": ["test"],
        }
    )

    event_logger.emit(
        workflow_id=workflow_id,
        event_type="agent.note.warning",
        data={
            "agent_id": "agent-2",
            "title": "Test Warning",
            "content": "Warning content",
            "category": "warning",
            "tags": ["test"],
        }
    )

    event_logger.emit(
        workflow_id=workflow_id,
        event_type="agent.note.accomplishment",
        data={
            "agent_id": "agent-3",
            "title": "Test Accomplishment",
            "content": "Accomplishment content",
            "category": "accomplishment",
            "tags": ["test"],
        }
    )

    return {"workflow_id": workflow_id, "project_root": tmp_path}


@pytest.fixture
def client(tmp_path):
    """Create FastAPI test client with temporary project root."""
    app = create_app(project_root=tmp_path)
    return TestClient(app)


class TestApiNotesEndpoint:
    """Test /api/notes/{workflow_id} JSON API."""

    def test_api_notes_returns_all_notes(self, client, sample_workflow_with_notes, monkeypatch):
        """API returns all notes when no category filter specified."""
        monkeypatch.chdir(sample_workflow_with_notes["project_root"])

        # Recreate client with correct project_root
        app = create_app(project_root=sample_workflow_with_notes["project_root"])
        client = TestClient(app)

        response = client.get(f"/api/notes/{sample_workflow_with_notes['workflow_id']}")

        assert response.status_code == 200
        notes = response.json()
        assert len(notes) == 3
        assert any(n["title"] == "Test Observation" for n in notes)
        assert any(n["title"] == "Test Warning" for n in notes)
        assert any(n["title"] == "Test Accomplishment" for n in notes)

    def test_api_notes_filters_by_category(self, client, sample_workflow_with_notes, monkeypatch):
        """API filters notes by category when specified."""
        monkeypatch.chdir(sample_workflow_with_notes["project_root"])

        app = create_app(project_root=sample_workflow_with_notes["project_root"])
        client = TestClient(app)

        response = client.get(
            f"/api/notes/{sample_workflow_with_notes['workflow_id']}?category=warning"
        )

        assert response.status_code == 200
        notes = response.json()
        assert len(notes) == 1
        assert notes[0]["title"] == "Test Warning"
        assert notes[0]["category"] == "warning"

    def test_api_notes_empty_when_no_events_db(self, tmp_path):
        """API returns empty array when events.db doesn't exist."""
        app = create_app(project_root=tmp_path)
        client = TestClient(app)

        response = client.get("/api/notes/nonexistent-workflow")

        assert response.status_code == 200
        assert response.json() == []

    def test_api_notes_limits_to_50(self, tmp_path):
        """API limits results to 50 most recent notes."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)

        # Create 60 notes
        for i in range(60):
            event_logger.emit(
                workflow_id=workflow_id,
                event_type="agent.note.observation",
                data={
                    "agent_id": f"agent-{i}",
                    "title": f"Note {i}",
                    "content": f"Content {i}",
                    "category": "observation",
                    "tags": [],
                }
            )

        app = create_app(project_root=tmp_path)
        client = TestClient(app)

        response = client.get(f"/api/notes/{workflow_id}")

        assert response.status_code == 200
        notes = response.json()
        assert len(notes) == 50, "Should limit to 50 notes"
        # Most recent first
        assert notes[0]["title"] == "Note 59"


class TestPartialNotesEndpoint:
    """Test /partials/notes/{workflow_id} HTML partial."""

    def test_partial_notes_renders_html(self, sample_workflow_with_notes):
        """Partial renders HTML with notes."""
        app = create_app(project_root=sample_workflow_with_notes["project_root"])
        client = TestClient(app)

        response = client.get(f"/partials/notes/{sample_workflow_with_notes['workflow_id']}")

        assert response.status_code == 200
        assert b"Test Observation" in response.content
        assert b"Test Warning" in response.content
        assert b"Test Accomplishment" in response.content

    def test_partial_notes_shows_category_tabs(self, sample_workflow_with_notes):
        """Partial includes category tab buttons."""
        app = create_app(project_root=sample_workflow_with_notes["project_root"])
        client = TestClient(app)

        response = client.get(f"/partials/notes/{sample_workflow_with_notes['workflow_id']}")

        assert response.status_code == 200
        # Check for tab buttons
        assert b"All" in response.content
        assert b"Observation" in response.content
        assert b"Warning" in response.content
        assert b"Accomplishment" in response.content

    def test_partial_notes_filters_by_category(self, sample_workflow_with_notes):
        """Partial filters notes when category specified."""
        app = create_app(project_root=sample_workflow_with_notes["project_root"])
        client = TestClient(app)

        response = client.get(
            f"/partials/notes/{sample_workflow_with_notes['workflow_id']}?category=warning"
        )

        assert response.status_code == 200
        assert b"Test Warning" in response.content
        # Should not show other categories
        assert b"Test Observation" not in response.content

    def test_partial_notes_shows_empty_state(self, tmp_path):
        """Partial shows 'No notes yet' when no notes exist."""
        app = create_app(project_root=tmp_path)
        client = TestClient(app)

        response = client.get("/partials/notes/nonexistent-workflow")

        assert response.status_code == 200
        assert b"No notes yet" in response.content

    def test_partial_notes_includes_emojis(self, sample_workflow_with_notes):
        """Partial includes emoji indicators for note categories."""
        app = create_app(project_root=sample_workflow_with_notes["project_root"])
        client = TestClient(app)

        response = client.get(f"/partials/notes/{sample_workflow_with_notes['workflow_id']}")

        assert response.status_code == 200
        # Check for category emojis
        content = response.content.decode('utf-8')
        assert "👁️" in content  # observation
        assert "⚠️" in content  # warning
        assert "✅" in content  # accomplishment


class TestNotesIntegration:
    """Integration tests for complete notes flow."""

    def test_notes_with_tags_and_metadata(self, tmp_path):
        """Notes with tags and related_file render correctly."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)

        event_logger.emit(
            workflow_id=workflow_id,
            event_type="agent.note.decision",
            data={
                "agent_id": "planner-agent",
                "title": "Architecture Decision",
                "content": "Use SQLite for event storage",
                "category": "decision",
                "tags": ["architecture", "database"],
                "related_file": "src/core/events.py",
            }
        )

        app = create_app(project_root=tmp_path)
        client = TestClient(app)

        response = client.get(f"/partials/notes/{workflow_id}")

        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert "Architecture Decision" in content
        assert "architecture" in content
        assert "database" in content
        assert "src/core/events.py" in content

    def test_category_counts_in_tabs(self, tmp_path):
        """Category tabs show correct note counts."""
        workflow_id = "test-workflow"
        event_logger = EventLogger(tmp_path)

        # Create 3 warnings, 2 observations
        for i in range(3):
            event_logger.emit(
                workflow_id=workflow_id,
                event_type="agent.note.warning",
                data={
                    "agent_id": "agent",
                    "title": f"Warning {i}",
                    "content": "Content",
                    "category": "warning",
                    "tags": [],
                }
            )

        for i in range(2):
            event_logger.emit(
                workflow_id=workflow_id,
                event_type="agent.note.observation",
                data={
                    "agent_id": "agent",
                    "title": f"Observation {i}",
                    "content": "Content",
                    "category": "observation",
                    "tags": [],
                }
            )

        app = create_app(project_root=tmp_path)
        client = TestClient(app)

        response = client.get(f"/partials/notes/{workflow_id}")

        content = response.content.decode('utf-8')
        # Check tab counts
        assert "All (5)" in content
        assert "Warning (3)" in content
        assert "Observation (2)" in content
