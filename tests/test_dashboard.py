# ABOUTME: Test suite for the jc dashboard web UI
# ABOUTME: Tests FastAPI endpoints, SSE streaming, and HTML rendering

"""Tests for jc dashboard web UI.

This module tests:
- FastAPI app initialization and routes
- API endpoints for workflow status and events
- SSE streaming for real-time logs
- HTML template rendering
- CLI command for starting the server
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient

from jean_claude.cli.main import cli


class TestDashboardCLI:
    """Tests for jc dashboard CLI command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    def test_dashboard_help_shows_usage(self, runner):
        """Test that --help shows command usage."""
        result = runner.invoke(cli, ["dashboard", "--help"])

        assert result.exit_code == 0
        assert "dashboard" in result.output.lower()
        assert "--port" in result.output

    def test_dashboard_has_port_option(self, runner):
        """Test that --port option exists."""
        result = runner.invoke(cli, ["dashboard", "--help"])

        assert "--port" in result.output
        assert "8765" in result.output or "port" in result.output.lower()

    def test_dashboard_has_host_option(self, runner):
        """Test that --host option exists."""
        result = runner.invoke(cli, ["dashboard", "--help"])

        assert "--host" in result.output


class TestDashboardApp:
    """Tests for FastAPI dashboard app."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with workflow data."""
        # Create agents directory with workflow
        workflow_dir = tmp_path / "agents" / "test-workflow-123"
        workflow_dir.mkdir(parents=True)

        # Create state.json
        state = {
            "workflow_id": "test-workflow-123",
            "workflow_name": "Test Workflow",
            "workflow_type": "feature",
            "phase": "implementing",
            "beads_task_id": "poc-xyz",
            "beads_task_title": "Add user authentication",
            "features": [
                {"name": "Create User model", "status": "completed", "description": "User model"},
                {"name": "Add login endpoint", "status": "in_progress", "description": "Login API"},
                {"name": "Add JWT middleware", "status": "not_started", "description": "Auth middleware"},
            ],
            "created_at": "2025-01-15T12:00:00",
            "updated_at": "2025-01-15T12:30:00",
            "total_duration_ms": 1800000,
            "total_cost_usd": 0.42,
        }
        with open(workflow_dir / "state.json", 'w') as f:
            json.dump(state, f)

        # Create events.jsonl
        events = [
            {
                "id": "evt-1",
                "timestamp": "2025-01-15T12:00:00",
                "workflow_id": "test-workflow-123",
                "event_type": "workflow.started",
                "data": {"beads_task": "poc-xyz"}
            },
            {
                "id": "evt-2",
                "timestamp": "2025-01-15T12:15:00",
                "workflow_id": "test-workflow-123",
                "event_type": "feature.completed",
                "data": {"feature_name": "Create User model"}
            },
        ]
        with open(workflow_dir / "events.jsonl", 'w') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')

        return tmp_path

    @pytest.fixture
    def client(self, temp_project):
        """Create a test client for the FastAPI app."""
        from jean_claude.dashboard.app import create_app

        app = create_app(project_root=temp_project)
        return TestClient(app)

    def test_root_returns_html(self, client):
        """Test that / returns HTML dashboard."""
        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_root_contains_dashboard_elements(self, client):
        """Test that dashboard HTML has key elements."""
        response = client.get("/")

        assert response.status_code == 200
        html = response.text

        # Should have key dashboard elements
        assert "dashboard" in html.lower() or "workflow" in html.lower()

    def test_api_workflows_returns_list(self, client):
        """Test that /api/workflows returns workflow list."""
        response = client.get("/api/workflows")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["workflow_id"] == "test-workflow-123"

    def test_api_status_returns_workflow_state(self, client):
        """Test that /api/status/{id} returns workflow state."""
        response = client.get("/api/status/test-workflow-123")

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_id"] == "test-workflow-123"
        assert data["phase"] == "implementing"
        assert len(data["features"]) == 3

    def test_api_status_not_found(self, client):
        """Test that /api/status/{id} returns 404 for unknown workflow."""
        response = client.get("/api/status/nonexistent")

        assert response.status_code == 404

    def test_api_events_returns_events(self, client):
        """Test that /api/events/{id} returns events list."""
        response = client.get("/api/events/test-workflow-123")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["event_type"] == "workflow.started"

    def test_api_events_not_found(self, client):
        """Test that /api/events/{id} returns 404 for unknown workflow."""
        response = client.get("/api/events/nonexistent")

        assert response.status_code == 404


