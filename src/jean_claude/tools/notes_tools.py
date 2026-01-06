# ABOUTME: Notes Agent SDK tools for shared knowledge between agents
# ABOUTME: Provides tools for agents to take notes and read notes from other agents

"""Notes Agent SDK tools for shared knowledge between agents.

This module provides MCP tools that agents can use to share knowledge
through the note-taking system. Agents can record observations, decisions,
learnings, and other information that should be accessible to other agents
working on the same workflow.

Tools provided:
- take_note: Record a note for other agents to see
- read_notes: Read notes from the shared notes file
- search_notes: Search notes by content

Example usage in agent execution:
    from jean_claude.tools.notes_tools import jean_claude_notes_tools

    result = await execute_agent(
        prompt="Implement feature...",
        options=ClaudeAgentOptions(
            mcp_servers={"notes": jean_claude_notes_tools},
            allowed_tools=[
                "mcp__jean-claude-notes__take_note",
                "mcp__jean-claude-notes__read_notes"
            ]
        )
    )
"""

from pathlib import Path
from typing import Any

try:
    from claude_agent_sdk import create_sdk_mcp_server, tool
except ImportError:
    # Fallback for testing without Agent SDK installed
    def tool(name, description, schema):
        def decorator(func):
            func.__tool_name__ = name
            func.__tool_description__ = description
            func.__tool_schema__ = schema
            return func
        return decorator

    def create_sdk_mcp_server(name, version, tools):
        return {"name": name, "version": version, "tools": tools}

from jean_claude.core.notes import NoteCategory
from jean_claude.core.notes_api import Notes

# Global state (will be injected by workflow)
_notes_context: dict[str, Any] = {
    "workflow_id": None,
    "project_root": None,
    "agent_id": None,
    "event_logger": None,
}


def set_notes_context(
    workflow_id: str,
    project_root: Path,
    agent_id: str = "agent",
    event_logger: Any = None,
) -> None:
    """Set the current notes context for notes tools.

    This must be called before agents can use notes tools.

    Args:
        workflow_id: The workflow ID for notes storage
        project_root: Path to the project root directory
        agent_id: Identifier for the agent taking notes
        event_logger: Optional EventLogger for event emission
    """
    _notes_context["workflow_id"] = workflow_id
    _notes_context["project_root"] = project_root
    _notes_context["agent_id"] = agent_id
    _notes_context["event_logger"] = event_logger


def get_notes_api() -> Notes | None:
    """Get the Notes API instance for the current context.

    Returns:
        Notes API instance or None if context not set
    """
    workflow_id = _notes_context.get("workflow_id")
    project_root = _notes_context.get("project_root")
    event_logger = _notes_context.get("event_logger")

    if not workflow_id or not project_root or not event_logger:
        return None

    return Notes(
        workflow_id=workflow_id,
        project_root=project_root,
        event_logger=event_logger
    )


@tool(
    "take_note",
    "Record a note for other agents working on this workflow. Use this to share observations, decisions, learnings, warnings, or accomplishments that other agents should know about.",
    {
        "title": str,
        "content": str,
        "category": str,  # observation, decision, learning, warning, accomplishment, context, todo
        "tags": str,  # comma-separated tags (optional)
        "related_file": str,  # optional file path
    }
)
async def take_note(args: dict[str, Any]) -> dict[str, Any]:
    """Record a note for other agents to see.

    This tool allows agents to share knowledge with other agents working on
    the same workflow. Notes persist across agent sessions and can be read
    by any agent with access to the workflow.

    Args:
        args: Dictionary containing:
            - title: Brief title for the note
            - content: Full content of the note
            - category: One of: observation, decision, learning, warning,
                       accomplishment, context, todo
            - tags: Comma-separated tags for categorization (optional)
            - related_file: Path to a related file (optional)

    Returns:
        Dictionary with confirmation or error message

    Example:
        Agent discovers a pattern in the codebase:
        >>> result = await take_note({
        ...     "title": "Auth module uses async/await pattern",
        ...     "content": "All auth methods return Promises. Use await when calling authenticate().",
        ...     "category": "learning",
        ...     "tags": "auth,patterns,async",
        ...     "related_file": "src/auth/handler.py"
        ... })
    """
    notes_api = get_notes_api()
    agent_id = _notes_context.get("agent_id", "agent")

    if not notes_api:
        return {
            "content": [{
                "type": "text",
                "text": "Error: Notes tools not initialized. set_notes_context() must be called first."
            }]
        }

    try:
        # Parse category
        category_map = {
            "observation": NoteCategory.OBSERVATION,
            "decision": NoteCategory.DECISION,
            "learning": NoteCategory.LEARNING,
            "warning": NoteCategory.WARNING,
            "accomplishment": NoteCategory.ACCOMPLISHMENT,
            "context": NoteCategory.CONTEXT,
            "todo": NoteCategory.TODO,
        }
        category_str = args.get("category", "observation").lower()
        category = category_map.get(category_str, NoteCategory.OBSERVATION)

        # Parse tags
        tags = []
        if args.get("tags"):
            tags = [t.strip() for t in args["tags"].split(",") if t.strip()]

        # Create note (event_logger is already in Notes constructor)
        note = notes_api.add(
            agent_id=agent_id,
            title=args["title"],
            content=args["content"],
            category=category,
            tags=tags,
            related_file=args.get("related_file"),
            related_feature=args.get("related_feature"),  # Fixed: was missing
        )

        return {
            "content": [{
                "type": "text",
                "text": f"Note recorded successfully. ID: {note.id[:8]}, Category: {category.value}"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error recording note: {str(e)}"
            }]
        }


