# ABOUTME: Main CLI entry point for Jean Claude
# ABOUTME: Defines the root 'jc' command group and registers subcommands

"""Main CLI entry point for Jean Claude."""

import click
from rich.console import Console

from jean_claude import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="jc")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Jean Claude CLI - AI-powered development workflows.

    Transform any project into an AI-driven development environment
    where agents can plan, implement, test, and deploy features.
    """
    ctx.ensure_object(dict)


@cli.command()
def version() -> None:
    """Display version information."""
    console.print(f"[bold blue]Jean Claude CLI[/bold blue] v{__version__}")
    console.print("[dim]AI-powered development workflows[/dim]")


# Import and register commands
from jean_claude.cli.commands import (
    dashboard,
    implement,
    init,
    initialize,
    logs,
    migrate,
    onboard,
    prime,
    prompt,
    run,
    status,
    workflow,
    work,
)

cli.add_command(dashboard.dashboard)
cli.add_command(implement.implement)
cli.add_command(init.init)
cli.add_command(initialize.initialize)
cli.add_command(logs.logs)
cli.add_command(migrate.migrate)
cli.add_command(onboard.onboard)
cli.add_command(prime.prime)
cli.add_command(prompt.prompt)
cli.add_command(run.run)
cli.add_command(status.status)
cli.add_command(workflow.workflow)
cli.add_command(work.work)

# Future commands (will be added as implemented):
# from jean_claude.cli.commands import watch
# cli.add_command(watch.watch)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
