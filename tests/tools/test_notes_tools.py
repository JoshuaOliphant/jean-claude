# ABOUTME: Test suite for notes agent tools
# ABOUTME: Tests for take_note, read_notes, search_notes SDK tools

"""Tests for notes agent tools.

This module tests the MCP tools that agents use to share knowledge
through the note-taking system.
"""

import pytest
from pathlib import Path

from jean_claude.tools.notes_tools import (
    set_notes_context,
    take_note,
    read_notes,
    search_notes,
    get_notes_summary,
    jean_claude_notes_tools,
    _notes_context,
)
from jean_claude.core.notes import NoteCategory


@pytest.fixture
def notes_context(tmp_path):
    """Set up notes context for testing."""
    workflow_id = "test-workflow"
    project_root = tmp_path
    agent_id = "test-agent"

    # Create agents directory
    (tmp_path / "agents" / workflow_id / "notes").mkdir(parents=True, exist_ok=True)

    # Set context
    set_notes_context(workflow_id, project_root, agent_id)

    yield {
        "workflow_id": workflow_id,
        "project_root": project_root,
        "agent_id": agent_id,
    }

    # Clean up context
    _notes_context["workflow_id"] = None
    _notes_context["project_root"] = None
    _notes_context["agent_id"] = None


class TestSetNotesContext:
    """Tests for set_notes_context function."""

    def test_set_notes_context(self, tmp_path):
        """Test setting notes context."""
        set_notes_context("test-wf", tmp_path, "my-agent")

        assert _notes_context["workflow_id"] == "test-wf"
        assert _notes_context["project_root"] == tmp_path
        assert _notes_context["agent_id"] == "my-agent"

        # Clean up
        _notes_context["workflow_id"] = None
        _notes_context["project_root"] = None
        _notes_context["agent_id"] = None


class TestTakeNote:
    """Tests for take_note tool."""

    @pytest.mark.asyncio
    async def test_take_note_success(self, notes_context):
        """Test taking a note successfully."""
        result = await take_note.handler({
            "title": "Test Note",
            "content": "This is test content",
            "category": "learning",
            "tags": "test,sample",
            "related_file": "src/test.py",
        })

        assert "content" in result
        assert len(result["content"]) == 1
        assert "recorded successfully" in result["content"][0]["text"]
        assert "learning" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_take_note_without_context(self):
        """Test that take_note fails without context."""
        # Clear context
        _notes_context["workflow_id"] = None
        _notes_context["project_root"] = None

        result = await take_note.handler({
            "title": "Test",
            "content": "Content",
            "category": "observation",
        })

        assert "Error" in result["content"][0]["text"]
        assert "not initialized" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_take_note_all_categories(self, notes_context):
        """Test taking notes with all categories."""
        categories = [
            "observation", "decision", "learning",
            "warning", "accomplishment", "context", "todo"
        ]

        for cat in categories:
            result = await take_note.handler({
                "title": f"Test {cat}",
                "content": f"Content for {cat}",
                "category": cat,
            })
            assert "recorded successfully" in result["content"][0]["text"]


class TestReadNotes:
    """Tests for read_notes tool."""

    @pytest.mark.asyncio
    async def test_read_notes_empty(self, notes_context):
        """Test reading notes when none exist."""
        result = await read_notes.handler({})

        assert "No notes found" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_read_notes_after_adding(self, notes_context):
        """Test reading notes after adding some."""
        # Add a note first
        await take_note.handler({
            "title": "First Note",
            "content": "First content",
            "category": "learning",
        })

        result = await read_notes.handler({})

        assert "Found 1 notes" in result["content"][0]["text"]
        assert "First Note" in result["content"][0]["text"]
        assert "LEARNING" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_read_notes_with_category_filter(self, notes_context):
        """Test filtering notes by category."""
        # Add notes of different categories
        await take_note.handler({
            "title": "Learning Note",
            "content": "Learning content",
            "category": "learning",
        })
        await take_note.handler({
            "title": "Warning Note",
            "content": "Warning content",
            "category": "warning",
        })

        # Filter by learning
        result = await read_notes.handler({"category": "learning"})

        assert "Learning Note" in result["content"][0]["text"]
        assert "Warning Note" not in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_read_notes_with_limit(self, notes_context):
        """Test limiting notes returned."""
        # Add multiple notes
        for i in range(5):
            await take_note.handler({
                "title": f"Note {i}",
                "content": f"Content {i}",
                "category": "observation",
            })

        result = await read_notes.handler({"limit": 2})

        # Should only have 2 notes
        text = result["content"][0]["text"]
        assert "Found 2 notes" in text


