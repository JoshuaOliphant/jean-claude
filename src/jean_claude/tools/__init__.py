# ABOUTME: Tools module for Jean Claude Agent SDK tool integrations
# ABOUTME: Provides MCP tools that agents can use to interact with workflow features

"""Jean Claude Agent SDK Tools.

This module provides MCP (Model Context Protocol) tools that agents can use
to interact with Jean Claude workflow features, following the Agent SDK pattern.

Tools are exposed to agents with the format: mcp__{server-name}__{tool-name}

Available tool servers:
- mailbox_tools: Communication tools for agent-user interaction
- notes_tools: Shared note-taking tools for knowledge sharing between agents
"""

from jean_claude.tools.mailbox_tools import jean_claude_mailbox_tools
from jean_claude.tools.notes_tools import (
    jean_claude_notes_tools,
    set_notes_context,
)

__all__ = [
    "jean_claude_mailbox_tools",
    "jean_claude_notes_tools",
    "set_notes_context",
]