@tool(
    "read_notes",
    "Read notes from other agents working on this workflow. Use this to see what other agents have learned, decided, or observed.",
    {
        "category": str,  # optional filter by category
        "limit": int,  # optional limit on number of notes
    }
)
async def read_notes(args: dict[str, Any]) -> dict[str, Any]:
    """Read notes from the shared notes file.

    This tool allows agents to see what other agents have recorded.
    Notes can be filtered by category and limited in number.

    Args:
        args: Dictionary containing:
            - category: Optional category filter (observation, decision, etc.)
            - limit: Optional maximum number of notes to return

    Returns:
        Dictionary with notes formatted for reading

    Example:
        Agent wants to see learnings from other agents:
        >>> result = await read_notes({
        ...     "category": "learning",
        ...     "limit": 5
        ... })
    """
    notes_api = get_notes_api()

    if not notes_api:
        return {
            "content": [{
                "type": "text",
                "text": "Error: Notes tools not initialized. set_notes_context() must be called first."
            }]
        }

    try:
        # Parse category filter
        category_filter = None
        if args.get("category"):
            category_map = {
                "observation": NoteCategory.OBSERVATION,
                "decision": NoteCategory.DECISION,
                "learning": NoteCategory.LEARNING,
                "warning": NoteCategory.WARNING,
                "accomplishment": NoteCategory.ACCOMPLISHMENT,
                "context": NoteCategory.CONTEXT,
                "todo": NoteCategory.TODO,
            }
            category_filter = category_map.get(args["category"].lower())

        # Get notes
        limit = args.get("limit")
        notes_list = notes_api.list(category=category_filter, limit=limit)

        if not notes_list:
            return {
                "content": [{
                    "type": "text",
                    "text": "No notes found."
                }]
            }

        # Format notes for display
        output_lines = [f"Found {len(notes_list)} notes:\n"]

        for note in notes_list:
            output_lines.append(f"## [{note.category.value.upper()}] {note.title}")
            output_lines.append(f"*Agent: {note.agent_id} | {note.created_at.strftime('%Y-%m-%d %H:%M')}*")
            if note.tags:
                output_lines.append(f"Tags: {', '.join(note.tags)}")
            if note.related_file:
                output_lines.append(f"File: {note.related_file}")
            output_lines.append("")
            output_lines.append(note.content)
            output_lines.append("\n---\n")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(output_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error reading notes: {str(e)}"
            }]
        }


@tool(
    "search_notes",
    "Search notes for specific keywords or topics. Use this to find relevant information from other agents.",
    {
        "query": str,  # search query
    }
)
async def search_notes(args: dict[str, Any]) -> dict[str, Any]:
    """Search notes by content.

    This tool allows agents to find relevant notes by searching
    for keywords in titles and content.

    Args:
        args: Dictionary containing:
            - query: The search query string

    Returns:
        Dictionary with matching notes

    Example:
        Agent wants to find notes about authentication:
        >>> result = await search_notes({
        ...     "query": "authentication"
        ... })
    """
    notes_api = get_notes_api()

    if not notes_api:
        return {
            "content": [{
                "type": "text",
                "text": "Error: Notes tools not initialized. set_notes_context() must be called first."
            }]
        }

    try:
        query = args.get("query", "")
        if not query:
            return {
                "content": [{
                    "type": "text",
                    "text": "Error: Search query is required."
                }]
            }

        results = notes_api.search(query)

        if not results:
            return {
                "content": [{
                    "type": "text",
                    "text": f"No notes found matching '{query}'."
                }]
            }

        # Format results for display
        output_lines = [f"Found {len(results)} notes matching '{query}':\n"]

        for note in results:
            output_lines.append(f"## [{note.category.value.upper()}] {note.title}")
            output_lines.append(f"*Agent: {note.agent_id}*")
            output_lines.append("")
            output_lines.append(note.content[:200] + ("..." if len(note.content) > 200 else ""))
            output_lines.append("\n---\n")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(output_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error searching notes: {str(e)}"
            }]
        }


@tool(
    "get_notes_summary",
    "Get a summary of all notes organized by category. Use this for a quick overview of shared knowledge.",
    {}
)
async def get_notes_summary(args: dict[str, Any]) -> dict[str, Any]:
    """Get a summary of all notes.

    This tool provides a quick overview of all notes organized
    by category, helping agents understand what knowledge has
    been shared.

    Args:
        args: Empty dictionary (no arguments needed)

    Returns:
        Dictionary with notes summary

    Example:
        >>> result = await get_notes_summary({})
    """
    notes_api = get_notes_api()

    if not notes_api:
        return {
            "content": [{
                "type": "text",
                "text": "Error: Notes tools not initialized. set_notes_context() must be called first."
            }]
        }

    try:
        summary = notes_api.get_summary()

        return {
            "content": [{
                "type": "text",
                "text": summary
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error getting notes summary: {str(e)}"
            }]
        }


# Create MCP server with notes tools
jean_claude_notes_tools = create_sdk_mcp_server(
    name="jean-claude-notes",
    version="1.0.0",
    tools=[take_note, read_notes, search_notes, get_notes_summary]
)
