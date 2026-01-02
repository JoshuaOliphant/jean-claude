# ABOUTME: Implementation of the 'jc note' command for agent note-taking
# ABOUTME: Allows agents to add, list, and search shared notes

"""Agent note-taking command for shared knowledge."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from jean_claude.core.notes import NoteCategory
from jean_claude.core.notes_api import Notes
from jean_claude.core.workflow_utils import find_most_recent_workflow

console = Console()


def get_category_style(category: NoteCategory) -> str:
    """Get Rich style for a note category.

    Args:
        category: The note category

    Returns:
        Rich style string
    """
    styles = {
        NoteCategory.OBSERVATION: "cyan",
        NoteCategory.DECISION: "yellow",
        NoteCategory.LEARNING: "green",
        NoteCategory.WARNING: "red",
        NoteCategory.ACCOMPLISHMENT: "magenta",
        NoteCategory.CONTEXT: "blue",
        NoteCategory.TODO: "white",
    }
    return styles.get(category, "white")


@click.group()
def note() -> None:
    """Agent note-taking system for shared knowledge.

    Notes allow agents to record observations, decisions, learnings,
    and other information that should be shared across agents working
    on the same workflow.

    \b
    Examples:
      jc note add "Found bug in auth"   # Add a note
      jc note list                      # List all notes
      jc note list --category learning  # Filter by category
      jc note search "authentication"   # Search notes
      jc note summary                   # Get summary
    """
    pass


@note.command("add")
@click.argument("title")
@click.option(
    "--content", "-c",
    default="",
    help="Full content of the note (prompted if not provided)"
)
@click.option(
    "--category", "-t",
    type=click.Choice([c.value for c in NoteCategory], case_sensitive=False),
    default="observation",
    help="Category of the note"
)
@click.option(
    "--agent", "-a",
    default="cli-user",
    help="Agent ID (default: cli-user)"
)
@click.option(
    "--tags",
    help="Comma-separated tags"
)
@click.option(
    "--file", "-f",
    "related_file",
    help="Related file path"
)
@click.option(
    "--feature",
    "related_feature",
    help="Related feature name"
)
@click.option(
    "--workflow", "-w",
    "workflow_id",
    help="Workflow ID (default: most recent)"
)
def add_note(
    title: str,
    content: str,
    category: str,
    agent: str,
    tags: str | None,
    related_file: str | None,
    related_feature: str | None,
    workflow_id: str | None,
) -> None:
    """Add a note to the shared notes.

    \b
    Examples:
      jc note add "Found memory leak in cache module"
      jc note add "Use repository pattern" --category decision
      jc note add "Auth flow explained" -c "The auth flow works by..." --category learning
      jc note add "TODO: Fix race condition" --category todo --tags "bug,urgent"
    """
    project_root = Path.cwd()

    # Resolve workflow ID
    if workflow_id is None:
        workflow_id = find_most_recent_workflow(project_root)
        if workflow_id is None:
            console.print("[red]Error:[/red] No workflows found")
            console.print("[dim]Run 'jc work <task-id>' to start a workflow first[/dim]")
            raise click.Abort()

    # If content not provided, prompt for it
    if not content:
        content = click.prompt("Note content", default=title)

    # Parse tags
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Create notes API and add note
    notes = Notes(workflow_id=workflow_id, base_dir=project_root / "agents")

    try:
        created_note = notes.add(
            agent_id=agent,
            title=title,
            content=content,
            category=NoteCategory(category),
            tags=tag_list,
            related_file=related_file,
            related_feature=related_feature,
        )
        console.print(f"[green]Note added:[/green] {created_note.id[:8]}")
        console.print(f"[dim]Category: {created_note.category.value} | Agent: {created_note.agent_id}[/dim]")
    except Exception as e:
        console.print(f"[red]Error adding note:[/red] {e}")
        raise click.Abort() from None


@note.command("list")
@click.option(
    "--workflow", "-w",
    "workflow_id",
    help="Workflow ID (default: most recent)"
)
@click.option(
    "--category", "-t",
    type=click.Choice([c.value for c in NoteCategory], case_sensitive=False),
    help="Filter by category"
)
@click.option(
    "--agent", "-a",
    help="Filter by agent ID"
)
@click.option(
    "--tag",
    help="Filter by tag"
)
@click.option(
    "--limit", "-n",
    type=int,
    help="Limit number of notes shown"
)
@click.option(
    "--full", "-f",
    is_flag=True,
    help="Show full note content"
)
def list_notes(
    workflow_id: str | None,
    category: str | None,
    agent: str | None,
    tag: str | None,
    limit: int | None,
    full: bool,
) -> None:
    """List notes from the shared notes.

    \b
    Examples:
      jc note list                      # List all notes
      jc note list --category learning  # Filter by category
      jc note list --agent coder-agent  # Filter by agent
      jc note list --limit 10           # Show last 10 notes
      jc note list --full               # Show full content
    """
    project_root = Path.cwd()

    # Resolve workflow ID
    if workflow_id is None:
        workflow_id = find_most_recent_workflow(project_root)
        if workflow_id is None:
            console.print("[yellow]No workflows found[/yellow]")
            return

    # Create notes API
    notes_api = Notes(workflow_id=workflow_id, base_dir=project_root / "agents")

    # Parse category if provided
    category_filter = NoteCategory(category) if category else None

    # Get notes
    notes_list = notes_api.list(
        agent_id=agent,
        category=category_filter,
        tag=tag,
        limit=limit,
    )

    if not notes_list:
        console.print("[yellow]No notes found[/yellow]")
        return

    console.print(f"\n[bold]Notes for workflow {workflow_id}[/bold] ({len(notes_list)} total)\n")

    if full:
        # Show full notes
        for note in notes_list:
            style = get_category_style(note.category)
            console.print(f"[{style}][{note.category.value.upper()}][/{style}] {note.title}")
            console.print(f"[dim]Agent: {note.agent_id} | {note.created_at.strftime('%Y-%m-%d %H:%M')}[/dim]")
            if note.tags:
                console.print(f"[dim]Tags: {', '.join(note.tags)}[/dim]")
            console.print()
            console.print(note.content)
            console.print("\n" + "-" * 40 + "\n")
    else:
        # Show table
        table = Table()
        table.add_column("Category", style="cyan", width=12)
        table.add_column("Title", style="white")
        table.add_column("Agent", style="dim")
        table.add_column("Time", style="dim")

        for note in notes_list:
            style = get_category_style(note.category)
            table.add_row(
                f"[{style}]{note.category.value}[/{style}]",
                note.title[:50] + ("..." if len(note.title) > 50 else ""),
                note.agent_id,
                note.created_at.strftime("%m-%d %H:%M"),
            )

        console.print(table)


@note.command("search")
@click.argument("query")
@click.option(
    "--workflow", "-w",
    "workflow_id",
    help="Workflow ID (default: most recent)"
)
@click.option(
    "--full", "-f",
    is_flag=True,
    help="Show full note content"
)
def search_notes(
    query: str,
    workflow_id: str | None,
    full: bool,
) -> None:
    """Search notes by text query.

    \b
    Examples:
      jc note search "authentication"
      jc note search "bug" --full
    """
    project_root = Path.cwd()

    # Resolve workflow ID
    if workflow_id is None:
        workflow_id = find_most_recent_workflow(project_root)
        if workflow_id is None:
            console.print("[yellow]No workflows found[/yellow]")
            return

    # Create notes API and search
    notes_api = Notes(workflow_id=workflow_id, base_dir=project_root / "agents")
    results = notes_api.search(query)

    if not results:
        console.print(f"[yellow]No notes found matching '{query}'[/yellow]")
        return

    console.print(f"\n[bold]Search results for '{query}'[/bold] ({len(results)} found)\n")

    if full:
        for note in results:
            style = get_category_style(note.category)
            console.print(f"[{style}][{note.category.value.upper()}][/{style}] {note.title}")
            console.print(f"[dim]Agent: {note.agent_id} | {note.created_at.strftime('%Y-%m-%d %H:%M')}[/dim]")
            console.print()
            console.print(note.content)
            console.print("\n" + "-" * 40 + "\n")
    else:
        table = Table()
        table.add_column("Category", style="cyan", width=12)
        table.add_column("Title", style="white")
        table.add_column("Agent", style="dim")

        for note in results:
            style = get_category_style(note.category)
            table.add_row(
                f"[{style}]{note.category.value}[/{style}]",
                note.title[:50] + ("..." if len(note.title) > 50 else ""),
                note.agent_id,
            )

        console.print(table)


@note.command("summary")
@click.option(
    "--workflow", "-w",
    "workflow_id",
    help="Workflow ID (default: most recent)"
)
def summary(workflow_id: str | None) -> None:
    """Get a summary of all notes.

    \b
    Example:
      jc note summary
    """
    project_root = Path.cwd()

    # Resolve workflow ID
    if workflow_id is None:
        workflow_id = find_most_recent_workflow(project_root)
        if workflow_id is None:
            console.print("[yellow]No workflows found[/yellow]")
            return

    # Create notes API and get summary
    notes_api = Notes(workflow_id=workflow_id, base_dir=project_root / "agents")
    summary_text = notes_api.get_summary()

    console.print(f"\n[bold]Workflow: {workflow_id}[/bold]\n")
    console.print(summary_text)


@note.command("context")
@click.option(
    "--workflow", "-w",
    "workflow_id",
    help="Workflow ID (default: most recent)"
)
@click.option(
    "--limit", "-n",
    type=int,
    default=10,
    help="Maximum notes to include (default: 10)"
)
def context(workflow_id: str | None, limit: int) -> None:
    """Output notes formatted for agent context.

    This command outputs notes in a format suitable for including
    in an agent's context or prompt.

    \b
    Example:
      jc note context > context.md
      jc note context --limit 20
    """
    project_root = Path.cwd()

    # Resolve workflow ID
    if workflow_id is None:
        workflow_id = find_most_recent_workflow(project_root)
        if workflow_id is None:
            console.print("[yellow]No workflows found[/yellow]")
            return

    # Create notes API and format for context
    notes_api = Notes(workflow_id=workflow_id, base_dir=project_root / "agents")
    context_text = notes_api.format_for_context(limit=limit)

    # Output raw text (for piping)
    print(context_text)
