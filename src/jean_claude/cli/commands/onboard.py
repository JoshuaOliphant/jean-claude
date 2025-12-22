# ABOUTME: Implementation of the 'jc onboard' command
# ABOUTME: Provides onboarding content for AGENTS.md and CLAUDE.md integration

"""Onboarding command for Jean Claude CLI."""

import click
from rich.console import Console
from rich.panel import Panel

console = Console()

AGENTS_MD_CONTENT = """\
## AI Developer Workflows

This project uses **Jean Claude CLI (jc)** for AI-powered development workflows.

**Quick reference:**
- `jc init` - Initialize Jean Claude in a project
- `jc prompt "your prompt"` - Execute adhoc prompts
- `jc run chore "task"` - Run a chore workflow
- `jc run feature "description"` - Run a feature workflow
- `jc workflow "complex task"` - Two-agent pattern (Opus plans, Sonnet codes)

**Workflow types:**
- `chore` - Small tasks, refactoring, documentation
- `feature` - New functionality or enhancements
- `bug` - Bug fixes and issue resolution

For more: `jc --help`
"""

CLAUDE_MD_LINK = """\
# Agents

@AGENTS.md
"""


@click.command()
@click.option(
    "--claude-md",
    is_flag=True,
    help="Also show CLAUDE.md link snippet",
)
def onboard(claude_md: bool) -> None:
    """Display onboarding content for AGENTS.md.

    Shows a minimal snippet to add to AGENTS.md (or create it) that
    documents Jean Claude CLI usage for AI assistants.

    \\b
    Examples:
      jc onboard              # Show AGENTS.md content
      jc onboard --claude-md  # Also show CLAUDE.md link
    """
    console.print()
    console.print("[bold blue]jc Onboarding[/bold blue]")
    console.print()
    console.print("Add this snippet to [cyan]AGENTS.md[/cyan] (or create it):")
    console.print()

    console.print(
        Panel(
            AGENTS_MD_CONTENT,
            title="[green]AGENTS.md Content[/green]",
            border_style="green",
        )
    )

    if claude_md:
        console.print()
        console.print("For [cyan]Claude Code[/cyan] users, add this to your [cyan]CLAUDE.md[/cyan]:")
        console.print()
        console.print(
            Panel(
                CLAUDE_MD_LINK,
                title="[blue]CLAUDE.md Link[/blue]",
                border_style="blue",
            )
        )

    console.print()
    console.print("[dim]How it works:[/dim]")
    console.print("   [dim]- AGENTS.md provides context for AI assistants[/dim]")
    console.print("   [dim]- @AGENTS.md in CLAUDE.md imports it for Claude Code[/dim]")
    console.print("   [dim]- Run `jc init` to set up project infrastructure[/dim]")
    console.print()