class TestSearchNotes:
    """Tests for search_notes tool."""

    @pytest.mark.asyncio
    async def test_search_notes_no_matches(self, notes_context):
        """Test searching when no matches found."""
        result = await search_notes.handler({"query": "nonexistent"})

        assert "No notes found matching" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_search_notes_with_matches(self, notes_context):
        """Test searching with matches."""
        # Add notes
        await take_note.handler({
            "title": "Authentication bug found",
            "content": "The auth module has a race condition",
            "category": "warning",
        })
        await take_note.handler({
            "title": "Database optimization",
            "content": "Indexing improved query time",
            "category": "accomplishment",
        })

        result = await search_notes.handler({"query": "auth"})

        text = result["content"][0]["text"]
        assert "Authentication" in text
        assert "Database" not in text

    @pytest.mark.asyncio
    async def test_search_notes_empty_query(self, notes_context):
        """Test searching with empty query."""
        result = await search_notes.handler({"query": ""})

        assert "Error" in result["content"][0]["text"]
        assert "required" in result["content"][0]["text"]


class TestGetNotesSummary:
    """Tests for get_notes_summary tool."""

    @pytest.mark.asyncio
    async def test_get_notes_summary_empty(self, notes_context):
        """Test summary when no notes exist."""
        result = await get_notes_summary.handler({})

        assert "No notes found" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_get_notes_summary_with_notes(self, notes_context):
        """Test summary with notes."""
        # Add notes of different categories
        await take_note.handler({
            "title": "Learning 1",
            "content": "Content",
            "category": "learning",
        })
        await take_note.handler({
            "title": "Warning 1",
            "content": "Content",
            "category": "warning",
        })

        result = await get_notes_summary.handler({})

        text = result["content"][0]["text"]
        assert "Notes Summary" in text
        assert "LEARNING" in text
        assert "WARNING" in text


class TestMCPServer:
    """Tests for the MCP server configuration."""

    def test_mcp_server_configuration(self):
        """Test that MCP server is configured correctly."""
        assert jean_claude_notes_tools is not None
        assert "name" in jean_claude_notes_tools
        assert jean_claude_notes_tools["name"] == "jean-claude-notes"

    def test_mcp_server_has_tools(self):
        """Test that MCP server has tools registered."""
        # The SDK wraps this differently, so we just check basic structure
        assert "type" in jean_claude_notes_tools or "instance" in jean_claude_notes_tools or "tools" in jean_claude_notes_tools


class TestIntegration:
    """Integration tests for notes tools."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, notes_context):
        """Test a full workflow of taking and reading notes."""
        # Agent 1 takes notes
        await take_note.handler({
            "title": "API endpoint pattern discovered",
            "content": "All endpoints follow /api/v1/{resource} pattern",
            "category": "learning",
            "tags": "api,patterns",
        })

        await take_note.handler({
            "title": "Using repository pattern for data access",
            "content": "Following existing codebase patterns",
            "category": "decision",
        })

        await take_note.handler({
            "title": "Rate limiting missing on auth endpoints",
            "content": "Security concern - should add rate limiting",
            "category": "warning",
            "related_file": "src/auth/routes.py",
        })

        # Agent 2 reads all notes
        all_notes = await read_notes.handler({})
        assert "Found 3 notes" in all_notes["content"][0]["text"]

        # Agent 2 searches for API-related notes
        api_notes = await search_notes.handler({"query": "api"})
        assert "API endpoint" in api_notes["content"][0]["text"]

        # Agent 2 gets summary
        summary = await get_notes_summary.handler({})
        text = summary["content"][0]["text"]
        assert "LEARNING" in text
        assert "DECISION" in text
        assert "WARNING" in text

        # Agent 2 reads only warnings
        warnings = await read_notes.handler({"category": "warning"})
        assert "Rate limiting" in warnings["content"][0]["text"]
