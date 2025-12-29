# ABOUTME: Tests for dashboard app refactoring to use workflow_utils.get_all_workflows
# ABOUTME: Tests the specific refactoring from duplicate workflow iteration pattern to utility function

"""Tests for dashboard/app.py refactoring to use workflow_utils.get_all_workflows.

This module tests the specific refactoring from lines 47-72 to use the centralized
workflow utility instead of duplicating the workflow iteration pattern.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, Mock

import pytest
from fastapi.testclient import TestClient

from jean_claude.core.state import WorkflowState
from jean_claude.dashboard.app import create_app


class TestDashboardAppRefactoring:
    """Tests for dashboard app get_all_workflows refactoring."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with workflow data."""
        # Create agents directory with multiple workflows
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Create workflow 1 (older)
        workflow1_dir = agents_dir / "test-workflow-1"
        workflow1_dir.mkdir()
        state1 = {
            "workflow_id": "test-workflow-1",
            "workflow_name": "Test Workflow 1",
            "workflow_type": "feature",
            "phase": "implementing",
            "beads_task_id": "task-1",
            "beads_task_title": "Add feature 1",
            "features": [
                {"name": "Feature 1A", "status": "completed", "description": "Done"},
            ],
            "created_at": "2025-01-15T12:00:00",
            "updated_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "total_duration_ms": 1800000,
            "total_cost_usd": 0.42,
        }
        with open(workflow1_dir / "state.json", 'w') as f:
            json.dump(state1, f)

        # Create workflow 2 (newer)
        workflow2_dir = agents_dir / "test-workflow-2"
        workflow2_dir.mkdir()
        state2 = {
            "workflow_id": "test-workflow-2",
            "workflow_name": "Test Workflow 2",
            "workflow_type": "bug",
            "phase": "complete",
            "beads_task_id": "task-2",
            "beads_task_title": "Fix bug 2",
            "features": [
                {"name": "Feature 2A", "status": "completed", "description": "Fixed"},
                {"name": "Feature 2B", "status": "in_progress", "description": "Working"},
            ],
            "created_at": "2025-01-15T14:00:00",
            "updated_at": datetime.now().isoformat(),
            "total_duration_ms": 3600000,
            "total_cost_usd": 0.85,
        }
        with open(workflow2_dir / "state.json", 'w') as f:
            json.dump(state2, f)

        # Create workflow 3 with corrupted state.json (should be skipped)
        workflow3_dir = agents_dir / "test-workflow-3"
        workflow3_dir.mkdir()
        with open(workflow3_dir / "state.json", 'w') as f:
            f.write("invalid json {{{")

        return tmp_path

    @pytest.fixture
    def client(self, temp_project):
        """Create a test client for the FastAPI app."""
        app = create_app(project_root=temp_project)
        return TestClient(app)

    def test_api_workflows_returns_sorted_dict_list(self, client):
        """Test that /api/workflows returns workflows as dict list sorted by updated_at desc."""
        response = client.get("/api/workflows")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2  # Should skip corrupted workflow

        # Should be sorted by updated_at descending (most recent first)
        assert data[0]["workflow_id"] == "test-workflow-2"
        assert data[1]["workflow_id"] == "test-workflow-1"

        # Check that all expected fields are present
        for workflow in data:
            assert "workflow_id" in workflow
            assert "workflow_name" in workflow
            assert "workflow_type" in workflow
            assert "phase" in workflow
            assert "updated_at" in workflow
            assert "features" in workflow

    def test_dashboard_uses_refactored_get_all_workflows(self, client):
        """Test that dashboard page uses refactored get_all_workflows function."""
        response = client.get("/")

        assert response.status_code == 200
        html = response.text

        # Should contain workflow information from most recent workflow (test-workflow-2)
        assert "test-workflow-2" in html.lower() or "Test Workflow 2" in html

    def test_get_all_workflows_handles_missing_agents_dir(self, tmp_path):
        """Test that get_all_workflows handles missing agents directory gracefully."""
        # Create app with project root that has no agents directory
        app = create_app(project_root=tmp_path)
        client = TestClient(app)

        response = client.get("/api/workflows")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_all_workflows_handles_empty_agents_dir(self, tmp_path):
        """Test that get_all_workflows handles empty agents directory gracefully."""
        # Create empty agents directory
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        app = create_app(project_root=tmp_path)
        client = TestClient(app)

        response = client.get("/api/workflows")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch('jean_claude.dashboard.app.get_all_workflow_states')
    def test_dashboard_app_calls_workflow_utils_function(self, mock_get_all_workflow_states, tmp_path):
        """Test that dashboard app calls the workflow_utils.get_all_workflows function."""
        # Mock the workflow_utils function to return WorkflowState objects
        mock_workflow1 = Mock()
        mock_workflow1.model_dump.return_value = {
            "workflow_id": "mock-1",
            "workflow_name": "Mock 1",
            "updated_at": datetime.now().isoformat(),
        }
        mock_workflow2 = Mock()
        mock_workflow2.model_dump.return_value = {
            "workflow_id": "mock-2",
            "workflow_name": "Mock 2",
            "updated_at": (datetime.now() - timedelta(hours=1)).isoformat(),
        }
        mock_get_all_workflow_states.return_value = [mock_workflow1, mock_workflow2]

        app = create_app(project_root=tmp_path)
        client = TestClient(app)

        response = client.get("/api/workflows")

        assert response.status_code == 200
        # Verify the workflow_utils function was called with correct project_root
        mock_get_all_workflow_states.assert_called_once_with(tmp_path)

        # Verify the response contains the mocked data converted to dicts
        data = response.json()
        assert len(data) == 2
        assert data[0]["workflow_id"] == "mock-1"
        assert data[1]["workflow_id"] == "mock-2"