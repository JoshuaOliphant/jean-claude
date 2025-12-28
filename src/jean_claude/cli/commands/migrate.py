# ABOUTME: Implementation of the 'jc migrate' command
# ABOUTME: Updates existing projects with new Jean Claude features

"""Migrate existing Jean Claude projects to latest version."""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from jean_claude.cli.commands.init import (
    INIT_DIRECTORIES,
    SLASH_COMMANDS,
    create_slash_commands,
)

console = Console()


@click.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without making changes",
)
def migrate(dry_run: bool) -> None:
    """Migrate existing project to latest Jean Claude version.

    Updates an already-initialized project with new features:
    - Creates any missing directories
    - Adds new slash command templates
    - Does NOT overwrite existing files

    \b
    Examples:
      jc migrate            # Apply updates
      jc migrate --dry-run  # Preview changes without applying
    """
    project_root = Path.cwd()
    config_path = project_root / ".jc-project.yaml"

    # Check if project is initialized
    if not config_path.exists():
        console.print(
            Panel(
                "[yellow]Project not initialized.[/yellow]\n\n"
                "Run [cyan]jc init[/cyan] first to initialize the project.",
                title="[yellow]Not Initialized[/yellow]",
                border_style="yellow",
            )
        )
        raise SystemExit(1)

    console.print()
    if dry_run:
        console.print("[bold blue]Migration preview (dry run)...[/bold blue]")
    else:
        console.print("[bold blue]Migrating Jean Claude project...[/bold blue]")
    console.print()

    # Track what would be / was created
    would_create_dirs: list[str] = []
    would_create_commands: list[str] = []

    # Check for missing directories
    for dir_name in INIT_DIRECTORIES:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            would_create_dirs.append(dir_name)
            if not dry_run:
                dir_path.mkdir(parents=True)

    # Check for missing slash commands
    commands_dir = project_root / ".claude" / "commands"
    for filename in SLASH_COMMANDS:
        command_path = commands_dir / filename
        if not command_path.exists():
            would_create_commands.append(filename)

    # Create slash commands if not dry run
    if not dry_run and would_create_commands:
        create_slash_commands(project_root)

    # Display results
    if not would_create_dirs and not would_create_commands:
        console.print(
            Panel(
                "[green]Project is up to date![/green]\n\n"
                "No migration needed.",
                title="[green]Already Current[/green]",
                border_style="green",
            )
        )
        return

    results_table = Table(show_header=False, box=None, padding=(0, 2))
    results_table.add_column(style="green" if not dry_run else "yellow")
    results_table.add_column()

    action_prefix = "Would create" if dry_run else "Created"
    symbol = "○" if dry_run else "✓"

    for dir_name in would_create_dirs:
        results_table.add_row(symbol, f"{action_prefix} [cyan]{dir_name}/[/cyan]")

    for cmd_name in would_create_commands:
        results_table.add_row(
            symbol, f"{action_prefix} [cyan].claude/commands/{cmd_name}[/cyan]"
        )

    console.print(results_table)
    console.print()

    if dry_run:
        console.print(
            Panel(
                f"[yellow]{len(would_create_dirs) + len(would_create_commands)} "
                f"item(s) would be created.[/yellow]\n\n"
                "Run [cyan]jc migrate[/cyan] without --dry-run to apply changes.",
                title="[yellow]Dry Run Complete[/yellow]",
                border_style="yellow",
            )
        )
    else:
        console.print(
            Panel(
                "[bold green]Migration complete![/bold green]\n\n"
                "New features:\n"
                "  • [cyan]jc work <beads-id>[/cyan] - Execute workflow from Beads task\n"
                "  • [cyan]jc workflow[/cyan] - Two-agent pattern (Opus plans, Sonnet implements)\n"
                "  • [cyan]jc initialize / jc implement[/cyan] - Modular workflow execution\n"
                "  • [cyan]jc prime[/cyan] - Context-efficient project exploration",
                title="[bold green]Success[/bold green]",
                border_style="green",
            )
        )