class TestDashboardSSE:
    """Tests for Server-Sent Events streaming."""

    def test_sse_endpoint_returns_404_for_missing_workflow(self, tmp_path):
        """Test that /api/events/{id}/stream returns 404 for nonexistent workflow."""
        from jean_claude.dashboard.app import create_app

        # Create empty project
        (tmp_path / "agents").mkdir(parents=True)

        app = create_app(project_root=tmp_path)
        client = TestClient(app)

        response = client.get("/api/events/nonexistent/stream")
        assert response.status_code == 404


class TestDashboardTemplates:
    """Tests for Jinja2 template rendering."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with workflow data."""
        workflow_dir = tmp_path / "agents" / "template-test"
        workflow_dir.mkdir(parents=True)

        state = {
            "workflow_id": "template-test",
            "workflow_name": "Template Test",
            "workflow_type": "feature",
            "phase": "implementing",
            "beads_task_id": "poc-tpl",
            "beads_task_title": "Test Template Rendering",
            "features": [
                {"name": "Feature A", "status": "completed", "description": "Done"},
                {"name": "Feature B", "status": "in_progress", "description": "Working"},
            ],
            "created_at": "2025-01-15T12:00:00",
            "updated_at": "2025-01-15T12:30:00",
            "total_duration_ms": 600000,
            "total_cost_usd": 0.15,
        }
        with open(workflow_dir / "state.json", 'w') as f:
            json.dump(state, f)

        with open(workflow_dir / "events.jsonl", 'w') as f:
            f.write('{"id": "1", "timestamp": "2025-01-15T12:00:00", "workflow_id": "template-test", "event_type": "workflow.started", "data": {}}\n')

        return tmp_path

    @pytest.fixture
    def client(self, temp_project):
        """Create a test client for the FastAPI app."""
        from jean_claude.dashboard.app import create_app

        app = create_app(project_root=temp_project)
        return TestClient(app)

    def test_dashboard_shows_workflow_title(self, client):
        """Test that dashboard shows workflow title."""
        response = client.get("/?workflow=template-test")

        assert response.status_code == 200
        # Should contain workflow info
        assert "template-test" in response.text.lower() or "Template Test" in response.text

    def test_dashboard_shows_features(self, client):
        """Test that dashboard shows feature list."""
        response = client.get("/?workflow=template-test")

        assert response.status_code == 200
        # Should show features
        assert "Feature A" in response.text or "feature" in response.text.lower()

    def test_dashboard_includes_htmx(self, client):
        """Test that dashboard includes HTMX script."""
        response = client.get("/")

        assert response.status_code == 200
        assert "htmx" in response.text.lower()

    def test_dashboard_includes_tailwind(self, client):
        """Test that dashboard includes Tailwind CSS."""
        response = client.get("/")

        assert response.status_code == 200
        assert "tailwind" in response.text.lower()


class TestDashboardWorkflowView:
    """Tests for specific workflow view."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create project with multiple workflows."""
        for i, name in enumerate(["workflow-a", "workflow-b"]):
            workflow_dir = tmp_path / "agents" / name
            workflow_dir.mkdir(parents=True)

            state = {
                "workflow_id": name,
                "workflow_name": f"Workflow {name.upper()}",
                "phase": "completed" if i == 0 else "implementing",
                "features": [],
                "created_at": "2025-01-15T12:00:00",
                "updated_at": "2025-01-15T12:30:00",
            }
            with open(workflow_dir / "state.json", 'w') as f:
                json.dump(state, f)

            with open(workflow_dir / "events.jsonl", 'w') as f:
                f.write(f'{{"id": "1", "timestamp": "2025-01-15T12:00:00", "workflow_id": "{name}", "event_type": "workflow.started", "data": {{}}}}\n')

        return tmp_path

    @pytest.fixture
    def client(self, temp_project):
        """Create a test client for the FastAPI app."""
        from jean_claude.dashboard.app import create_app

        app = create_app(project_root=temp_project)
        return TestClient(app)

    def test_workflow_selector_shows_all_workflows(self, client):
        """Test that workflow selector shows all available workflows."""
        response = client.get("/api/workflows")

        assert response.status_code == 200
        data = response.json()
        workflow_ids = [w["workflow_id"] for w in data]
        assert "workflow-a" in workflow_ids
        assert "workflow-b" in workflow_ids

    def test_can_view_specific_workflow(self, client):
        """Test that ?workflow= parameter selects specific workflow."""
        response = client.get("/?workflow=workflow-b")

        assert response.status_code == 200
        assert "workflow-b" in response.text.lower() or "Workflow B" in response.text
