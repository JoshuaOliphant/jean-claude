# ABOUTME: Implementation of the 'jc onboard' command
# ABOUTME: Provides onboarding content for CLAUDE.md integration

"""Onboarding command for Jean Claude CLI."""

import click
from rich.console import Console
from rich.panel import Panel

console = Console()

CLAUDE_MD_CONTENT = """\
## AI Developer Workflows

This project uses **Jean Claude CLI (jc)** for AI-powered development workflows.

### Quick Reference

| Task | Command |
|------|---------|
| Run tests | `uv run pytest tests/` |
| Execute prompt | `jc prompt "your prompt"` |
| Two-agent workflow | `jc workflow "complex task"` |
| Work from Beads | `jc work <beads-id>` |
| Run chore | `jc run chore "task"` |

### Two-Agent Workflow

- `jc workflow "description"` - Full workflow (Opus plans, Sonnet codes)
- `jc initialize "description"` - Plan only (creates spec)
- `jc implement <workflow-id>` - Resume implementation

### Beads Integration

- `jc work task-123` - Execute from Beads task
- `jc work task-123 --dry-run` - Plan only
- `jc work task-123 --show-plan` - Pause for approval

For more: `jc --help`
"""

MINIMAL_CONTENT = """\
## Jean Claude CLI

`jc workflow "task"` - AI-powered development workflows

For more: `jc --help`
"""


@click.command()
@click.option(
    "--minimal",
    is_flag=True,
    help="Show minimal snippet (2 lines)",
)
def onboard(minimal: bool) -> None:
    """Display onboarding content for CLAUDE.md.

    Shows a snippet to add to your project's CLAUDE.md that documents
    Jean Claude CLI usage for AI assistants.

    \\b
    Examples:
      jc onboard           # Show full CLAUDE.md content
      jc onboard --minimal # Show minimal snippet
    """
    console.print()
    console.print("[bold blue]jc Onboarding[/bold blue]")
    console.print()

    content = MINIMAL_CONTENT if minimal else CLAUDE_MD_CONTENT
    title = "Minimal CLAUDE.md" if minimal else "CLAUDE.md Content"

    console.print(f"Add this snippet to your project's [cyan]CLAUDE.md[/cyan]:")
    console.print()

    console.print(
        Panel(
            content,
            title=f"[green]{title}[/green]",
            border_style="green",
        )
    )

    console.print()
    console.print("[dim]How it works:[/dim]")
    console.print("   [dim]- CLAUDE.md provides context for Claude Code sessions[/dim]")
    console.print("   [dim]- Content is injected at the start of each conversation[/dim]")
    console.print("   [dim]- Run `jc init` to set up full project infrastructure[/dim]")
    console.print()
