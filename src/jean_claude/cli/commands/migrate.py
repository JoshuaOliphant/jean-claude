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
    install_skill,
    update_claude_md,
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
    - Installs jean-claude-cli skill (if missing)
    - Updates CLAUDE.md with Jean Claude section (if missing)
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
    would_install_skill = False
    would_update_claude_md = False

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

    # Check for jean-claude-cli skill
    skill_path = project_root / ".claude" / "skills" / "jean-claude-cli" / "SKILL.md"
    if not skill_path.exists():
        would_install_skill = True
        if not dry_run:
            install_skill(project_root)

    # Check for CLAUDE.md section
    claude_md_locations = [
        project_root / "CLAUDE.md",
        project_root / ".claude" / "CLAUDE.md",
    ]
    has_jc_section = False
    for location in claude_md_locations:
        if location.exists() and "## Jean Claude AI Workflows" in location.read_text():
            has_jc_section = True
            break

    if not has_jc_section:
        would_update_claude_md = True
        if not dry_run:
            update_claude_md(project_root)

    # Display results
    has_changes = (
        would_create_dirs
        or would_create_commands
        or would_install_skill
        or would_update_claude_md
    )

    if not has_changes:
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
    update_prefix = "Would update" if dry_run else "Updated"
    install_prefix = "Would install" if dry_run else "Installed"
    symbol = "○" if dry_run else "✓"

    for dir_name in would_create_dirs:
        results_table.add_row(symbol, f"{action_prefix} [cyan]{dir_name}/[/cyan]")

    for cmd_name in would_create_commands:
        results_table.add_row(
            symbol, f"{action_prefix} [cyan].claude/commands/{cmd_name}[/cyan]"
        )

    if would_install_skill:
        results_table.add_row(
            symbol, f"{install_prefix} [cyan].claude/skills/jean-claude-cli/[/cyan] skill"
        )

    if would_update_claude_md:
        results_table.add_row(
            symbol, f"{update_prefix} [cyan]CLAUDE.md[/cyan] with Jean Claude section"
        )

    console.print(results_table)
    console.print()

    if dry_run:
        total_changes = (
            len(would_create_dirs)
            + len(would_create_commands)
            + (1 if would_install_skill else 0)
            + (1 if would_update_claude_md else 0)
        )
        console.print(
            Panel(
                f"[yellow]{total_changes} "
                f"item(s) would be created/updated.[/yellow]\n\n"
                "Run [cyan]jc migrate[/cyan] without --dry-run to apply changes.",
                title="[yellow]Dry Run Complete[/yellow]",
                border_style="yellow",
            )
        )
    else:
        console.print(
            Panel(
                "[bold green]Migration complete![/bold green]\n\n"
                "Latest features:\n"
                "  • [cyan]jean-claude-cli skill[/cyan] - Comprehensive CLI documentation\n"
                "  • [cyan]CLAUDE.md integration[/cyan] - Project-specific guidance\n"
                "  • [cyan]Coordinator pattern[/cyan] - Mobile ntfy.sh notifications\n"
                "  • [cyan]Two-agent workflows[/cyan] - Opus plans, Sonnet implements\n"
                "  • [cyan]Beads integration[/cyan] - Seamless issue tracking",
                title="[bold green]Success[/bold green]",
                border_style="green",
            )
        )
